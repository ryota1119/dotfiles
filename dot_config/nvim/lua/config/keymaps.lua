-- グローバルキーマップ
-- リーダーキー (<leader>) のマップは which-key.lua および各プラグインの
-- keys = {} で集中管理する。ここではリーダー以外の汎用キーのみ定義する。

local map = vim.keymap.set
local opts = { noremap = true, silent = true }

-- 表示行単位の上下移動
map("n", "j", "gj", opts)
map("n", "k", "gk", opts)

-- ウィンドウ間の移動
map("n", "<C-h>", "<C-w>h", opts)
map("n", "<C-j>", "<C-w>j", opts)
map("n", "<C-k>", "<C-w>k", opts)
map("n", "<C-l>", "<C-w>l", opts)

-- ウィンドウのリサイズ
map("n", "<C-Up>", ":resize +2<CR>", opts)
map("n", "<C-Down>", ":resize -2<CR>", opts)
map("n", "<C-Left>", ":vertical resize -2<CR>", opts)
map("n", "<C-Right>", ":vertical resize +2<CR>", opts)

-- バッファ移動
map("n", "<S-l>", ":bnext<CR>", { noremap = true, silent = true, desc = "Next buffer" })
map("n", "<S-h>", ":bprevious<CR>", { noremap = true, silent = true, desc = "Previous buffer" })

-- ビジュアルでインデントを保持
map("v", "<", "<gv", opts)
map("v", ">", ">gv", opts)

-- ビジュアルで行を移動
map("v", "J", ":m '>+1<CR>gv=gv", opts)
map("v", "K", ":m '<-2<CR>gv=gv", opts)

-- ビジュアルのペーストでヤンクしない
map("v", "p", '"_dP', opts)

-- ESC で検索ハイライト解除（<leader>h と二重で持つ）
map("n", "<Esc>", "<cmd>nohlsearch<CR>", opts)
