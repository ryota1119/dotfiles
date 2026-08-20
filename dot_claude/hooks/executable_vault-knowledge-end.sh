#!/bin/sh
# Claude Code の SessionEnd フック。実体は ~/.local/bin/vault-knowledge-end。
#
# Codex 側と同じ処理をするため本体を共有している。ここを薄いラッパーに留めるのは、
# ~/.claude/settings.json（chezmoi管理外の揮発ファイル）に書かれたパスを
# 変えずに済ませるため。
exec "${HOME}/.local/bin/vault-knowledge-end" claude
