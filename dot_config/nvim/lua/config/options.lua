-- Neovim基本オプション設定
local opt = vim.opt

-- 基本設定
opt.number = true
opt.relativenumber = false
opt.mouse = "a"
opt.clipboard = ""

-- インデント設定
opt.expandtab = true
opt.shiftwidth = 2
opt.tabstop = 2
opt.smartindent = true

-- 検索設定
opt.ignorecase = true
opt.smartcase = true
opt.hlsearch = true
opt.incsearch = true

-- UI設定
opt.termguicolors = true
opt.showmode = false
opt.cursorline = true
opt.signcolumn = "yes"
opt.wrap = false
opt.showtabline = 2
opt.hidden = true

-- パフォーマンス設定
opt.updatetime = 300

-- LSP関連のオプション
opt.completeopt = { "menuone", "noinsert", "noselect" }
opt.shortmess:append("c") -- 補完メッセージを短縮 
