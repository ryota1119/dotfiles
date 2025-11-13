# =============================================================================
# Zsh関数定義
# =============================================================================

# ディレクトリ作成と移動を同時に行う
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# ファイルの内容を表示してから編集
v() {
  if [ -f "$1" ]; then
    cat "$1" | vim -
  else
    vim "$1"
  fi
}

# プロセスをポート番号で検索
port() {
  lsof -i :"$1"
}

# ディレクトリサイズを表示
ds() {
  du -sh "$1" 2>/dev/null | sort -hr
}

# Gitブランチを一覧表示
gb() {
  git branch -a | grep -v "remotes/origin/HEAD" | sed 's/^[* ]*//'
}

# 最近使用したディレクトリに移動
cdr() {
  local dir
  dir=$(cdr -l | sed 's/^[0-9]* *//' | fzf)
  if [ -n "$dir" ]; then
    cd "$dir"
  fi
}

# .sshディレクトリ内のHostエントリをfzfで選択し、選択したホストにSSH接続する
ssh-fzf() {
  local selected_host
  selected_host=$(grep -rh '^Host ' "${HOME}/.ssh/" \
    | grep -v '\*' \
    | sed 's/Host //' \
    | sort \
    | fzf)

  if [ -z "$selected_host" ]; then
    echo "キャンセルされました"
    return
  fi

  echo "Connecting to $selected_host..."
  ssh "$selected_host"
}

# =============================================================================
# gh/ghq/fzf関連関数
# =============================================================================

# ghq管理下のリポジトリ一覧をfzfで選択し、選択したディレクトリに移動する
ghq-cd() {
  local dir
  dir=$(ghq list | fzf --preview 'eza -T --color=always {} | head -200')
  if [ -n "$dir" ]; then
    cd "$(ghq root)/$dir"
  fi
}

# ghq管理下のリポジトリ一覧をfzfで選択し、Cursorで開く
ghq-cursor() {
  local dir
  dir=$(ghq list | fzf --preview 'eza -T --color=always {} | head -200')
  if [ -n "$dir" ]; then
    cursor "$(ghq root)/$dir"
  fi
}

# GitHub上のリポジトリ一覧をfzfで選択し、選択したリポジトリをcloneする
# 1. organizationを選択 → 2. リポジトリを選択 → 3. ghqでcloneして移動
gh-clone-fzf() {
  local org repo user_login
  # Step 1: organizationを選択（ユーザー自身も含む）
  user_login=$(gh api user --jq '.login')
  org=$( (echo "$user_login"; gh api user/orgs --jq '.[].login') | sort | fzf --prompt "Organization: ")
  if [ -z "$org" ]; then
    echo "キャンセルされました"
    return
  fi

  # Step 2: 選択したorganizationのリポジトリ一覧から選択
  repo=$(gh repo list "$org" --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner' | fzf --prompt "Repository: ")
  if [ -z "$repo" ]; then
    echo "キャンセルされました"
    return
  fi

  # Step 3: ghqでcloneして移動
  ghq get "https://github.com/${repo}"
  cd "$(ghq root)/github.com/${repo}"
}

# GitHubリポジトリの説明をプレビューしながらfzfで選択し、選択したリポジトリをcloneする
# 1. organizationを選択 → 2. リポジトリを選択（プレビュー付き） → 3. ghqでcloneして移動
gh-clone-fzf-preview() {
  local org repo user_login
  # Step 1: organizationを選択（ユーザー自身も含む）
  user_login=$(gh api user --jq '.login')
  org=$( (echo "$user_login"; gh api user/orgs --jq '.[].login') | sort | fzf --prompt "Organization: ")
  if [ -z "$org" ]; then
    echo "キャンセルされました"
    return
  fi

  # Step 2: 選択したorganizationのリポジトリ一覧から選択（プレビュー付き）
  repo=$(gh repo list "$org" --limit 1000 --json nameWithOwner,description --jq '.[] | "\(.nameWithOwner)\t\(.description // "No description")"' \
    | fzf --delimiter=$'\t' --with-nth=1 --prompt "Repository: " --preview 'gh repo view {1} --json description,homepageUrl,stargazerCount,updatedAt --jq "\"\(.description // \"No description\")\n\n⭐ Stars: \(.stargazerCount)\n🕒 Updated: \(.updatedAt)\n🌐 Homepage: \(.homepageUrl // \"N/A\")\""' \
    | cut -f1)
  if [ -z "$repo" ]; then
    echo "キャンセルされました"
    return
  fi

  # Step 3: ghqでcloneして移動
  ghq get "https://github.com/${repo}"
  cd "$(ghq root)/github.com/${repo}"
}

# ローカルリポジトリ（ghq）とGitHubリポジトリを統合検索し、ローカルなら開き、リモートならcloneする
ghq-gh-fzf() {
  local repo selected_type
  selected_type=$( (ghq list | sed 's/^/local:/'; gh repo list --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner' | sed 's/^/remote:/') \
    | fzf --delimiter=: --with-nth=2 --preview 'if [[ {1} == "local" ]]; then eza -T --color=always $(ghq root)/{2} | head -200; else gh repo view {2} --json description,stargazerCount --jq "\"\(.description // \"No description\")\n⭐ Stars: \(.stargazerCount)\""; fi' \
    | cut -d':' -f1-2)

  if [ -z "$selected_type" ]; then
    echo "キャンセルされました"
    return
  fi

  repo=$(echo "$selected_type" | cut -d':' -f2)
  local_type=$(echo "$selected_type" | cut -d':' -f1)

  if [ "$local_type" = "local" ]; then
    local local_path
    local_path=$(ghq list -p | grep -E "/${repo}$")
    if [ -n "$local_path" ]; then
      cd "$local_path"
    else
      echo "ローカルリポジトリが見つかりません: $repo"
    fi
  else
    ghq get "https://github.com/${repo}"
    cd "$(ghq root)/github.com/${repo}"
  fi
}

# GitHubのPR一覧をfzfで選択し、ブラウザで開く
gh-pr-fzf() {
  local pr
  pr=$(gh pr list --limit 100 --json number,title,author,state --jq '.[] | "\(.number)\t\(.title)\t\(.author.login)\t\(.state)"' \
    | fzf --delimiter=$'\t' --with-nth=1,2 --preview 'gh pr view {1} --json title,body,state,author,url --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""' \
    | cut -f1)
  [ -n "$pr" ] && gh pr view "$pr" --web
}

# GitHubのIssue一覧をfzfで選択し、ブラウザで開く
gh-issue-fzf() {
  local issue
  issue=$(gh issue list --limit 100 --json number,title,author,state --jq '.[] | "\(.number)\t\(.title)\t\(.author.login)\t\(.state)"' \
    | fzf --delimiter=$'\t' --with-nth=1,2 --preview 'gh issue view {1} --json title,body,state,author,url --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""' \
    | cut -f1)
  [ -n "$issue" ] && gh issue view "$issue" --web
}

# GitHubのPRまたはIssue一覧をfzfで選択し、ブラウザで開く
gh-pr-issue-fzf() {
  local selected
  selected=$( (gh pr list --limit 50 --json number,title,state --jq '.[] | "pr:\(.number)\t\(.title)\t\(.state)"'; \
    gh issue list --limit 50 --json number,title,state --jq '.[] | "issue:\(.number)\t\(.title)\t\(.state)"') \
    | fzf --delimiter=$'\t' --with-nth=1,2 --preview 'if [[ {1} =~ ^pr: ]]; then gh pr view $(echo {1} | cut -d: -f2) --json title,body,state,author --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""; else gh issue view $(echo {1} | cut -d: -f2) --json title,body,state,author --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""; fi' \
    | cut -f1)

  if [ -z "$selected" ]; then
    echo "キャンセルされました"
    return
  fi

  if [[ "$selected" =~ ^pr: ]]; then
    local pr_num=$(echo "$selected" | cut -d: -f2)
    gh pr view "$pr_num" --web
  else
    local issue_num=$(echo "$selected" | cut -d: -f2)
    gh issue view "$issue_num" --web
  fi
}
