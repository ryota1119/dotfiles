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
alias dotfiles='cd ~/dotfiles'
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
# tmux
# -----------------------------------------------------------------------------
alias t='tmux'                      # 基本コマンド短縮
alias ta='tmux attach -t'           # セッションにアタッチ
alias tn='tmux new -s'              # 新しいセッション作成
alias tl='tmux ls'                  # セッション一覧
alias tk='tmux kill-session -t'     # セッション終了
alias tks='tmux kill-server'        # サーバごと終了

# iTerm2 統合モード (Control Mode)
alias ti='tmux -CC'                 # 統合モード起動
alias tia='tmux -CC attach -t'      # 統合モードで既存セッションに接続
alias tin='tmux -CC new -A -s'      # 指定セッションに接続 or 作成

# tmux の使い方を表示
alias th='cat << "EOF"
Usage: tmux [command]

セッション管理:
  tmux                      新規セッション開始
  tmux new -s <name>        名前付きセッション作成
  tmux ls                   セッション一覧
  tmux attach -t <name>     セッションに再接続
  tmux kill-session -t      セッション削除

プレフィックスキー: Ctrl-b (デフォルト)

ウィンドウ操作:
  Prefix + c                新規ウィンドウ作成
  Prefix + ,                ウィンドウ名変更
  Prefix + w                ウィンドウ一覧
  Prefix + &                ウィンドウを閉じる
  Shift + Left/Right        前後のウィンドウに移動 (カスタム)

ペイン操作:
  Prefix + |                縦に分割 (カスタム)
  Prefix + -                横に分割 (カスタム)
  Ctrl + h/j/k/l            ペイン間移動 (カスタム)
  Prefix + Shift + arrows   ペインのサイズ変更 (カスタム)
  Prefix + x                ペインを閉じる
  Prefix + z                ペインを最大化/復元

コピーモード (viキーバインド):
  Prefix + [                コピーモード開始
  v                         選択開始
  y                         コピー & 終了
  q                         終了
  Mouse wheel up            自動でコピーモード突入

セッション制御:
  Prefix + d                デタッチ (バックグラウンドで実行継続)
  Prefix + $                セッション名変更
  Prefix + s                セッション一覧を表示
  Prefix + ?                全キーバインド表示
  exit or Ctrl+d            現在のペイン/ウィンドウを終了

マウス操作: 有効
  - クリックでペイン切り替え
  - ドラッグでテキスト選択 & コピー
  - ホイールスクロールで履歴表示

Examples:
  tmux new -s work          "work"という名前でセッション作成
  tmux attach -t work       "work"セッションに再接続
  tmux kill-session -t old  "old"セッションを削除

詳細は "man tmux" または Prefix + ? を参照
EOF
'
