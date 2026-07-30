# =============================================================================
# Zshエイリアス定義
# =============================================================================

# -----------------------------------------------------------------------------
# ls / ディレクトリ移動
# -----------------------------------------------------------------------------
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# -----------------------------------------------------------------------------
# 安全なファイル操作
# -----------------------------------------------------------------------------
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias md='mkdir -p'
alias rd='rmdir'

# -----------------------------------------------------------------------------
# 検索・差分（カラー化）
# -----------------------------------------------------------------------------
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias diff='diff --color=auto'

# -----------------------------------------------------------------------------
# システム情報
# -----------------------------------------------------------------------------
alias df='df -h'
alias du='du -h'
alias myip='curl -s https://ipinfo.io/ip'
alias ports='lsof -iTCP -sTCP:LISTEN -n -P'   # macOSでLISTENポートを確認

# -----------------------------------------------------------------------------
# 開発ツール
# -----------------------------------------------------------------------------
alias py='python3'
alias pip='pip3'

# -----------------------------------------------------------------------------
# 小ユーティリティ
# -----------------------------------------------------------------------------
alias reload='source ~/.zshrc'
alias path='echo -e ${PATH//:/\\n}'
alias now='date +"%T"'
alias week='date +%V'
alias timer='echo "Timer started. Stop with Ctrl-D." && date && time cat && date'

# -----------------------------------------------------------------------------
# Git
# -----------------------------------------------------------------------------
alias g='git'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph'
alias gs='git status'
alias gd='git diff'

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
alias d='docker'
alias dc='docker compose'
alias dcps='docker compose ps'
alias dcud='docker compose up -d'
alias dcudb='docker compose up -d --build'
alias dce='docker compose exec'
alias dcl='docker compose logs'
alias dcd='docker compose down'
alias dcbnc='docker compose build --no-cache'

# -----------------------------------------------------------------------------
# cmux
# -----------------------------------------------------------------------------
alias cmclaude='cmux claude-teams'
alias cmcodex='cmux codex-teams'
alias cmomo='cmux omo'
alias cmomx='cmux omx'
alias cmomc='cmux omc'
alias cmopen='cmux open'
alias cmreload='cmux reload-config'
alias cmrestore='cmux restore-session'

