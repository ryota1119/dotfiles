---
name: vault-save
description: >
  会話の中で確定した知識・判断・気づきを、exocortex（第二の脳）へ1ページとして
  保存するskill。vaultctlのplan→承認→applyの経路だけを使い、新規ページ、
  wiki/index.mdへの掲載、既存ページからの被リンク、wiki/log.mdとwiki/hot.mdへの
  記録を同一トランザクションで書く。既存ページへの追記・書き換えも扱う。
  外部ソース（URL・記事・PDF等）が原本として存在する取り込みは扱わず、
  inbox/経由でvault-ingestへ回す。
  「これ保存して」「Wikiに残して」「今の話をページにして」等で使う。
  applyは必ず事前に内容を提示して承認を得る。
  Also triggers on: "保存して", "Wikiに残して", "第二の脳に保存",
  "知見として記録", "ページにして", "exocortexに保存", "vault-save".
metadata:
  version: 1.0.0
---

# vault-save — 会話の知識を vault へ保存する

会話の中でボスと確定した知識・判断・気づきを、exocortex に知識ページとして保存する。

**判定は CLI、整理は skill、決定は人間。** ページが規約に適合しているかは `vaultctl` が
決める。この skill は `vaultctl` の判定を自分で代替しない（規約2.1）。何を保存するか、
保存してよいかを決めるのはボスであって、skill ではない。

やり取りはすべて日本語で行う。

## 担当範囲と境界

| skill | 責務 |
| --- | --- |
| **`vault-save`** | **会話由来の内容を1ページとして保存する。既存ページへの追記・書き換えも担う** |
| `vault-ingest` | 外部ソースを取り込み、原本を `.raw/` へ退避して ledger に登録する |
| `vault-review` | 既存の vault を検査し、finding を整理して提示する |

### `vault-ingest` との境界

境界は **「Vault の外に、後から出典確認できる原本が存在するか」** の一点で切る。

| 入力の性質 | 経路 |
| --- | --- |
| ボス自身の考え・判断・設計方針・実装で得た一次体験・会話で合意した結論 | **`vault-save`**（この skill） |
| URL・記事・論文・PDF・他人の投稿・公式ドキュメントなど、原本を `.raw/` に退避して `content_sha256` を取るべきもの | `inbox/` へ置いて **`vault-ingest`** |
| 両方が混在（ボスの気づき ＋ 外部記事の引用） | **分割する。** ボスの気づき部分だけをこの skill で保存し、外部ソースは `inbox/` へ回す。分割できなければ保存せずボスへ確認する |

`vault-save` が扱う内容は原本が無いため `source-ledger` に登録できない。したがって
**`wiki/sources/` にページを作らない。** 作れる `type` は `concept` と `entity` の2種だけ。

### この skill が扱わないこと

- `type: source` / `meta` / `overview` のページ作成
- `source-ledger.json` / `claim-ledger.json` への追記（`vault-ingest` の責務）
- `.raw/` への原本退避、`inbox/` からの削除
- lint finding に基づく既存ページの修正提案（`vault-review` の責務）
- 実 vault に現存する finding の解消（Phase 3 の別タスク）

### secretary からの回付

secretary の「メモして」は、ソースの有無で保存経路を分岐する運用になっている。ソースが
無い側（ボス自身の考え・判断）がこの skill に回ってくる。**`メモして` はこの skill の
トリガーに含めない**（secretary と重複させない）。

## 前提の確認

作業前に次を読む。競合したら**より厳しい承認境界を採る**。

- `~/Workspace/CLAUDE.md`（共通ルール）
- `~/Workspace/exocortex/CLAUDE.md`（匿名化ルールを含む）
- 規約 `~/Workspace/docs/superpowers/plans/2026-08-18-vault-skills-conventions.md`

vault のパスは常に明示する。`--vault` は**サブコマンドより前**に置く（規約3.1）。

```bash
vaultctl --vault ~/Workspace/exocortex lint --json --today 2026-08-18
```

**`~/Workspace/exocortex` は Google Drive 上のディレクトリへの symlink であり、git 管理下に
ない。** 書き込みは `vaultctl apply` 経由のみ。`sed -i`・リダイレクト・エディタ・Write/Edit
ツールでの直接編集は禁止（規約6.1）。復旧手段は journal のバックアップと Drive の版履歴
だけなので、疑わしい操作は行わない。

## 保存する内容の決め方

frontmatter と本文の雛形、キーの埋め方、slug の規則、index / log / hot への追記行は
**`references/page-template.md` を正とする**。ここには「何を1ページにするか」だけを書く。

### 1ページに切り出す条件

次の3つをすべて満たす塊を1ページにする。満たさないものは**保存せず、その旨を報告する**。

1. **再利用価値がある** — 後日、別の作業で参照して判断が変わり得る。単なる作業ログや
   進捗報告は保存しない。
2. **1つの主題に収まる** — 主題が1文で言える。複数主題なら分けるか、主題を絞る。
3. **確定している** — 検討中の選択肢の羅列ではなく、結論・仕様・観測結果として書ける。

そのうえで「担当範囲と境界」の判定を通し、外部原本があるものは `vault-ingest` へ回す。

**同一主題の既存ページがあれば、新規作成せず追記を提案する**（下記「既存ページへの追記・
書き換え」）。同じ主題のページが2枚できるのが最も避けたい状態で、slug は vault 全体で
1つの名前空間なので、似た名前のページが並ぶと後から追えなくなる。

### type の選択

| 条件 | type |
| --- | --- |
| 仕組み・仕様・設計判断・観測された挙動・方針など「事柄」 | `concept` |
| 企業・製品・人物・組織など、固有の実体そのものが主題 | `entity` |
| 外部原本がある | **作らない。`vault-ingest` へ回す** |

迷ったら `concept`。`entity` は「その実体の説明が主題」のときだけ使う。

## 被リンク先の選び方

**新規ページは、既存の非ハブページから1件以上リンクされていなければならない**（D-S1）。
新規ページ側から張る発リンクでは規則5 は解消しない。**被リンクが要る。**

### 候補の見つけ方（この順に実行する）

1. **新規ページ本文が既に言及しているページ。** 相互リンクになるので第一候補。
2. **キーワード検索。**
   ```bash
   grep -rl "<キーワード>" ~/Workspace/exocortex/wiki/concepts \
        ~/Workspace/exocortex/wiki/sources ~/Workspace/exocortex/wiki/entities
   ```
3. **tags の重なり。**
   ```bash
   grep -rl "  - <tag>" ~/Workspace/exocortex/wiki/concepts ~/Workspace/exocortex/wiki/entities
   ```
4. **`wiki/index.md` の同一節の説明文**から主題の近さを読む。

**ハブ5枚（`index.md` / `hot.md` / `log.md` / `dashboard.md` / `overview.md`）は候補にできない。**
`check_orphans` はハブからのリンクを被リンクに数えないため、ハブに載せても規則5 は消えない。

### 順位付け

候補が複数出たら次の優先順で **1〜2件**に絞る。上限2件（U-3）。増やすほど replace 対象が
増え、`original_sha256` 不一致のリスクと承認の負荷が上がる。

1. 新規ページから既に発リンクしている（相互リンクになる）
2. 主題の上位概念にあたるページ
3. `status: evergreen`（安定していて、リンクが将来も意味を保つ）
4. 現在 lint 規則5 で孤立しているページ（**相手の孤立は解消しないが**、島を増やさない）

「とりあえず繋ぐ」ための無関係なリンクを張らない。**内容上の関係を1文で説明できないなら
候補にしない。**

### 見つからない場合

**ページを作らずに止めてボスへ報告する。** 承認を求めない。報告に含めるもの:

- 実行した検索コマンドとヒット数
- 却下した候補と却下理由
- 選択肢: (1) 保存を見送る (2) 主題を既存ページへの追記に変える (3) ボスが被リンク元を指定する

### 被リンクの張り方

**被リンク元ページの frontmatter `related` へ `- "[[新slug]]"` を1行追加する。** 本文には
追記しない。本文が1バイトも変わらないため、検証モード `frontmatter-only` がそのまま使える。

## bundle の組み立て

作業ディレクトリは `~/Workspace/tmp/vaultctl-work/<operation_id>/`（規約5.1）。
`operation_id` は `save-<UTC+9 の YYYYMMDDTHHMMSS>-<slug>`（規約5.2）。
bundle / plan のスキーマは規約4節に従う。**ここでは writes の構成だけを決める。**

### 新規作成プロファイル（writes 5件）

| # | mode | path | 検証モード |
| - | --- | --- | --- |
| 1 | `create` | `wiki/{concepts,entities}/<slug>.md` | create の検証 |
| 2 | `replace` | `wiki/index.md` | `insert-only` |
| 3 | `replace` | 被リンク元の既存ページ | `frontmatter-only` |
| 4 | `replace` | `wiki/log.md` | `insert-only` |
| 5 | `replace` | `wiki/hot.md` | `insert-only` |

被リンク元が2件なら writes 6件になる。**`delete` は1件も含めない。**

### 既存ページへの追記・書き換え（writes 3件）

| # | mode | path | 検証モード |
| - | --- | --- | --- |
| 1 | `replace` | 対象の既存ページ | `insert-only` または `body-edit` |
| 2 | `replace` | `wiki/log.md` | `insert-only` |
| 3 | `replace` | `wiki/hot.md` | `insert-only` |

**`wiki/index.md` は触らない**（既に掲載済み）。**被リンクも追加しない**（既にリンクされている）。

節の追加や末尾への追記なら `insert-only`、既存本文の書き換え・削除を含むなら `body-edit`。

### 検証モードの宣言（必須）

`preflight.py` には **replace ごとの検証モードを宣言した JSON を渡す**。宣言が無い replace が
1件でもあると `[NG]` で止まる。**宣言し忘れて検査が素通りするのを防ぐため**であり、
省略できない。

```json
{
  "wiki/index.md":  {"mode": "insert-only", "line": "- [[slug]] — 説明", "section": "## Concepts"},
  "wiki/log.md":    {"mode": "insert-only", "line": "- 2026-08-19 — save — …", "section": "# Wiki Log"},
  "wiki/hot.md":    {"mode": "insert-only", "line": "- 2026-08-19: [[slug]] — …", "section": "## Last Updated"},
  "wiki/concepts/existing.md": {"mode": "frontmatter-only", "related_add": "[[slug]]"}
}
```

`body-edit` は `edits` に **`[旧テキスト, 新テキスト]` の配列**を宣言する。削除は新テキストを
空文字にする。**宣言に無い変更が1つでもあれば止まる。** 書き換えは「先に何をどう変えるかを
宣言し、実際の差分がそれと完全に一致することを確かめる」手順で行う。

```json
{"wiki/concepts/target.md": {"mode": "body-edit", "edits": [["旧い記述。", "新しい記述。"]]}}
```

## 検証と承認

この順序で進める。**飛ばさない。**

1. `vaultctl --vault ~/Workspace/exocortex plan --bundle <bundle> --out <plan>`
2. `scripts/preflight.py --vault ~/Workspace/exocortex --plan <plan> --bundle <bundle> --intent <intent>`
   — **全項目 `[OK]` でなければ先へ進まない**
3. 規約3.2 の提示ブロックを組み立ててボスへ提示する。**下記の追加節を必ず添える**
4. ボスの明示的な承認を得る
5. `vaultctl apply --plan <plan> --approved-plan-sha256 <承認された値>`
6. `lint --json` を再実行し、予測との一致を確認する（規約6.3）

### 提示に追加する節

規約3.2 の提示ブロックに次を**追加**する。規約3.2 の既定項目は1つも減らさない。

```
### 被リンク元の選定（規則5対策）

採用: wiki/concepts/<既存slug>.md
  理由: <相互リンクになる／上位概念にあたる 等>
  変更: frontmatter の related に - "[[<新slug>]]" を1行追加。本文は不変

検討して見送った候補:
| path | 却下理由 |
| ---- | -------- |

検索した範囲: grep -rl "<キーワード>" wiki/{concepts,sources,entities} → N件
```

### lint への影響の予測

**violation は増減しない。review は条件によって +1 になる。** 毎回この式で予測を立てる。

1. **violation は増えない。** 規則10-a の「ledger から参照されていない」は
   **`wiki/sources/**` にしか適用されない**ので、`concept` / `entity` を作る限り
   ledger を更新しなくても finding は増えない。他の violation 規則も、preflight を
   全項目 `[OK]` で通していれば先回りで潰れている。
2. **規則9-a のサマリは必ず文言が変わる**（その type の `developing` が1増える）。
   件数は変わらない。
3. **規則9-a の個別 finding は、適用前の `developing` の枚数で決まる。**
   個別 finding は `developing` を古い順に最大5件挙げる仕様なので、

   ```
   適用前の developing 枚数 k → 個別 finding は min(k, 5) 件
   適用後は k+1 枚          → 個別 finding は min(k+1, 5) 件
   したがって review の増分 = 1（k < 5 のとき） / 0（k >= 5 のとき）
   ```

   **「新規ページは updated が当日だから古い順5件に入らない」という理由づけは誤り。**
   キューが5件に満たなければ、当日更新のページでもそのまま並ぶ。2026-08-19 に合成 vault
   （`developing` 0枚）で実測して確認した。実 vault は `developing` が20枚超あるため
   増分は 0 になるが、**それは条件が満たされているからであって、常に 0 なのではない。**

**適用前に `k` を数えてから予測を書く。**

```bash
vaultctl --vault ~/Workspace/exocortex graph --json \
  | grep -c '"status": "developing"'
```

**サマリの文言が変わることを「件数が増えた」と誤読しない。** 件数と文言を分けて予測し、
分けて確認する。予測とずれたら次の write を発行せず、規約7節の停止規則に入る。

ボスが被リンク元を差し替えた場合は、**bundle の組み立てからやり直す。** `operation_id` も
新しい時刻で採番し直す（同じ ID は二度使えない）。承認後に `content_file` を書き換えない。

## 承認ルール

規約8節の `vault-save` 列を継承し、狭める方向にのみ上書きする。

**自律実行してよいこと**

- vault の読み取り・検索
- `lint` / `ledger verify` / `graph` / `recover --dry-run` の実行
- `~/Workspace/tmp/vaultctl-work/<operation_id>/` への中間ファイル・bundle の作成
- `vaultctl plan` の実行（vault を一切変更しないことを実装で確認済み）
- `scripts/preflight.py` によるプリフライト検証
- ページ案・被リンク案の作成と提示

**事前承認が必要なこと**

- `vaultctl apply`
- `vaultctl recover` の実行
- ディレクトリ構成・frontmatter schema・lint 規則の変更
- 会社情報を実名・実値のまま保存する判断
- Backlog / Notion など vault 外への転記

**この skill による上書き（狭める方向）**

- 被リンク元が1件も見つからない場合は、**ページを作らずに停止してボスへ報告する**（D-S1）。
  承認を求めない。
- 本文の内容に確信が持てない箇所は、創作して埋めず `## 根拠と留保` に未確認として書く。

## 禁止事項

規約6.1 を正とする。この skill 固有の禁止を加える。

1. **bundle に `mode=delete` を含めない。** `vault-save` の承認範囲に delete は無い。
   `preflight.py` が1件でも検出したら停止する。
2. **ledger（`source-ledger.json` / `claim-ledger.json`）を触らない。** `ledger stage` も
   呼ばない。会話由来の内容には `origin.locator` / `retrieved_at` / `content_sha256` /
   `refresh_due` のどれも存在せず、偽の値を入れると規則10-b の誤発火や匿名化違反を招く。
3. **`wiki/sources/` にページを作らない。** 原本があるなら `vault-ingest` の仕事。
4. **本文のコードフェンス内に `[[...]]` を書かない。** `graph.py::extract_links` は
   コードフェンスを除外しないため、コード例の中の wikilink も規則4（切れたリンク）の
   対象になる。
5. **見出しだけの節を作らない**（規則6）。直後により深い見出しが来る場合だけ免除される。
6. **`wiki/index.md` の末尾行を触らない。** 過去の非原子的書き込みで切断されており、
   本文に「（以下欠損：…復元不可）」と明記されている。
7. **既存の ledger・ハブの書式を勝手に変えない。** 書式変更は規約8節の「ディレクトリ構成・
   schema の変更」に準じ、事前承認が要る。

## 報告

適用後は次を報告する。

1. **作成・変更したファイル** — path と mode の一覧
2. **被リンク元** — どのページの `related` に張ったか、なぜそのページを選んだか
3. **lint の実測差分** — 適用前後の `violation` / `review` の件数と、予測との一致
4. **未確認事項** — `## 根拠と留保` に書いた内容の要約
5. **次アクション** — 裏取りが要る場合の回付先（research など）

予測と実測がずれた場合は、**追加の write を発行せず**、`lint --json` の差分を提示して
指示を仰ぐ（規約7節）。

## 同梱物

| ファイル | 用途 |
| --- | --- |
| `references/page-template.md` | `concept` / `entity` の frontmatter と本文の雛形、埋め方の注記 |
| `scripts/preflight.py` | 規約6.2 の検証を機械実行する。`plan.json` と vault root を受け取る |

`preflight.py` は実行時に作業ディレクトリ（`~/Workspace/tmp/vaultctl-work/<operation_id>/`）
へコピーして走らせる。規約6.2 の「検証スクリプトは作業ディレクトリに置いて実行する」を
満たしつつ、毎回書き起こして停止規則が形骸化するのを防ぐため。
