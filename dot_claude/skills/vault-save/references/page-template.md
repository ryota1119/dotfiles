# ページ雛形と埋め方

`vault-save` が作れるのは `concept` と `entity` の2種だけ（D-T13-2）。
`source` は原本があるということなので `vault-ingest` へ回す。

キーの定義は `vaultctl` の `schema.py`（`REQUIRED_KEYS` / `EXTRA_KEYS` / `KEY_ORDER`）が正。
ここに書いてある内容とずれたら **`schema.py` を正とし、この雛形を直す**。
`scripts/preflight.py` の `schema照合` 検査が、ずれを実行時に検出する。

---

## concept の雛形

```yaml
---
type: concept
title: "<日本語のタイトル>"
status: developing
created: <当日 YYYY-MM-DD>
updated: <当日 YYYY-MM-DD。created と同じ>
tags:
  - concept
  - <ドメインtag>
  - "<YYYY-MM>"
domain: <対象領域を一文で。不要なら書かない>
related:
  - "[[<関連する既存slug>]]"
---
```

## entity の雛形

```yaml
---
type: entity
title: "<固有名>"
status: developing
created: <当日 YYYY-MM-DD>
updated: <当日 YYYY-MM-DD>
tags:
  - entity
  - "<YYYY-MM>"
aliases:
  - "<別名>"
related:
  - "[[<関連する既存slug>]]"
---
```

`entity` に使える拡張キーは **`aliases` と `related` だけ**。`domain` や `sources` は
規則1 の「type=entity では使えないキーです」で落ちる。

---

## キーの埋め方

| キー | 埋め方 | 落ちる規則 |
| --- | --- | --- |
| `type` | `concept` / `entity` のみ | 規則1・3 |
| `title` | 日本語可。空にしない。**`: ` を含む、または `:` `#` `[` `{` `&` `*` で始まる場合はダブルクォートで囲む** | 規則1 |
| `status` | 既定は `developing`。`evergreen` はボスが明示的にそう述べたときだけ | 規則1 |
| `created` / `updated` | `date +%F` の出力をそのまま。**`/` 区切りにしない。** 新規作成では両方が当日 | 規則2 |
| `tags` | 文字列リスト。1件目は type 名、以降にドメインtag、末尾に年月。**年月は `"2026-08"` とダブルクォートで囲む**（囲まないと YAML が数値や日付として解釈しうる） | 規則1 |
| `domain` / `related` / `sources` / `assessment` / `risk` | `concept` のみ | 規則1 |
| `aliases` / `related` | `entity` のみ | 規則1 |

**書いてはならないキー:** `address`（全ページから除去済み）、`claim_ids`（`source` 専用）、
`complexity`、`created_by` などの独自キー。`KEY_ORDER` に無いキーは規則1 の
「未定義のキーです」で必ず落ちる。

`related` の値は `- "[[slug]]"` の形（ダブルクォート付き）にする。実 vault の27ファイルが
この書き方をしている。**frontmatter の `related` / `sources` もリンクとして数えられる**ので、
存在しない slug を書くと規則4 を踏む。

---

## slug の付け方

- `concept`: `<主題を表す英数ハイフン>-YYYY-MM`（例 `stimulus-action-scope-2026-08`）。`YYYY-MM` は作成月
- `entity`: 固有名を小文字ハイフンにしたもの（例 `cloudflare`）。**日付を付けない**
- 使える文字は**小文字英数とハイフンのみ**。日本語・空白・アンダースコア・大文字を使わない

**slug は vault 全体で1つの名前空間**であり、重複すると先に読まれた方が勝って、もう片方が
グラフから消える。作る前に必ず確認する。

```bash
ls ~/Workspace/exocortex/wiki/concepts/<slug>.md \
   ~/Workspace/exocortex/wiki/sources/<slug>.md \
   ~/Workspace/exocortex/wiki/entities/<slug>.md 2>/dev/null
```

1件でもヒットしたら**新規作成せず**、既存ページの存在をボスへ報告する。`mode=create` は
`plan` の時点で落ちるが、その前に気づくほうが早い。

---

## 本文の構成

```markdown
# <title と同じ文字列>

<リード段落: 結論を2〜4行で。なぜ記録するかを1行添える>

## <観測・仕様・構造など主題に応じた節>

<本文>

## <必要なだけ節を足す>

## 根拠と留保

<何に基づくか（会話・実装作業・実測）、裏取りの状況、status を developing にした理由>
```

### 必ず守ること

1. **見出しだけの節を作らない**（規則6）。節を立てたら必ず本文を書く。直後により深い見出しが
   来る場合だけ免除される。
2. **コードフェンスの中に `[[...]]` を書かない**（規則4）。`extract_links` はコードフェンスを
   除外しないので、コード例の中の wikilink も実在チェックの対象になる。
3. 本文から既存ページへ `[[slug]]` で1本以上リンクする。**これは規則5 の解消にはならない**
   （被リンクが要る）が、グラフの断絶を防ぐ。リンク先 slug の実在を必ず確認する。
4. **`## 根拠と留保` は必ず書く。** `vault-save` の内容は ledger に登録されないため、
   **出所を担保するのはこの節だけ**である。次を明記する。
   - 何に基づくか（会話・実装作業・実測のどれか）
   - 裏取りの状況
   - **「原本ソースが無いため source-ledger・claim-ledger は更新していない」**
   - `status` を `developing` にした理由
5. 会社関連の内容は `exocortex/CLAUDE.md` の匿名化ルールに従う。プロジェクト名・クライアント名・
   システム固有名を伏せる。**実名・実値のまま保存する判断は要承認。**

---

## `wiki/index.md` の掲載行

`type` に対応する節の**末尾**に1行挿入する。

```
- [[<slug>]] — <1行の説明。ページを開かずに何が書いてあるか分かる粒度>
```

| `type` | 挿入先 |
| --- | --- |
| `concept` | `## Concepts` |
| `entity` | `## Entities` |

**`## Concepts` 節の最終行は過去の書き込み事故で切断されており、本文に「（以下欠損：…復元不可）」
と明記されている。この行を修正・削除しない。** その後ろに足すだけにする。修復は `vault-review`
と Phase 3 の担当。

## `wiki/log.md` の追記行

`# Wiki Log` 見出しの直後（最新エントリの上）に1行挿入する。**要点1〜3文に収める**（U-2）。
詳細は保存したページ本文に持たせ、log は「いつ何をしたか」の索引に徹する。

```
- <YYYY-MM-DD> — save — <何を保存したか。[[slug]] を含める。被リンク元と、ledger を更新していないこと>
```

**「原本ソースが無いため source-ledger・claim-ledger は更新していない」を必ず含める。**
実 vault の既存18件が守っている書き方で、後から出所を追うときの手掛かりになる。

## `wiki/hot.md` の追記行

`## Last Updated` 見出しの直後に1行挿入する。

```
- <YYYY-MM-DD>: [[<slug>]] — <ごく短い要約>
```

**既存エントリに `旧: ` を付けない**（U-1）。実 vault の現行慣習とは変えている。既存行を
書き換えると規約6.2 の検証が使えなくなるため、**挿入だけ**にする。
