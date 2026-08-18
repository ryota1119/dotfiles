#!/bin/sh
# Codex CLIのMCPサーバーを1Passwordの実値で(再)登録する。
# シークレットのローテーション後や新しいマシンでの初回セットアップ時に実行する。
# `codex mcp add`は同名を渡すと上書きするため、素朴に呼ぶだけで冪等になる。
set -eu

ACCOUNT="my.1password.com"
XAPI_ITEM="X Developer Client Secret"    # 1Password: Personalボルト (個人アカウント)
SOCIALDATA_ITEM="SocialData"              # 1Password: SocialData (Personal)

CLIENT_ID=$(op read "op://Personal/${XAPI_ITEM}/username" --account "$ACCOUNT")
CLIENT_SECRET=$(op read "op://Personal/${XAPI_ITEM}/password" --account "$ACCOUNT")
SOCIALDATA_API_KEY=$(op read "op://Personal/${SOCIALDATA_ITEM}/api_key" --account "$ACCOUNT")

codex mcp add playwright -- npx @playwright/mcp@latest
codex mcp add hn-mcp -- uv run --directory "$HOME/Workspace/repos/github.com/RayLabOrg/hn-mcp" hn-mcp
codex mcp add qiita-mcp -- uv run --directory "$HOME/Workspace/repos/github.com/RayLabOrg/qiita-mcp" qiita-mcp
codex mcp add zenn-mcp -- uv run --directory "$HOME/Workspace/repos/github.com/RayLabOrg/zenn-mcp" zenn-mcp
codex mcp add xapi --env CLIENT_ID="$CLIENT_ID" --env CLIENT_SECRET="$CLIENT_SECRET" \
  -- npx -y @xdevplatform/xurl mcp https://api.x.com/mcp
codex mcp add socialdata-mcp --env SOCIALDATA_API_KEY="$SOCIALDATA_API_KEY" \
  -- uv run --directory "$HOME/Workspace/repos/github.com/RayLabOrg/socialdata-mcp" socialdata-mcp

echo "codex mcp: 6 server(s) registered/updated from 1Password."
