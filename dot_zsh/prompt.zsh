# =============================================================================
# プロンプト設定
# =============================================================================

setopt prompt_subst
setopt transient_rprompt

# プロンプト表示前の処理
precmd() {
  # 現在のディレクトリパスを取得
  local current_dir=${PWD/#$HOME/\~}

  # Git情報を取得
  local git_info=""
  if git rev-parse --git-dir > /dev/null 2>&1; then
    local branch=$(git branch --show-current 2>/dev/null)

    if [ -n "$branch" ]; then
      # 1回のgit statusで変更の有無だけ判定（大規模リポジトリでも高速）
      if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
        git_info="%F{green}($branch)%f"
      else
        git_info="%F{yellow}($branch*)%f"
      fi
    fi
  fi

  PROMPT="%F{032}%n%f:%F{250}$current_dir%f $git_info"$'\n'"%# "
}

# 右プロンプト
RPROMPT="%F{240}%T%f"
