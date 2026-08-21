#!/bin/bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
lock_bin="$repo_root/dot_local/bin/executable_vault-lock"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-vault-lock.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

export VAULT_LOCK_DIR="$test_root/write.lock"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok: %s\n' "$1"; }

# 1. 空いているときは取得できる
"$lock_bin" acquire --timeout 2 || fail "空きロックを取得できなかった"
[ -d "$VAULT_LOCK_DIR" ] || fail "ロックディレクトリが作られていない"
[ -f "$VAULT_LOCK_DIR/pid" ] || fail "pidファイルが作られていない"
[ "$(cat "$VAULT_LOCK_DIR/pid")" = "$$" ] || fail "pidファイルの中身が呼び出し元PIDでない"
ok "空きロックを取得できる"

# 2. release で解放される
"$lock_bin" release || fail "releaseが非0で終了した"
[ -d "$VAULT_LOCK_DIR" ] && fail "releaseしてもロックが残っている"
ok "releaseで解放される"

# 3. release は冪等（持っていなくても成功する）
"$lock_bin" release || fail "未保持でのreleaseが非0で終了した"
ok "releaseは冪等"

# 4. 生きているプロセスが持っている間は取得できず、タイムアウトで exit 1
sleep 60 &
live_pid=$!
mkdir -p "$VAULT_LOCK_DIR"
printf '%s\n' "$live_pid" > "$VAULT_LOCK_DIR/pid"
start=$(date +%s)
if "$lock_bin" acquire --timeout 2; then
  kill "$live_pid" 2>/dev/null || true
  fail "生存プロセスが保持中なのに取得できてしまった"
fi
elapsed=$(( $(date +%s) - start ))
kill "$live_pid" 2>/dev/null || true
[ "$elapsed" -ge 2 ] || fail "タイムアウトまで待っていない（${elapsed}秒で戻った）"
rm -rf "$VAULT_LOCK_DIR"
ok "保持中はタイムアウトまで待って exit 1"

# 5. 死んだPIDのロックは奪う
mkdir -p "$VAULT_LOCK_DIR"
sh -c 'exit 0' & dead_pid=$!
wait "$dead_pid" 2>/dev/null || true
printf '%s\n' "$dead_pid" > "$VAULT_LOCK_DIR/pid"
"$lock_bin" acquire --timeout 2 || fail "残骸ロックを奪えなかった"
[ "$(cat "$VAULT_LOCK_DIR/pid")" = "$$" ] || fail "奪った後のpidが自分でない"
"$lock_bin" release
ok "死んだPIDのロックを奪う"

# 6. pidファイルが壊れていても奪える
mkdir -p "$VAULT_LOCK_DIR"
printf 'not-a-pid\n' > "$VAULT_LOCK_DIR/pid"
"$lock_bin" acquire --timeout 2 || fail "壊れたpidファイルのロックを奪えなかった"
"$lock_bin" release
ok "壊れたpidファイルでも奪える"

# 7. pidファイルが無いディレクトリだけのロックも奪える
mkdir -p "$VAULT_LOCK_DIR"
"$lock_bin" acquire --timeout 2 || fail "pidファイルの無いロックを奪えなかった"
"$lock_bin" release
ok "pidファイルの無いロックも奪える"

# 8. 未知のサブコマンドは exit 64
if "$lock_bin" bogus 2>/dev/null; then
  fail "未知のサブコマンドが成功してしまった"
fi
ok "未知のサブコマンドを拒否する"

printf '\nすべて通過\n'
