# fzf設定
export FZF_DEFAULT_OPTS='--height 40% --reverse --border'
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# lazy git
export XDG_CONFIG_HOME="$HOME/.config"

# mise
eval "$(mise activate zsh)"

# bison mise経由でphpをインストールするのに必要
export PATH="/opt/homebrew/opt/bison/bin:$PATH"
