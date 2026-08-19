#!/usr/bin/env bash
# vault-ingest のテスト用の合成 vault を作る。
#
# 他の2本の fixture との違い:
#   make-fixture-vault.sh  (vault-review) … finding を意図的に含む「汚い」vault
#   make-save-fixture.sh   (vault-save)   … violation 0 件の「きれいな」vault
#   make-ingest-fixture.sh (これ)          … 上記に加えて inbox/ と .raw/ と
#                                            source-ledger のエントリを持つ
#
# expected: violation=0 review=1
#   review の1件は規則9-a の type=source サマリ。ページを置く限り 0 にはできない。
#
# inbox に置くファイルと、その分類（計画3.1）:
#   reconcile-source.md      manifest あり・hash 一致・ページ実在・ledger 参照あり → reconcile
#   fresh-source.md          manifest に無い                                      → ingest
#   drifted-source.md        manifest あり・hash 不一致                            → inconsistent(A)
#   orphan-page-source.md    manifest あり・pages_created が実在しない             → inconsistent(B)
#   unledgered-source.md     manifest あり・ページ実在・ledger 参照なし            → inconsistent(C)
#
# 実 vault からは複製しない（規約6.1の2）。全ファイルをここで生成する。

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /abs/dest" >&2
  exit 64
fi

dest=$1
if [[ $dest != /* ]]; then
  echo "error: destination must be an absolute path: $dest" >&2
  exit 64
fi
if [[ -e $dest || -L $dest ]]; then
  echo "error: destination already exists: $dest" >&2
  exit 1
fi

mkdir -p "$dest/wiki/concepts" "$dest/wiki/sources" "$dest/wiki/entities" \
         "$dest/wiki/meta/ledgers" "$dest/inbox" "$dest/.raw"

write_page() {
  local relpath=$1 frontmatter=$2 body=$3
  printf -- '---\n%s---\n\n%s\n' "$frontmatter" "$body" > "$dest/$relpath"
}

# --- 知識ページ -------------------------------------------------------------

write_page "wiki/sources/reconcile-topic-2026-08.md" \
'type: source
title: Reconcile topic
status: evergreen
created: 2026-08-19
updated: 2026-08-19
tags: []
related:
  - "[[unledgered-topic-2026-08]]"
' '# Reconcile topic

処理済みで原本だけが inbox に残っているソースのページ。
[[unledgered-topic-2026-08]] を参照する。'

write_page "wiki/sources/unledgered-topic-2026-08.md" \
'type: source
title: Unledgered topic
status: evergreen
created: 2026-08-19
updated: 2026-08-19
tags: []
related:
  - "[[reconcile-topic-2026-08]]"
' '# Unledgered topic

ページは実在するが source-ledger から参照されていないソース。
[[reconcile-topic-2026-08]] を参照する。'

write_page "wiki/index.md" \
'type: meta
title: Ingest fixture index
status: evergreen
created: 2026-08-19
updated: 2026-08-19
tags: []
' '# Wiki Index

## Sources

- [[reconcile-topic-2026-08]] — Reconcile topic
- [[unledgered-topic-2026-08]] — Unledgered topic

## Entities

No entity pages.

## Concepts

No concept pages.'

write_page "wiki/log.md" \
'type: meta
title: Wiki Log
status: evergreen
created: 2026-08-19
updated: 2026-08-19
tags: []
' '# Wiki Log

- 2026-08-19 — fixture — 合成 vault を作成した。'

write_page "wiki/hot.md" \
'type: meta
title: Hot Topics
status: evergreen
created: 2026-08-19
updated: 2026-08-19
tags: []
' '# Hot Topics

## Last Updated

- 2026-08-19: fixture の初期状態。'

# --- inbox の原本 -----------------------------------------------------------

printf 'reconcile されるべき原本。\n'        > "$dest/inbox/reconcile-source.md"
printf '未処理の原本。まだページが無い。\n'   > "$dest/inbox/fresh-source.md"
printf '取り込み後に書き換えられた原本。\n'   > "$dest/inbox/drifted-source.md"
printf 'ページが消された原本。\n'             > "$dest/inbox/orphan-page-source.md"
printf 'ledger に載っていない原本。\n'        > "$dest/inbox/unledgered-source.md"

sha() { shasum -a 256 "$1" | cut -d' ' -f1; }

# --- .raw/.manifest.json ----------------------------------------------------
# drifted は「取り込み時とは違う hash」を意図的に書く。

cat > "$dest/.raw/.manifest.json" <<JSON
{
  "version": 1,
  "description": "Ingest delta tracker. Source payloads are create-only.",
  "sources": {
    "inbox/reconcile-source.md": {
      "hash": "$(sha "$dest/inbox/reconcile-source.md")",
      "pages_created": ["wiki/sources/reconcile-topic-2026-08.md"]
    },
    "inbox/drifted-source.md": {
      "hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "pages_created": ["wiki/sources/reconcile-topic-2026-08.md"]
    },
    "inbox/orphan-page-source.md": {
      "hash": "$(sha "$dest/inbox/orphan-page-source.md")",
      "pages_created": ["wiki/sources/deleted-topic-2026-08.md"]
    },
    "inbox/unledgered-source.md": {
      "hash": "$(sha "$dest/inbox/unledgered-source.md")",
      "pages_created": ["wiki/sources/unledgered-topic-2026-08.md"]
    }
  }
}
JSON

# --- ledger -----------------------------------------------------------------
# reconcile-topic だけを登録する。unledgered-topic は意図的に登録しない。
# locator は inbox/ を指す（実 vault と同じ状態。T14-4 の Tx-B で .raw/ へ書き換える）。

cat > "$dest/wiki/meta/ledgers/source-ledger.json" <<JSON
{
  "schema": "vaultctl.source-ledger.v1",
  "generated_at": "2026-08-19",
  "sources": {
    "src-fixture-reconcile00": {
      "authority": "official",
      "content_kind": "webpage",
      "content_sha256": "$(sha "$dest/inbox/reconcile-source.md")",
      "origin": { "kind": "file", "locator": "inbox/reconcile-source.md" },
      "pages": ["wiki/sources/reconcile-topic-2026-08.md"],
      "refresh_due": "2099-01-01",
      "retrieved_at": "2026-08-19",
      "review_status": "active",
      "title": "Reconcile topic"
    }
  }
}
JSON

cat > "$dest/wiki/meta/ledgers/claim-ledger.json" <<'JSON'
{
  "schema": "vaultctl.claim-ledger.v1",
  "generated_at": "2026-08-19",
  "claims": {}
}
JSON

echo "$dest"
