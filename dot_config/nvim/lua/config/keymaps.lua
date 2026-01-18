-- キーマップ設定

local keymap = vim.keymap.set
local opts = { noremap = true, silent = true }

-- リーダーキーは lazy.lua で設定済み（スペース）

-- ノーマルモード
-- より快適な上下移動（表示行単位で移動）
keymap("n", "j", "gj", opts)
keymap("n", "k", "gk", opts)

-- ウィンドウ間の移動
keymap("n", "<C-h>", "<C-w>h", opts)
keymap("n", "<C-j>", "<C-w>j", opts)
keymap("n", "<C-k>", "<C-w>k", opts)
keymap("n", "<C-l>", "<C-w>l", opts)

-- ウィンドウのリサイズ
keymap("n", "<C-Up>", ":resize +2<CR>", opts)
keymap("n", "<C-Down>", ":resize -2<CR>", opts)
keymap("n", "<C-Left>", ":vertical resize -2<CR>", opts)
keymap("n", "<C-Right>", ":vertical resize +2<CR>", opts)

-- バッファ移動
keymap("n", "<S-l>", ":bnext<CR>", opts)
keymap("n", "<S-h>", ":bprevious<CR>", opts)

-- インデント調整
keymap("v", "<", "<gv", opts)
keymap("v", ">", ">gv", opts)

-- 選択したテキストの移動
keymap("v", "J", ":m '>+1<CR>gv=gv", opts)
keymap("v", "K", ":m '<-2<CR>gv=gv", opts)

-- ビジュアルモードでペースト時にヤンクしない
keymap("v", "p", '"_dP', opts)

-- 検索結果のハイライトを消す
keymap("n", "<leader>h", ":nohlsearch<CR>", opts)

-- 保存と終了
keymap("n", "<leader>w", ":w<CR>", opts)
keymap("n", "<leader>q", ":q<CR>", opts)

-- 分割
keymap("n", "<leader>sv", ":vsplit<CR>", opts)
keymap("n", "<leader>sh", ":split<CR>", opts)

-- バッファを閉じる
keymap("n", "<leader>bd", ":bdelete<CR>", opts)
