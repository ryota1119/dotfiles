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
  version: 0.1.0
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
