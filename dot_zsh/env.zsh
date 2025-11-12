# fzf設定
export FZF_DEFAULT_OPTS='--height 40% --reverse --border'
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# asdf init
if [ -f "$HOME/.asdf/asdf.sh" ]; then
  . "$HOME/.asdf/asdf.sh"
fi

