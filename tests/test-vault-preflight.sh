#!/bin/bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
pf_bin="$repo_root/dot_local/bin/executable_vault-preflight"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-vault-preflight.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok: %s\n' "$1"; }

# 毎回まっさらなリポジトリを作る
new_repo() {
  local d="$test_root/repo-$1"
  rm -rf "$d"; mkdir -p "$d/20_Knowledge/concepts" "$d/90_System"
  (
    cd "$d"
    git init -q
    git config user.email t@example.com
    git config user.name test
    cat > 20_Knowledge/concepts/note-a.md <<'EOF'
---
type: concept
title: "A"
updated: 2026-08-20
---

# A

line 1
line 2
line 3
line 4
line 5
line 6
line 7
line 8
line 9
line 10
EOF
    printf '# hot\n' > 90_System/hot.md
    git add -A
    git commit -q -m init
  )
  printf '%s' "$d"
}

# 実行して exit code を返す（出力は捨てる）
pf_code() { ( cd "$1" && VAULT_PREFLIGHT_REPO="$1" "$pf_bin" >/dev/null 2>&1 ); echo $?; }
# 実行して標準出力を返す
pf_out()  { ( cd "$1" && VAULT_PREFLIGHT_REPO="$1" "$pf_bin" 2>/dev/null ) || true; }

# 1. クリーンなら exit 0
r=$(new_repo clean)
[ "$(pf_code "$r")" = "0" ] || fail "クリーンなリポジトリで非0になった"
ok "クリーンなら exit 0"

# 2. 未追跡の追加だけなら exit 0 かつ自動commitされる
r=$(new_repo untracked)
printf 'new note\n' > "$r/20_Knowledge/concepts/note-new.md"
[ "$(pf_code "$r")" = "0" ] || fail "未追跡の追加で非0になった"
[ -z "$(cd "$r" && git status --porcelain)" ] || fail "未追跡の追加が自動commitされていない"
ok "未追跡の追加は自動commitして exit 0"

# 3. updated が進んでいて内容が変わっただけなら exit 0
r=$(new_repo normal_edit)
python3 - "$r" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "20_Knowledge/concepts/note-a.md"
s = p.read_text()
s = s.replace("updated: 2026-08-20", "updated: 2026-08-21")
s = s.replace("line 3", "line 3 revised")
p.write_text(s)
PY
[ "$(pf_code "$r")" = "0" ] || fail "正当な編集で非0になった"
ok "updatedが進んだ編集は exit 0"

# 4. updated が据え置きで本文が縮んだら exit 2
r=$(new_repo shrink)
python3 - "$r" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "20_Knowledge/concepts/note-a.md"
s = p.read_text()
for n in (8, 9, 10):
    s = s.replace(f"line {n}\n", "")
p.write_text(s)
PY
[ "$(pf_code "$r")" = "2" ] || fail "updated据え置きの縮小を exit 2 で検出できなかった"
pf_out "$r" | grep -q 'SIGNATURE: stale-updated' || fail "stale-updated のSIGNATURE行が出ていない"
ok "updated据え置きの縮小を exit 2 で検出"

# 5. 複数ファイルのmtimeが秒単位で一致したら exit 2
r=$(new_repo mtime)
python3 - "$r" <<'PY'
import sys, pathlib
d = pathlib.Path(sys.argv[1])
for rel in ("20_Knowledge/concepts/note-a.md", "90_System/hot.md"):
    p = d / rel
    s = p.read_text()
    s = s.replace("updated: 2026-08-20", "updated: 2026-08-21")
    p.write_text(s + "extra line\n")
PY
touch -t 202608202344.20 "$r/20_Knowledge/concepts/note-a.md" "$r/90_System/hot.md"
[ "$(pf_code "$r")" = "2" ] || fail "mtime一致を exit 2 で検出できなかった"
pf_out "$r" | grep -q 'SIGNATURE: mtime-cluster' || fail "mtime-cluster のSIGNATURE行が出ていない"
ok "mtime一致を exit 2 で検出"

# 6. 大量削除は exit 2（updated は進めておき、削除量だけで判定させる）
r=$(new_repo bigdel)
python3 - "$r" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "20_Knowledge/concepts/note-a.md"
p.write_text('---\ntype: concept\ntitle: "A"\nupdated: 2026-08-21\n---\n')
PY
[ "$(pf_code "$r")" = "2" ] || fail "大量削除を exit 2 で検出できなかった"
pf_out "$r" | grep -q 'SIGNATURE: large-deletion' || fail "large-deletion のSIGNATURE行が出ていない"
ok "大量削除を exit 2 で検出"

# 7. UTF-8 として読めないファイルは exit 2
r=$(new_repo utf8)
printf 'valid start \xe3\x81 ' > "$r/20_Knowledge/concepts/note-a.md"
[ "$(pf_code "$r")" = "2" ] || fail "不正UTF-8を exit 2 で検出できなかった"
pf_out "$r" | grep -q 'SIGNATURE: invalid-utf8' || fail "invalid-utf8 のSIGNATURE行が出ていない"
ok "不正UTF-8を exit 2 で検出"

# 8. gitリポジトリでなければ exit 1
d="$test_root/notrepo"; mkdir -p "$d"
[ "$(pf_code "$d")" = "1" ] || fail "非gitディレクトリの exit code が 1 でない"
ok "非gitディレクトリは exit 1"

# 9. KNOWLEDGE_VAULT も VAULT_PREFLIGHT_REPO も未設定なら exit 1
( env -u KNOWLEDGE_VAULT -u VAULT_PREFLIGHT_REPO "$pf_bin" >/dev/null 2>&1 ) && \
  fail "未設定なのに成功してしまった"
ok "パス未設定は exit 1"

printf '\nすべて通過\n'
