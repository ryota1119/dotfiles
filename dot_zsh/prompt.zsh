# =============================================================================
# プロンプト設定
# =============================================================================

# プロンプトの基本設定
setopt prompt_subst
setopt transient_rprompt

# プロンプト表示前の処理
add_newline() {
  if [[ -z $PS1_NEWLINE_LOGIN ]]; then
    PS1_NEWLINE_LOGIN=true
  else
    printf '\n'
  fi
}

# プロンプトの設定
precmd() {
  # 現在のディレクトリパスを取得
  local current_dir=$(pwd | sed "s|$HOME|~|")
  
  # Git情報を取得
  local git_info=""
  if git rev-parse --git-dir > /dev/null 2>&1; then
    local branch=$(git branch --show-current 2>/dev/null)
    local git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    
    if [ -n "$branch" ]; then
      if [ "$git_status" -eq 0 ]; then
        git_info="%F{green}($branch)%f"
      else
        git_info="%F{yellow}($branch*)%f"
      fi
    fi
  fi
  
  # プロンプトを構築
  PROMPT="%F{032}%n%f:%F{250}$current_dir%f $git_info"$'\n'"%# "
}

# 右プロンプト（オプション）
RPROMPT="%F{240}%T%f"
