#!/usr/bin/env bash
# expected: rule2=1 rule3=1 rule4=1 rule5=2 rule6=1 rule7=2 / violation=8
# fixture-ghost は index 上の幽霊リンクなので、規則4と規則7の両方に意図的に該当する。

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

mkdir -p "$dest/wiki/concepts" "$dest/wiki/sources" "$dest/wiki/meta/ledgers" "$dest/inbox"

write_page() {
  local path=$1 type=$2 title=$3 created=$4 updated=$5 body=$6
  cat >"$dest/$path" <<EOF
---
type: $type
title: $title
status: evergreen
created: $created
updated: $updated
tags: []
---

$body
EOF
}

write_page "wiki/index.md" meta "Fixture index" 2026-08-18 2026-08-18 \
  $'# Wiki Index\n\n## Sources\n\n- [[fixture-badtype]] — Fixture bad type\n- [[fixture-ghost]] — Fixture ghost\n\n## Entities\n\nNo entity pages.\n\n## Concepts\n\n- [[fixture-orphan]] — Fixture orphan\n- [[fixture-empty-section]] — Fixture empty section\n- [[fixture-baddate]] — Fixture bad date\n- [[fixture-connector]] — Fixture connector'

write_page "wiki/concepts/fixture-orphan.md" concept "Fixture orphan" 2026-08-18 2026-08-18 \
  $'# Fixture orphan\n\nThis page deliberately has no incoming link outside the hub. It links to [[fixture-connector]].'

write_page "wiki/concepts/fixture-badtype.md" source "Fixture bad type" 2026-08-18 2026-08-18 \
  $'# Fixture bad type\n\nThis source is deliberately stored under concepts. See [[fixture-empty-section]].'

write_page "wiki/concepts/fixture-empty-section.md" concept "Fixture empty section" 2026-08-18 2026-08-18 \
  $'# Fixture empty section\n\nThis page links to [[fixture-baddate]].\n\n## Deliberately empty'

write_page "wiki/concepts/fixture-baddate.md" concept "Fixture bad date" 2026-08-18 2026-08-17 \
  $'# Fixture bad date\n\nThis page links to [[fixture-connector]].'

write_page "wiki/concepts/fixture-connector.md" concept "Fixture connector" 2026-08-18 2026-08-18 \
  $'# Fixture connector\n\nThis page supplies a backlink to [[fixture-badtype]].'

write_page "wiki/sources/fixture-unlisted.md" source "Fixture unlisted" 2026-08-18 2026-08-18 \
  $'# Fixture unlisted\n\nThis page is deliberately absent from the index and has no incoming link.'

cat >"$dest/wiki/meta/ledgers/source-ledger.json" <<'EOF'
{
  "generated_at": "2026-08-18",
  "schema": "vaultctl.source-ledger.v1",
  "sources": {
    "src-fixture-badtype": {
      "pages": ["wiki/concepts/fixture-badtype.md"],
      "refresh_due": "2099-01-01",
      "review_status": "active"
    },
    "src-fixture-unlisted": {
      "pages": ["wiki/sources/fixture-unlisted.md"],
      "refresh_due": "2099-01-01",
      "review_status": "active"
    }
  }
}
EOF

cat >"$dest/wiki/meta/ledgers/claim-ledger.json" <<'EOF'
{
  "claims": {},
  "generated_at": "2026-08-18",
  "schema": "vaultctl.claim-ledger.v1"
}
EOF
