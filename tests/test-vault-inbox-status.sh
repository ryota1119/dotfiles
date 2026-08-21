#!/bin/bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
bin="$repo_root/dot_local/bin/executable_vault-inbox-status"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-vault-inbox-status.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok: %s\n' "$1"; }

vault="$test_root/vault"; mkdir -p "$vault/00_Inbox"
export KNOWLEDGE_VAULT="$vault"
export HOME="$test_root/home"; mkdir -p "$HOME"

# 1. 0件なら何も出さない
out=$("$bin")
[ -z "$out" ] || fail "0件なのに出力があった: $out"
ok "0件なら無音"

# 2. 2件あれば件数を含む有効なJSONを出す
printf 'a\n' > "$vault/00_Inbox/proposal-20260821-100000-aaaaaaaa.md"
printf 'b\n' > "$vault/00_Inbox/proposal-20260821-110000-bbbbbbbb.md"
out=$("$bin")
printf '%s' "$out" | python3 -c "import json,sys; json.load(sys.stdin)" \
  || fail "出力が有効なJSONでない"
printf '%s' "$out" | python3 -c "
import json,sys
d = json.load(sys.stdin)
h = d.get('hookSpecificOutput', {})
assert h.get('hookEventName') == 'SessionStart', 'hookEventName が違う'
ctx = h.get('additionalContext', '')
assert '2' in ctx, 'additionalContext に件数が無い'
assert 'Inbox' in ctx, 'additionalContext に Inbox の語が無い'
" || fail "additionalContext の中身が期待と違う"
ok "2件で additionalContext を出す"

# 3. proposal 以外のファイルは数えない
printf 'x\n' > "$vault/00_Inbox/memo.md"
out=$("$bin")
printf '%s' "$out" | python3 -c "
import json,sys
ctx = json.load(sys.stdin)['hookSpecificOutput']['additionalContext']
assert '3' not in ctx, 'proposal以外を数えている: ' + ctx
" || fail "proposal以外を数えている"
ok "proposal-*.md だけを数える"

# 4. サブディレクトリの proposal は数えない（maxdepth 1）
mkdir -p "$vault/00_Inbox/sub"
printf 'c\n' > "$vault/00_Inbox/sub/proposal-20260821-120000-cccccccc.md"
out=$("$bin")
printf '%s' "$out" | python3 -c "
import json,sys
ctx = json.load(sys.stdin)['hookSpecificOutput']['additionalContext']
assert '3' not in ctx, 'サブディレクトリを数えている: ' + ctx
" || fail "サブディレクトリを数えている"
ok "サブディレクトリは数えない"

# 5. Vault が無くても落ちない
KNOWLEDGE_VAULT="$test_root/nonexistent" "$bin" >/dev/null 2>&1 \
  || fail "Vaultが無いときに非0で終了した"
ok "Vaultが無くても exit 0"

# 6. KNOWLEDGE_VAULT 未設定でも落ちない
( env -u KNOWLEDGE_VAULT HOME="$HOME" "$bin" >/dev/null 2>&1 ) \
  || fail "KNOWLEDGE_VAULT未設定で非0になった"
ok "KNOWLEDGE_VAULT未設定でも exit 0"

printf '\nすべて通過\n'
