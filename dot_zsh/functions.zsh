# =============================================================================
# Zsh関数定義
# =============================================================================

# -----------------------------------------------------------------------------
# 基本ユーティリティ
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Git
# -----------------------------------------------------------------------------

# Gitブランチを一覧表示
gb() {
  git branch -a | grep -v "remotes/origin/HEAD" | sed 's/^[* ]*//'
}

# -----------------------------------------------------------------------------
# fzf 連携
# -----------------------------------------------------------------------------

# 最近使用したディレクトリに fzf で移動
# NOTE: zsh 組み込みの `cdr` と同名になるため、呼び出しは `builtin` 経由にする
fcdr() {
  local dir
  dir=$(cdr -l | sed 's/^[0-9]* *//' | fzf)
  if [ -n "$dir" ]; then
    cd "$dir"
  fi
}

# .ssh/config の Host エントリを fzf で選択して SSH 接続
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

# -----------------------------------------------------------------------------
# gh / ghq / fzf 連携
# -----------------------------------------------------------------------------

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

# GitHub 上のリポジトリ一覧を fzf で選択し、選択したリポジトリを clone する
# 1. organizationを選択 → 2. リポジトリを選択 → 3. ghqでcloneして移動
gh-clone-fzf() {
  local org repo user_login
  user_login=$(gh api user --jq '.login')
  org=$( (echo "$user_login"; gh api user/orgs --jq '.[].login') | sort | fzf --prompt "Organization: ")
  if [ -z "$org" ]; then
    echo "キャンセルされました"
    return
  fi

  repo=$(gh repo list "$org" --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner' | fzf --prompt "Repository: ")
  if [ -z "$repo" ]; then
    echo "キャンセルされました"
    return
  fi

  ghq get "https://github.com/${repo}"
  cd "$(ghq root)/github.com/${repo}"
}

# 説明プレビュー付きで GitHub リポジトリを fzf 選択して clone する
gh-clone-fzf-preview() {
  local org repo user_login
  user_login=$(gh api user --jq '.login')
  org=$( (echo "$user_login"; gh api user/orgs --jq '.[].login') | sort | fzf --prompt "Organization: ")
  if [ -z "$org" ]; then
    echo "キャンセルされました"
    return
  fi

  repo=$(gh repo list "$org" --limit 1000 --json nameWithOwner,description --jq '.[] | "\(.nameWithOwner)\t\(.description // "No description")"' \
    | fzf --delimiter=$'\t' --with-nth=1 --prompt "Repository: " --preview 'gh repo view {1} --json description,homepageUrl,stargazerCount,updatedAt --jq "\"\(.description // \"No description\")\n\n⭐ Stars: \(.stargazerCount)\n🕒 Updated: \(.updatedAt)\n🌐 Homepage: \(.homepageUrl // \"N/A\")\""' \
    | cut -f1)
  if [ -z "$repo" ]; then
    echo "キャンセルされました"
    return
  fi

  ghq get "https://github.com/${repo}"
  cd "$(ghq root)/github.com/${repo}"
}

# ローカル(ghq) と GitHub のリポジトリを統合検索し、ローカルなら開き、リモートなら clone する
ghq-gh-fzf() {
  local repo selected_type local_type
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

# GitHub の PR 一覧を fzf で選択してブラウザで開く
gh-pr-fzf() {
  local pr
  pr=$(gh pr list --limit 100 --json number,title,author,state --jq '.[] | "\(.number)\t\(.title)\t\(.author.login)\t\(.state)"' \
    | fzf --delimiter=$'\t' --with-nth=1,2 --preview 'gh pr view {1} --json title,body,state,author,url --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""' \
    | cut -f1)
  [ -n "$pr" ] && gh pr view "$pr" --web
}

# GitHub の Issue 一覧を fzf で選択してブラウザで開く
gh-issue-fzf() {
  local issue
  issue=$(gh issue list --limit 100 --json number,title,author,state --jq '.[] | "\(.number)\t\(.title)\t\(.author.login)\t\(.state)"' \
    | fzf --delimiter=$'\t' --with-nth=1,2 --preview 'gh issue view {1} --json title,body,state,author,url --jq "\"\(.title)\n\n\(.body // \"No description\")\n\n👤 Author: \(.author.login)\n📊 State: \(.state)\""' \
    | cut -f1)
  [ -n "$issue" ] && gh issue view "$issue" --web
}

# GitHub の PR または Issue を一覧から fzf で選択してブラウザで開く
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
    gh pr view "$(echo "$selected" | cut -d: -f2)" --web
  else
    gh issue view "$(echo "$selected" | cut -d: -f2)" --web
  fi
}

# -----------------------------------------------------------------------------
# mise 連携
# -----------------------------------------------------------------------------

# mise で管理できるツールを fzf で選択し、バージョンを選択してインストールする
mise-fzf() {
  local tool version

  tool=$(mise registry | awk '{print $1}' | fzf --prompt "Tool: ")
  if [ -z "$tool" ]; then
    echo "キャンセルされました"
    return
  fi

  echo "バージョン一覧を取得中..."
  version=$(mise ls-remote "$tool" | sort -Vr | fzf --prompt "Version ($tool): ")
  if [ -z "$version" ]; then
    echo "キャンセルされました"
    return
  fi

  echo "Installing $tool@$version..."
  mise install "$tool@$version"
}

# -----------------------------------------------------------------------------
# Neovim / Markdown
# -----------------------------------------------------------------------------

# Markdown ファイルを neovim で開いてプレビューを起動
mdp() {
  if [ $# -eq 0 ]; then
    echo "使い方: mdp <markdown_file>"
    echo "例: mdp README.md"
    return 1
  fi

  local file="$1"

  if [ ! -f "$file" ]; then
    echo "エラー: ファイルが見つかりません: $file"
    return 1
  fi

  if [[ ! "$file" =~ \.(md|markdown)$ ]]; then
    echo "警告: $file はMarkdownファイルではないかもしれません"
  fi

  nvim -c "MarkdownPreview" "$file"
}

# カレントディレクトリ以下の Markdown ファイルを fzf で選択してプレビュー
mdp-fzf() {
  local file

  file=$(find . -type f \( -name "*.md" -o -name "*.markdown" \) 2>/dev/null \
    | sed 's|^\./||' \
    | fzf --prompt "Markdown File: " \
          --preview 'bat --style=numbers --color=always {}' \
          --preview-window=right:60%:wrap)

  if [ -z "$file" ]; then
    echo "キャンセルされました"
    return
  fi

  nvim -c "MarkdownPreview" "$file"
}

# Markdown ファイルを新規作成して neovim で開く
mdnew() {
  local filename="$1"

  if [ -z "$filename" ]; then
    echo "使い方: mdnew <filename>"
    echo "例: mdnew note.md"
    return 1
  fi

  if [[ ! "$filename" =~ \.(md|markdown)$ ]]; then
    filename="${filename}.md"
  fi

  if [ -f "$filename" ]; then
    echo "警告: $filename は既に存在します"
    read -q "REPLY?上書きしますか？ (y/n) "
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      return 0
    fi
  fi

  cat > "$filename" << 'EOF'
# タイトル

## 概要

ここに内容を書く

## セクション1

内容

## セクション2

内容
EOF

  echo "作成しました: $filename"
  nvim -c "MarkdownPreview" "$filename"
}

# -----------------------------------------------------------------------------
# repos ディレクトリ移動
# -----------------------------------------------------------------------------

# ~/Workspace/repos/ 配下のリポジトリへ相対パス指定で移動する
#   例: repos github.com/MediaPlanet/living-flyer-manage
#   引数なしの場合は ~/Workspace/repos/ 直下へ移動する
#   補完: repos<TAB> で配下の移動可能なディレクトリを階層的に表示する
repos() {
  local base="${HOME}/Workspace/repos"

  # 引数なしなら基準ディレクトリへ
  if [ $# -eq 0 ]; then
    cd "$base"
    return
  fi

  # 末尾スラッシュを除去して目的パスを組み立てる
  local target="${base}/${1%/}"

  if [ -d "$target" ]; then
    cd "$target"
  else
    echo "ディレクトリが見つかりません: $target" >&2
    return 1
  fi
}

# repos の補完: ~/Workspace/repos/ を基準にディレクトリのみを階層補完する
#   -J で明示的なグループ名を付けている点が重要。
#   completion.zsh の `zstyle ':completion:*' group-name ''`（全補完を無名グループに集約）と
#   `_files -W`（基準ディレクトリ指定）を併用すると、内部の2パスが無名グループに畳まれて
#   候補が二重表示される。明示グループ名を与えると1グループに統合され重複しなくなる。
_repos() {
  _files -J repos-dirs -W "${HOME}/Workspace/repos" -/
}
compdef _repos repos

# ~/Workspace/ 配下へ相対パス指定で移動する（repos の Workspace ルート版）
#   例: work sandbox/python
#   引数なしの場合は ~/Workspace/ 直下へ移動する
#   補完: work<TAB> で配下の移動可能なディレクトリを階層的に表示する
work() {
  local base="${HOME}/Workspace"

  # 引数なしなら基準ディレクトリへ
  if [ $# -eq 0 ]; then
    cd "$base"
    return
  fi

  # 末尾スラッシュを除去して目的パスを組み立てる
  local target="${base}/${1%/}"

  if [ -d "$target" ]; then
    cd "$target"
  else
    echo "ディレクトリが見つかりません: $target" >&2
    return 1
  fi
}

# work の補完: ~/Workspace/ を基準にディレクトリのみを階層補完する
#   -J で明示的なグループ名を付ける理由は _repos と同じ（group-name '' との併用による二重表示回避）
_work() {
  _files -J work-dirs -W "${HOME}/Workspace" -/
}
compdef _work work

# -----------------------------------------------------------------------------
# Claude Code（OpenRouter バックエンド時のみ有効）
# -----------------------------------------------------------------------------

# ANTHROPIC_AUTH_TOKEN をシェル環境に常駐させず、claude 起動時にだけ 1Password から解決する。
# OP_OPENROUTER_KEY_PATH が未設定のマシン(= 会社マシン)では素通しし、純正の claude をそのまま呼ぶ。
# このため functions.zsh が全マシンへ同期されても、会社マシンの挙動は一切変わらない。
claude() {
  if [ -z "$OP_OPENROUTER_KEY_PATH" ]; then
    command claude "$@"
    return
  fi

  local token
  token=$(op read --account "$OP_ACCOUNT_FOR_AI" "$OP_OPENROUTER_KEY_PATH" 2>/dev/null)
  if [ -z "$token" ]; then
    echo "OpenRouter APIキーを1Passwordから取得できませんでした: $OP_OPENROUTER_KEY_PATH" >&2
    echo "op signin を実行してから再試行してください。" >&2
    return 1
  fi

  ANTHROPIC_AUTH_TOKEN="$token" command claude "$@"
}

# Exocortex など、匿名化済みとはいえ会社由来の知見を扱う作業を
# DeepSeek ではなく Anthropic モデル(OpenRouter 経由)で開始する。
# 注意: これは「DeepSeekに渡さない」だけで、トラフィック自体は OpenRouter を通る。
claude-anthropic() {
  ANTHROPIC_MODEL="~anthropic/claude-sonnet-latest" claude "$@"
}
