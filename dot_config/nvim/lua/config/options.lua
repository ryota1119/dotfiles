-- エディタの基本設定

local opt = vim.opt

-- 文字コード
opt.encoding = "utf-8"
opt.fileencoding = "utf-8"

-- 行番号
opt.number = true          -- 行番号を表示
opt.relativenumber = false -- 相対行番号を表示

-- インデント
opt.tabstop = 2       -- タブ文字の幅
opt.shiftwidth = 2    -- インデントの幅
opt.expandtab = true  -- タブをスペースに変換
opt.smartindent = true -- スマートインデント
opt.autoindent = true  -- 自動インデント

-- 検索
opt.ignorecase = true -- 検索時に大文字小文字を区別しない
opt.smartcase = true  -- 大文字が含まれる場合は区別する
opt.hlsearch = true   -- 検索結果をハイライト
opt.incsearch = true  -- インクリメンタル検索

-- 表示
opt.wrap = false          -- 行の折り返しを無効化
opt.scrolloff = 8         -- スクロール時の余白行数
opt.sidescrolloff = 8     -- 横スクロール時の余白
opt.signcolumn = "yes"    -- サインカラムを常に表示
-- opt.colorcolumn = "80"    -- 80文字目にラインを表示
opt.cursorline = true     -- カーソル行をハイライト
opt.termguicolors = true  -- True Colorを有効化

-- ファイル
opt.backup = false        -- バックアップファイルを作成しない
opt.writebackup = false   -- 書き込み前のバックアップを作成しない
opt.swapfile = false      -- スワップファイルを作成しない
opt.undofile = true       -- アンドゥファイルを作成

-- UI
opt.showmode = false      -- モード表示を無効化（ステータスラインで表示）
opt.showcmd = true        -- コマンドを表示
opt.cmdheight = 1         -- コマンドラインの高さ
opt.laststatus = 3        -- グローバルステータスライン
opt.splitright = true     -- 垂直分割時に右に開く
opt.splitbelow = true     -- 水平分割時に下に開く

-- 補完
opt.completeopt = "menu,menuone,noselect" -- 補完メニューの設定

-- マウス
opt.mouse = "a"           -- すべてのモードでマウスを有効化

-- クリップボード
opt.clipboard = "unnamedplus" -- システムクリップボードと連携

-- 更新時間
opt.updatetime = 250      -- スワップファイルの書き込み間隔（ms）
opt.timeoutlen = 300      -- キーマップのタイムアウト時間（ms）

-- その他
opt.hidden = true         -- 保存せずにバッファを切り替え可能
opt.iskeyword:append("-") -- ハイフンを単語の一部として扱う
