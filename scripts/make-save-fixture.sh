#!/usr/bin/env bash
# expected: violation=0 / review=1 (rule9-a=1)
# 規則9-a は知識ページが1枚でもあれば type 別比率を常時出すため、review 0にはできない。

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

mkdir -p "$dest/wiki/concepts" "$dest/inbox"

cat >"$dest/wiki/index.md" <<'EOF'
---
type: meta
title: Save fixture index
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
---

# Wiki Index

## Sources

No source pages.

## Entities

No entity pages.

## Concepts

- [[fixture-related]] — Related key を持つ被リンク候補
- [[fixture-plain]] — Related key を持たない被リンク候補
- [[fixture-target]] — 追記・書き換え対象
EOF

cat >"$dest/wiki/log.md" <<'EOF'
---
type: meta
title: Wiki Log
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
---

# Wiki Log

- 2026-08-18 — fixture — 合成 vault を作成した。
EOF

cat >"$dest/wiki/hot.md" <<'EOF'
---
type: meta
title: Hot Topics
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
---

# Hot Topics

## Last Updated

- 2026-08-18: [[fixture-target]]
EOF

cat >"$dest/wiki/overview.md" <<'EOF'
---
type: overview
title: Save fixture overview
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
---

# Save fixture overview

This synthetic vault exercises vault-save without copying the real vault.
EOF

cat >"$dest/wiki/concepts/fixture-related.md" <<'EOF'
---
type: concept
title: Fixture related
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
related:
  - "[[fixture-plain]]"
---

# Fixture related

This page has a related key and links to [[fixture-plain]].
EOF

cat >"$dest/wiki/concepts/fixture-plain.md" <<'EOF'
---
type: concept
title: Fixture plain
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
---

# Fixture plain

This page has no related key and links to [[fixture-target]].
EOF

cat >"$dest/wiki/concepts/fixture-target.md" <<'EOF'
---
type: concept
title: Fixture target
status: evergreen
created: 2026-08-18
updated: 2026-08-18
tags: []
related:
  - "[[fixture-related]]"
---

# Fixture target

This existing page can be edited by the append profile and links to [[fixture-related]].

## Existing observations

The body has multiple populated sections for body-edit fixtures.

## Existing constraints

Edits must preserve every undeclared block.
EOF
