#!/bin/bash

set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-shared-skills.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

skills=(engineering research pm secretary)
for skill in "${skills[@]}"; do
  skill_file="$repo_root/dot_claude/skills/$skill/SKILL.md"

  if grep -Eq 'subagent_type|~/.claude/agents|/effort' "$skill_file"; then
    printf 'Runtime-specific Agent invocation remains in %s\n' "$skill_file" >&2
    exit 1
  fi

  if ! tr '\n' ' ' <"$skill_file" | grep -Eq '専用.*Agent.*利用可能なら委任.*利用できない[[:space:]]*場合.*メインセッション.*直接実行'; then
    printf 'Missing Agent fallback policy in %s\n' "$skill_file" >&2
    exit 1
  fi
done

engineering_skill="$repo_root/dot_claude/skills/engineering/SKILL.md"
for requirement in 'テスト計画' '承認境界' '独立レビュー' '必須の手動確認'; do
  if ! grep -Fq "$requirement" "$engineering_skill"; then
    printf 'Missing engineering safety requirement: %s\n' "$requirement" >&2
    exit 1
  fi
done

worktree_reference="$repo_root/dot_claude/skills/engineering/references/worktree-and-agents.md"
for requirement in '1 agent=1 branch=1 worktree' '承認を得る'; do
  if ! grep -Fq "$requirement" "$worktree_reference"; then
    printf 'Missing worktree safety requirement: %s\n' "$requirement" >&2
    exit 1
  fi
done

if ! grep -Fxq 'tests/' "$repo_root/.chezmoiignore"; then
  printf 'tests/ must remain excluded from chezmoi management\n' >&2
  exit 1
fi

export HOME="$test_root/home"
export XDG_CONFIG_HOME="$test_root/xdg-config"
export OPENCODE_DISABLE_PROJECT_CONFIG=1
mkdir -p "$HOME" "$XDG_CONFIG_HOME"
cp -R "$repo_root/dot_claude" "$HOME/.claude"

skill_output="$test_root/opencode-skills.txt"
opencode debug skill >"$skill_output"
for skill in "${skills[@]}"; do
  if ! grep -Eq "(^|[^[:alnum:]_-])$skill([^[:alnum:]_-]|$)" "$skill_output"; then
    printf 'OpenCode did not discover skill: %s\n' "$skill" >&2
    exit 1
  fi
done

printf '%s\n' 'Shared skills tests passed'
