# =============================================================================
# Zshエイリアス定義
# =============================================================================

# 基本コマンド
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# 安全なコマンド
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# ディレクトリ操作
alias md='mkdir -p'
alias rd='rmdir'

# ファイル操作
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias diff='diff --color=auto'
# alias rm='mv2trash'

# Git関連
alias g='git'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph'
alias gs='git status'
alias gd='git diff'

# システム関連
alias df='df -h'
alias du='du -h'
alias free='free -h'

# ネットワーク関連
alias myip='curl -s https://ipinfo.io/ip'
alias ports='netstat -tulanp'

# 開発関連
alias py='python3'
alias pip='pip3'

# カスタムエイリアス
alias dotfiles='cd ~/dotfiles'
alias reload='source ~/.zshrc'
alias path='echo -e ${PATH//:/\\n}'
alias now='date +"%T"'
alias week='date +%V'
alias timer='echo "Timer started. Stop with Ctrl-D." && date && time cat && date'

# Dockerコマンド エイリアス
alias d='docker'
alias dc='docker compose'
alias dcps='docker compose ps'
alias dcud='docker compose up -d'
alias dcudb='docker compose up -d --build'
alias dce='docker compose exec'
alias dcl='docker compose logs'
alias dcd='docker compose down'
alias dcbnc='docker compose build --no-cache'

# --- tmux エイリアス ---
alias t="tmux"                      # 基本コマンド短縮
alias ta="tmux attach -t"           # セッションにアタッチ
alias tn="tmux new -s"              # 新しいセッション作成
alias tl="tmux ls"                  # セッション一覧
alias tk="tmux kill-session -t"     # セッション終了
alias tks="tmux kill-server"        # サーバごと終了

# iTerm2 統合モード用（Control Mode）
alias ti="tmux -CC"                   # 統合モード起動（手動でセッション名指定可）
alias tia="tmux -CC attach -t"        # 統合モードで既存セッションに接続
alias tin="tmux -CC new -A -s"   # mainセッションに統合モードで接続 or 作成
