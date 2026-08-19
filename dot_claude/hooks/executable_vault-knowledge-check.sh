#!/bin/bash
# セッションが終わる直前に一度だけ、再利用可能なナレッジをKnowledge Vaultへ
# 保存するようClaudeへ促す。Stopフックとして使う。
#
# 設計上の判断:
#   - SessionEnd ではなく Stop を使う。SessionEnd はセッション終了後に走るため、
#     その時点でClaudeに保存作業をさせられない。
#   - Stop は毎ターン発火するので、session_id ごとのマーカーで1回に絞る。
#   - すでに vault-save / vault-ingest を使ったセッションでは促さない。
#   - 短いセッション（雑談・単発の質問）では促さない。
set -uo pipefail

STATE_DIR="${HOME}/.claude/.vault-knowledge-check"
MIN_LINES=60          # これ未満のトランスクリプトは「作業らしい会話」とみなさない

input=$(cat 2>/dev/null || true)
[ -z "$input" ] && exit 0

sid=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null || true)
tpath=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null || true)

# session_id が取れないなら何もしない（安全側）
[ -z "$sid" ] && exit 0

mkdir -p "$STATE_DIR" 2>/dev/null || exit 0
marker="${STATE_DIR}/${sid}"

# 2回目以降は黙って抜ける（ループ防止）
[ -e "$marker" ] && exit 0

# ここから先は一度しか通らない。判定前にマーカーを立てる
: > "$marker"

# トランスクリプトが読めないなら促さない（誤検知を避ける）
[ -z "$tpath" ] || [ ! -f "$tpath" ] && exit 0

lines=$(wc -l < "$tpath" 2>/dev/null || echo 0)
[ "$lines" -lt "$MIN_LINES" ] && exit 0

# すでにVaultへ保存した／取り込んだセッションなら促さない
if grep -qE '"(vault-save|vault-ingest|vault-research)"' "$tpath" 2>/dev/null; then
  exit 0
fi

cat <<'JSON'
{
  "decision": "block",
  "reason": "このセッションを終える前に一度だけ確認する。この会話に、将来の別のセッションでも再利用できる知見があるか棚卸しせよ。対象は AGENTS.md の vault-save スコープに該当するもの、すなわち Decision（理由付きの決定）、Reusable learning（今回限りでない学び）、New concept、Project state、Open question、Important constraint である。一時的な会話・単なる途中経過・ツールのログ・会話の全文は対象外。該当するものが無ければ「保存に値するものはない」と一行で述べて終了してよい。該当するものがあれば、何を保存する候補とするかを箇条書きで簡潔に示し、保存してよいか確認せよ。承認を得るまで書き込まない。",
  "systemMessage": "Knowledge Vault: このセッションの知見の棚卸しを促しました（1セッション1回）"
}
JSON
