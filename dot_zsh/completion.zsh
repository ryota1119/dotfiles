# =============================================================================
# 補完機能設定
# =============================================================================

# 基本補完設定
autoload -Uz compinit && compinit

# 補完スタイル設定
zstyle ":completion:*:commands" rehash 1
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' group-name ''

# Homebrew補完
if type brew &>/dev/null; then
  FPATH=$(brew --prefix)/share/zsh-completions:$FPATH
  autoload -Uz compinit && compinit
fi

# カスタム補完
autoload -Uz cdr
autoload -Uz zmv
autoload -Uz zcalc
