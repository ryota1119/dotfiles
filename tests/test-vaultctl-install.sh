#!/bin/bash

set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
script_tmpl="$repo_root/.chezmoiscripts/run_onchange_after_20-install-vaultctl.sh.tmpl"

if ! command -v chezmoi >/dev/null 2>&1; then
  printf 'chezmoi コマンドが見つからない\n' >&2
  exit 1
fi

if [ ! -f "$script_tmpl" ]; then
  printf 'vaultctl インストールスクリプトが存在しない: %s\n' "$script_tmpl" >&2
  exit 1
fi

test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-vaultctl-install.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

rendered="$test_root/rendered.sh"
if ! chezmoi execute-template --source "$repo_root" <"$script_tmpl" >"$rendered"; then
  printf 'インストールスクリプトのテンプレートを描画できない: %s\n' "$script_tmpl" >&2
  exit 1
fi

if ! grep -Eq 'uv tool install --force --editable "[^"]+/vaultctl"' "$rendered"; then
  printf 'uv tool install --force --editable <sourceDir>/vaultctl が描画結果に無い\n' >&2
  exit 1
fi

source_copy="$test_root/source"
mkdir -p "$source_copy"
cp -R "$repo_root/." "$source_copy"

probe="$source_copy/vaultctl/src/vaultctl/_digest_probe.py"
mkdir -p "$(dirname -- "$probe")"
printf 'PROBE = 1\n' >"$probe"
digest_before=$(chezmoi execute-template --source "$source_copy" <"$script_tmpl" \
  | grep '^# vaultctl-source-digest: ' | head -n 1)

printf 'PROBE_EXTRA = 2\n' >>"$probe"
digest_after=$(chezmoi execute-template --source "$source_copy" <"$script_tmpl" \
  | grep '^# vaultctl-source-digest: ' | head -n 1)

if [ -z "$digest_before" ]; then
  printf 'digest 行が描画結果に無い\n' >&2
  exit 1
fi

if [ "$digest_before" = "$digest_after" ]; then
  printf 'vaultctl 配下の .py を変更しても digest が変わらない\n' >&2
  exit 1
fi

for ignored in 'vaultctl/' 'worktrees/'; do
  if ! grep -Fxq "$ignored" "$repo_root/.chezmoiignore"; then
    printf '%s must remain excluded from chezmoi management\n' "$ignored" >&2
    exit 1
  fi
done

printf '%s\n' 'vaultctl install script tests passed'
