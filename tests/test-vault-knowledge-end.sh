#!/bin/bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
src="$repo_root/dot_local/bin/executable_vault-knowledge-end.tmpl"

command -v jq >/dev/null 2>&1 || { printf 'skip: jq が無い\n'; exit 0; }

test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-vault-knowledge-end.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok: %s\n' "$1"; }

vault="$test_root/vault"
mkdir -p "$vault/00_Inbox" "$vault/20_Knowledge" "$vault/90_System"

# chezmoi テンプレートの {{ ... }} を実値へ置換して実行可能にする
hook="$test_root/vault-knowledge-end"
python3 - "$src" "$hook" "$vault" <<'PY'
import re, sys
src, dst, vault = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src, encoding="utf-8").read()
s = re.sub(r'\{\{[^}]*\}\}', '"%s"' % vault, s)
open(dst, "w", encoding="utf-8").write(s)
PY
chmod +x "$hook"

export HOME="$test_root/home"
mkdir -p "$HOME"
export KNOWLEDGE_VAULT="$vault"

# headless LLM を実際に呼ばないようスタブへ差し替える。呼ばれた事実だけ記録する。
stub_bin="$test_root/stub-bin"
mkdir -p "$stub_bin"
cat > "$stub_bin/claude" <<'STUB'
#!/bin/sh
printf '%s\n' "$*" >> "${VAULT_TEST_STUB_LOG}"
exit 0
STUB
chmod +x "$stub_bin/claude"
cp "$stub_bin/claude" "$stub_bin/codex"
export VAULT_TEST_STUB_LOG="$test_root/stub-calls.log"
: > "$VAULT_TEST_STUB_LOG"
export PATH="$stub_bin:$PATH"

# 2000バイトゲートを超える長さのトランスクリプトを作る
tpath="$test_root/transcript.jsonl"
: > "$tpath"
i=0
while [ "$i" -lt 40 ]; do
  printf '{"type":"user","message":{"content":"これは検証用の発言です。ダイジェストのバイト数ゲートを超えるために十分な長さを持たせています。%s"}}\n' "$i" >> "$tpath"
  printf '{"type":"assistant","message":{"content":[{"type":"text","text":"了解しました。これは検証用の応答です。同様に十分な長さを持たせています。%s"}]}}\n' "$i" >> "$tpath"
  i=$(( i + 1 ))
done

payload() {
  printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","hook_event_name":"SessionEnd"}' \
    "$1" "$2" "$test_root"
}

count_proposals() { find "$vault/00_Inbox" -name 'proposal-*.md' | wc -l | tr -d ' '; }

# 1. 提案ファイルが Inbox に作られる
printf '%s' "$(payload abcd1234efgh5678 "$tpath")" | "$hook" claude
[ "$(count_proposals)" = "1" ] || fail "提案ファイルが1件作られていない（$(count_proposals)件）"
ok "提案ファイルが作られる"

f=$(find "$vault/00_Inbox" -name 'proposal-*.md' | head -1)

# 2. ファイル名が規約どおり
case "$(basename "$f")" in
  proposal-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]-abcd1234.md) ;;
  *) fail "ファイル名が規約と違う: $(basename "$f")" ;;
esac
ok "ファイル名が proposal-<YYYYMMDD-HHMMSS>-<session-id 先頭8文字>.md"

# 3. frontmatter が揃っている
grep -q '^session_id: abcd1234efgh5678' "$f" || fail "session_id が無い"
grep -q '^cwd:' "$f" || fail "cwd が無い"
grep -q '^type: source' "$f" || fail "type: source が無い"
grep -q '^host: claude' "$f" || fail "host が無い"
ok "frontmatter が揃っている"

# 4. 正典に触れていない
[ -z "$(find "$vault/20_Knowledge" "$vault/90_System" -type f 2>/dev/null)" ] \
  || fail "正典配下にファイルが作られている"
ok "正典に触れていない"

# 5. ダイジェスト本文が入っている
grep -q '検証用の発言です' "$f" || fail "ダイジェスト本文が入っていない"
ok "ダイジェスト本文が入っている"

# 6. 同一セッション・同一行数の再発火では増えない
printf '%s' "$(payload abcd1234efgh5678 "$tpath")" | "$hook" claude
[ "$(count_proposals)" = "1" ] || fail "二重起動で提案が増えた（$(count_proposals)件）"
ok "二重起動しても増えない"

# 7. 短いセッションでは投函しない
short="$test_root/short.jsonl"
printf '{"type":"user","message":{"content":"hi"}}\n' > "$short"
printf '%s' "$(payload shortsess0000 "$short")" | "$hook" claude
[ "$(count_proposals)" = "1" ] || fail "短いセッションで投函された（$(count_proposals)件）"
ok "2000バイト未満は投函しない"

# 8. ロックは撤去されている（gitに触らないため不要）
grep -q 'LOCK_DIR' "$src" && fail "ロックの残骸がある"
ok "ロックが撤去されている"

# 9. 生ダイジェストが先に投函されている（headlessが失敗してもキャプチャは残る）
grep -q 'この時点では生のダイジェスト' "$f" || fail "暫定である旨の注記が無い"
ok "生ダイジェストを先に投函し、暫定である旨を明記している"

# 10. headless 要約が detach で起動される
grep -qE 'claude -p' "$src" || fail "claude の headless 起動が無い"
grep -qE 'codex exec' "$src" || fail "codex の headless 起動が無い"
grep -q 'disown' "$src" || fail "detach していない"
grep -q 'VAULT_KNOWLEDGE_HOOK_ACTIVE' "$src" || fail "再帰ガードが無い"
ok "headless 要約を detach で起動し、再帰ガードがある"

# 11. headless に git 系ツールを渡していない
grep -q 'Bash(git' "$src" && fail "headless に git ツールを渡している"
grep -q 'allowedTools "Read,Write,Edit,Grep,Glob"' "$src" \
  || fail "allowedTools が想定と違う"
ok "headless に git 系ツールを渡していない"

# 12. スタブが実際に呼ばれた（detachなので少し待つ）
waited=0
while [ ! -s "$VAULT_TEST_STUB_LOG" ] && [ "$waited" -lt 10 ]; do
  sleep 1; waited=$(( waited + 1 ))
done
[ -s "$VAULT_TEST_STUB_LOG" ] || fail "headless が起動されていない（${waited}秒待機）"
grep -q -- "-p" "$VAULT_TEST_STUB_LOG" || fail "claude -p の形で呼ばれていない"
ok "headless が実際に起動される"

printf '\nすべて通過\n'
