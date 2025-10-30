# =============================================================================
# 環境変数とパス設定
# =============================================================================

# 基本環境変数
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
export EDITOR=vim
export VISUAL=vim
export PAGER=less

# 基本パス設定
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="/usr/local/bin:$PATH"
export PATH="/opt/homebrew/bin:$PATH"

# 履歴設定
export HISTSIZE=10000
export SAVEHIST=10000
export HISTFILE="$HOME/.zsh_history"
setopt hist_ignore_dups
setopt hist_ignore_space
setopt hist_verify
setopt share_history

# 開発環境関連

# Homebrew設定
export HOMEBREW_NO_AUTO_UPDATE=1

# fzf設定
export FZF_DEFAULT_OPTS='--height 40% --reverse --border'
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# direnv
eval "$(direnv hook zsh)"
