#!/bin/sh
# Claude CodeのMCPサーバーを1Passwordの実値で(再)登録する。
# シークレットのローテーション後や新しいマシンでの初回セットアップ時に実行する。
set -eu

ACCOUNT="my.1password.com"
XAPI_ITEM="yqraaqfomzo7uvfjlyy5zvemfa"    # 1Password: X Developer クライアントシークレット (Personal)
XSERVER_ITEM="Xserver"                    # 1Password: Xserver (Development, 案件固有のため)
SHINO_MUSIC_SCHOOL_DIR="$HOME/Workspace/repos/github.com/ray-on-code/shino_music_school"

CLIENT_ID=$(op read "op://Personal/${XAPI_ITEM}/username" --account "$ACCOUNT")
CLIENT_SECRET=$(op read "op://Personal/${XAPI_ITEM}/password" --account "$ACCOUNT")

# xapi: userスコープ(全プロジェクト共通)
claude mcp remove xapi -s user >/dev/null 2>&1 || true
claude mcp add xapi -s user -e CLIENT_ID="$CLIENT_ID" -e CLIENT_SECRET="$CLIENT_SECRET" \
  -- npx -y @xdevplatform/xurl mcp https://api.x.com/mcp

echo "claude mcp: xapi (user scope) registered/updated from 1Password."

# xserver: shino_music_school案件固有、localスコープ(そのプロジェクトのcwdで実行する必要がある)
if [ -d "$SHINO_MUSIC_SCHOOL_DIR" ]; then
  XSERVER_API_KEY=$(op read "op://Development/${XSERVER_ITEM}/api_key" --account "$ACCOUNT")
  XSERVER_SERVERNAME=$(op read "op://Development/${XSERVER_ITEM}/servername" --account "$ACCOUNT")
  (
    cd "$SHINO_MUSIC_SCHOOL_DIR"
    claude mcp remove xserver -s local >/dev/null 2>&1 || true
    claude mcp add xserver -s local \
      -e XSERVER_API_KEY="$XSERVER_API_KEY" -e XSERVER_SERVERNAME="$XSERVER_SERVERNAME" \
      -- npx -y xserver-mcp
  )
  echo "claude mcp: xserver (local scope, shino_music_school) registered/updated from 1Password."
else
  echo "skip: $SHINO_MUSIC_SCHOOL_DIR が存在しないため xserver は登録しなかった" >&2
fi
