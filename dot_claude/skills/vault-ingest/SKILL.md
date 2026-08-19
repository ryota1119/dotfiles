---
name: vault-ingest
description: >
  Exocortex（~/Workspace/exocortex）の `inbox/` に溜まったソースを取り込むstaff。
  inboxを走査して未処理・処理済み・不整合に分類し、原本を`.raw/`へ退避し、
  source pageの草案とsource-ledgerのエントリを作り、vaultctlのplan→承認→applyで
  同一トランザクションとして適用し、処理済みの原本を`inbox/`から削除する。
  「inboxを取り込んで」「vaultのinboxを処理して」「溜まったクリップを整理して」
  「週次の取り込みを回して」等、inboxに実ファイルとして存在するソースの
  取り込み依頼で使う。会話中の内容を1ページとして保存する依頼はvault-saveが担当する。
  applyと削除は必ず事前承認を得てから実行する。
  Also triggers on: "inboxを処理", "取り込んで", "vault-ingest", "クリップを取り込む",
  "週次の取り込み", "inboxを空にして", ".rawへ退避", "source-ledgerに登録".
metadata:
  version: 0.4.0
---

# vault-ingest — inbox のソースを取り込む

`inbox/` に実ファイルとして置かれたソースを、出所を辿れる形で vault に取り込む。

**判定は CLI、整理は skill、決定は人間。** 分類は機械的に行うが、**どのモードで進めるかは
必ずボスが決める**。走査結果から skill が勝手にモードを選んで適用まで走らない。

やり取りはすべて日本語で行う。

## 担当範囲

1. `inbox/` の走査・分類・キュー化
2. 原本の `.raw/` への退避
3. source ページの草案作成と `wiki/index.md` への掲載・被リンク
4. `source-ledger.json` への登録
5. 処理済み原本の `inbox/` からの削除
6. 上記を `vaultctl` の plan → 承認 → apply へ載せる

### vault-save との境界

**`inbox/` に実ファイルがあるかどうかで切る。** これが唯一の判定基準。

| 入力 | 経路 |
| --- | --- |
| `inbox/` にファイルがある（Web Clipper で落とした記事、PDF、他人の投稿） | **`vault-ingest`**（この skill） |
| 会話の中でボスと確定した考え・判断・設計方針・一次体験 | `vault-save` |

外部原本があるものは `source-ledger` に登録できるので、こちらが扱う。会話由来のものは
`origin.locator` / `retrieved_at` / `content_sha256` / `refresh_due` のどれも埋められないため、
`vault-save` が扱い ledger には載せない。

**URL を直接渡された場合、この skill は自分で fetch しない。** vault への書き込みは
`vaultctl apply` 経由だけと決まっており（規約6.1の1）、fetch して `inbox/` へ置くのは
その経路の外になる。Obsidian Web Clipper で `inbox/` に落としてから呼び出す。
なお `mckinsey.com` / `pwc.com` のように WebFetch を構造的に拒否するサイトがあり、
fetch させる方式はそもそも成立しない場合がある（2026-08-18 実測）。

### 扱わないこと

- `claim-ledger` への追記（claim の選定は人間の判断が濃く、skill が単独で決められない）
- 会話由来の内容の保存（`vault-save`）
- lint finding の解消（`vault-review` と Phase 3）

## 前提と禁止事項

禁止事項は**共通規約6.1 を正とする**。ここでは再記述せず、この skill 固有の3点だけ書く。

1. **不整合を自動で吸収しない。** hash 不一致・ページ欠落・ledger 未参照は、いずれも
   「たぶんこうだろう」で埋めずに**停止してボスへ報告する**。ledger を勝手に書いたり
   原本を消したりする経路を作らない。
2. **`.raw/` へ退避するときファイル名をリネームしない。** ファイル名の先頭に ISO8601 の
   タイムスタンプが入っており既に一意かつ時系列順で、リネームすると ledger の
   `origin.locator` との対応が読めなくなる。同名衝突は `mode=create` が `plan` の時点で
   失敗する。**これは「同じ原本を二度退避しようとしている」という事実**なので、
   連番を勝手に付けず停止して報告する。
3. **`inbox/` からの削除は、退避が完了して検証が通ったあとにしか行わない。** delete は
   取り返しがつかない。exocortex は git 管理下になく、`mode=create` にはバックアップが無い
   （＝退避先の `.raw/` を巻き戻すと消える）。

vault のパスは常に明示する。`--vault` は**サブコマンドより前**に置く（規約3.1）。

## 実行の流れ

1. **走査と分類**（下記）。`scripts/scan_inbox.py` を実行して `queue.json` を作る
2. **分類結果をボスへ提示し、どのモードで進めるかの承認を得る**
3. モードごとの手順へ進む（reconcile / ingest）

| モード | 対象 | 概要 |
| --- | --- | --- |
| **reconcile** | 既にページ化・ledger 登録済みで、原本だけが `inbox/` に残っているもの | `.raw/` への退避 ＋ ledger の `locator` 書き換え ＋ `inbox/` からの削除 |
| **ingest** | 未処理のもの | 上記に加えてページ草案・`index.md` 掲載・被リンク・ledger 登録 |

**不整合が1件でもあれば、そのファイルはどちらのモードにも入れない。** 分類結果に不整合が
あることを報告し、対処をボスに決めてもらう。他のファイルの処理は続けてよい。

トランザクションは3本に分ける。**まとめない。**

| Tx | 内容 | mode |
| --- | --- | --- |
| Tx-A | `.raw/` への原本退避 | `create` |
| Tx-B | ledger の `origin.locator` を `inbox/` から `.raw/` へ書き換え | `replace` |
| Tx-C | `inbox/` からの削除 | **`delete`** |

**承認は3回とる。** delete を他と束ねない。退避が完全に信用できる状態を作ってから削除する。

## inbox の走査と分類

```bash
scripts/scan_inbox.py --vault ~/Workspace/exocortex --out <絶対パス>/queue.json
```

読み取り専用で、vault へ1バイトも書かない。不整合が1件でもあれば **exit 1** で終わる。

### 分類規則

| 判定 | 分類 |
| --- | --- |
| manifest の `sources` に無い | **ingest**（未処理） |
| manifest にあり、hash が一致し、`pages_created` が全て実在し、その全てが source-ledger から参照されている | **reconcile**（処理済み・原本のみ残存） |
| manifest にあるが hash が不一致 | **不整合A**（取り込み後に原本が書き換わった）→ 停止して報告 |
| manifest にあるが `pages_created` のページが実在しない | **不整合B**（ページが削除された）→ 停止して報告 |
| ページは実在するが source-ledger から参照されていない | **不整合C**（規則10-a 相当）→ 停止して報告。**ledger 登録は Phase 3 の担当であり、ここで埋めない** |

### Unicode 正規化の罠

**`.raw/.manifest.json` のキーは NFC、`os.listdir` が返す名前は NFD になりうる。**
素朴に集合比較すると**処理済みを未処理と誤判定し、同じソースから二重にページを作る。**

- **突合（manifest / ledger との照合）は NFC 正規化してから行う**
- **bundle の `path` にはファイルシステムから読んだ生の名前を使う**

`queue.json` は `inbox_path`（生）と `inbox_path_nfc`（正規化後）の両方を持つ。この区別を
実装時に忘れないためなので、**片方だけ使い回さない。**

### `.raw/` の命名

```
.raw/<inbox のファイル名をそのまま>
```

リネームしない。サブディレクトリを掘らない。件数が3桁になったら見直す。

## 原本の `.raw/` への退避（Tx-A）

```bash
scripts/build_archive_bundle.py --queue <queue.json> --out <bundle.json> \
    --operation-id ingest-<YYYYMMDDTHHMMSS>-<slug> --snapshot <snapshot.json>
```

- **create しか出さない。** delete を混ぜない
- `content_file` は inbox の実ファイルそのものの絶対パス。**コピーを作らない**
- 不整合が1件でもあれば bundle を作らずに止まる
- 退避先が既にあれば止まる。連番を付けない

`--snapshot` は退避元の実測ハッシュを残す。**`plan` と `apply` の間に Google Drive の同期が
走ると `original_sha256` 不一致で失敗しうる**ので、apply の直前に取り直して照合する。

`.raw/` への create は **lint の件数を動かさない。** ページ解析（規則1〜7・11）は `wiki/` しか
走査せず、`.raw/` を見るのは規則8（同期競合コピー）だけだから。ただし
` (数字).md` / `のコピー` / `conflicted copy` / `- コピー` を名前に含むファイルを置くと
規則8 が発火する。**予測は「増減なし」だが、ファイル名を確認してから書く。**

## `inbox/` からの削除（Tx-C）

**この skill で最も危険な処理。** 退避が完全に信用できる状態を作ってからでないと実行しない。

```bash
scripts/verify_archived.py --queue <queue.json> --out <delete-bundle.json> \
    --operation-id ingest-<YYYYMMDDTHHMMSS>-<slug> --presentation <pres.md>
```

このスクリプトが次のゲートをすべて通したときだけ delete bundle を書く。**1つでも
通らなければ何も書かず exit 1 で終わる。**

| ゲート | 内容 |
| --- | --- |
| G3 | `queue.json` の不整合が0件 |
| — | `.raw/` に Google Drive の競合コピーが無い |
| G2 | **`.raw/` と `inbox/` の両方をその場で全読みして SHA256 を再計算し、全件一致する** |
| G5 | 検証を通った件数が対象件数と完全一致する |

**`queue.json` に記録したハッシュを信じない。** 記録から時間が経っており、その間に Drive の
同期や Obsidian の保存が走りうる。同一ハッシュでサイズ違いは起こり得ないが、読み取りバグを
検出する冗長チェックとしてサイズも比較する。

**1件でも不一致があれば全件中止する。** 「一致した分だけ消す」をしない。部分的に消すと
どこまで消えたかを後から追えなくなる。

### 退避と削除を別トランザクションにする理由

設計書7節は「ページ作成と ledger 追記を同一トランザクションに」と言っているが、
**「原本退避と inbox 削除を同一トランザクションに」とは言っていない。** 分ける理由は3つ。

1. G2 の保証は `.raw/` に実ファイルが存在してからでないと取れない。同一トランザクションだと
   `plan` 時点では staging しか無く、**apply 直前の検証ができない**
2. 同一トランザクションで失敗すると自動ロールバックで `.raw/` の create も巻き戻る。
   **退避のやり直しになる。** 分けておけば退避は残る
3. delete だけの bundle なら「delete 以外が**0件か**」を検査できる。混入の検出が単純になる

### 承認の提示

`--presentation` が規約3.2の2 に従うブロックを書く。**削除対象を1件ずつ全件列挙**し、
delete 行を太字にし、各行に退避先と SHA256 一致確認を併記し、journal backup のパスを
明記する。**「15件」と件数だけ書いて承認を求めない。**

## ledger の locator 書き換え（Tx-B）

`inbox/` から消したファイルを指す `origin.locator` は死ぬ。ledger の存在意義は出所が
追えることなので、**実在しないパスを残さない。**

```bash
scripts/build_ledger_relocate.py --queue <queue.json> --out <bundle.json> \
    --staging <staging ディレクトリ> --operation-id ingest-<...>-<slug> \
    [--generated-at YYYY-MM-DD]
```

| `origin.kind` | 扱い |
| --- | --- |
| `file` で `locator` が `inbox/` 始まり | **`.raw/<name>` へ書き換える** |
| `url` | **触らない**（inbox に依存していない） |

**`locator` 以外のキーを1つも変えない。** `content_sha256` / `retrieved_at` /
`refresh_due` / `pages` / `title` / `authority` / `content_kind` / `review_status` は
既存値をそのまま維持する。スクリプトが差分キー集合を計算し、
`sources.<id>.origin.locator`（と `generated_at`）以外が動いていたら**止まる**。

**Tx-B は Tx-C より前に置く。** Tx-B が失敗しても inbox に原本が残っていれば元に戻せる。
逆順だと「原本を消したが locator が古いまま」という中途半端な状態が残る。

**Tx-B を Tx-A に混ぜない。** Tx-A は `.raw/` の create だけで完結させ、「退避が成功した」
という事実を単独で確定させる。

## reconcile モードの通し手順

```
1. scan_inbox.py                → queue.json、分類をボスへ提示して承認
2. build_archive_bundle.py      → Tx-A: plan → 提示 → 承認 → apply
3. verify_archived.py（検証のみ）→ G2 で .raw/ と inbox/ の SHA256 一致を確認
4. build_ledger_relocate.py     → Tx-B: plan → 提示 → 承認 → apply
5. verify_archived.py（bundle 生成）→ Tx-C: plan → 提示 → 承認 → apply
6. lint --json を再実行して予測と照合
```

**lint の予測は「violation・review とも増減なし」。** reconcile はページを1枚も作らず、
`.raw/` と `inbox/` はページ解析の対象外だから。ずれたら次の write を発行せず止まる。

## 承認ルール

規約8節の `vault-ingest` 列を継承し、狭める方向にのみ上書きする。

**自律実行してよいこと**

- vault の読み取り・検索、`scan_inbox.py` の実行
- `lint` / `ledger verify` / `graph` / `recover --dry-run` の実行
- `~/Workspace/tmp/` への中間ファイル・bundle の作成
- `vaultctl plan` の実行

**事前承認が必要なこと**

- `vaultctl apply`（Tx-A / Tx-B / Tx-C を**個別に**）
- **`mode=delete` を含む bundle の apply — 削除対象を1件ずつ全件列挙して提示する。
  件数だけの要約で承認を求めない**
- `vaultctl recover` の実行
- ディレクトリ構成・frontmatter schema・lint 規則の変更
- 会社情報を実名・実値のまま保存する判断
- Backlog / Notion など vault 外への転記

## 失敗時の対応

事象別の対処は**規約7節を正とする**。この skill 固有の停止事由だけ挙げる。

| 事象 | 対応 |
| --- | --- |
| 分類で不整合が出た | そのファイルを処理対象から外し、原因（A / B / C）を明示して報告する |
| `.raw/` に同名ファイルが既にある | 連番を付けずに停止。「同じ原本を二度退避しようとしている」という事実として報告する |
| 退避後の検証で hash が一致しない | **`inbox/` からの削除を実行しない。** 退避をやり直す |
| slug が既存ページと衝突 | ページを作らずに停止して報告する |

**想定と実測がずれたら、次の write を発行せず、状態を報告して止まる。**
「もう一度やれば通るだろう」で再実行しない。

## 同梱物

| ファイル | 用途 |
| --- | --- |
| `scripts/scan_inbox.py` | `inbox/` の走査・分類・`queue.json` の生成。読み取り専用 |
| `scripts/build_archive_bundle.py` | `.raw/` への退避 bundle の組み立て（create のみ） |
| `scripts/build_ledger_relocate.py` | `origin.locator` の `inbox/` → `.raw/` 書き換え bundle |
| `scripts/verify_archived.py` | 削除前のゲート検証と delete bundle・承認提示ブロックの生成 |
