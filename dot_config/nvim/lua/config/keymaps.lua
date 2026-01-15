-- ============================================================================
-- グローバルキーマップ設定
-- ============================================================================
-- このファイルには、プラグインに依存しない基本的なVim/Neovim操作のみを記述します。
-- プラグイン固有のkeymapは各プラグインファイル内で定義してください。
-- ============================================================================

-- 共通オプション
local opts = { noremap = true, silent = true }

-- ----------------------------------------------------------------------------
-- 基本操作
-- ----------------------------------------------------------------------------
vim.keymap.set("n", "<leader>w", "<cmd>w<cr>", vim.tbl_extend("force", opts, { desc = "Save file" }))
vim.keymap.set("n", "<leader>q", "<cmd>q<cr>", vim.tbl_extend("force", opts, { desc = "Quit window" }))
vim.keymap.set("n", "<leader>Q", "<cmd>qa!<cr>", vim.tbl_extend("force", opts, { desc = "Quit all (force)" }))

-- バッファ操作
vim.keymap.set("n", "<leader>bd", "<cmd>bd<cr>", vim.tbl_extend("force", opts, { desc = "Delete buffer" }))
vim.keymap.set("n", "<leader>ba", "<cmd>%bd|e#<cr>", vim.tbl_extend("force", opts, { desc = "Delete all buffers except current" }))

-- ウィンドウ分割
vim.keymap.set("n", "<leader>-", "<C-w>s", vim.tbl_extend("force", opts, { desc = "Split window horizontally" }))
vim.keymap.set("n", "<leader>|", "<C-w>v", vim.tbl_extend("force", opts, { desc = "Split window vertically" }))

-- ウィンドウ間移動（矢印キー）
vim.keymap.set("n", "<C-h>", "<C-w>h", vim.tbl_extend("force", opts, { desc = "Move to left window" }))
vim.keymap.set("n", "<C-j>", "<C-w>j", vim.tbl_extend("force", opts, { desc = "Move to below window" }))
vim.keymap.set("n", "<C-k>", "<C-w>k", vim.tbl_extend("force", opts, { desc = "Move to above window" }))
vim.keymap.set("n", "<C-l>", "<C-w>l", vim.tbl_extend("force", opts, { desc = "Move to right window" }))

-- ウィンドウリサイズ
vim.keymap.set("n", "<C-Up>", "<cmd>resize +2<cr>", vim.tbl_extend("force", opts, { desc = "Increase window height" }))
vim.keymap.set("n", "<C-Down>", "<cmd>resize -2<cr>", vim.tbl_extend("force", opts, { desc = "Decrease window height" }))
vim.keymap.set("n", "<C-Left>", "<cmd>vertical resize -2<cr>", vim.tbl_extend("force", opts, { desc = "Decrease window width" }))
vim.keymap.set("n", "<C-Right>", "<cmd>vertical resize +2<cr>", vim.tbl_extend("force", opts, { desc = "Increase window width" }))

-- ----------------------------------------------------------------------------
-- 検索
-- ----------------------------------------------------------------------------
vim.keymap.set("n", "n", "nzzzv", vim.tbl_extend("force", opts, { desc = "Next search result (centered)" }))
vim.keymap.set("n", "N", "Nzzzv", vim.tbl_extend("force", opts, { desc = "Previous search result (centered)" }))
vim.keymap.set("n", "*", "*zzzv", vim.tbl_extend("force", opts, { desc = "Search word under cursor (centered)" }))
vim.keymap.set("n", "#", "#zzzv", vim.tbl_extend("force", opts, { desc = "Search word under cursor backward (centered)" }))
vim.keymap.set("n", "<leader>/", "<cmd>nohlsearch<cr>", vim.tbl_extend("force", opts, { desc = "Clear search highlight" }))

-- ----------------------------------------------------------------------------
-- 編集
-- ----------------------------------------------------------------------------
-- Visualモードで選択範囲を移動
vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv", vim.tbl_extend("force", opts, { desc = "Move selection down" }))
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv", vim.tbl_extend("force", opts, { desc = "Move selection up" }))

-- インデント調整後も選択を維持
vim.keymap.set("v", "<", "<gv", vim.tbl_extend("force", opts, { desc = "Indent left" }))
vim.keymap.set("v", ">", ">gv", vim.tbl_extend("force", opts, { desc = "Indent right" }))

-- 行の結合時にカーソル位置を維持
vim.keymap.set("n", "J", "mzJ`z", vim.tbl_extend("force", opts, { desc = "Join lines" }))

-- ----------------------------------------------------------------------------
-- システムクリップボード連携
-- ----------------------------------------------------------------------------
-- yank系は常にシステムクリップボード
vim.keymap.set({ "n", "x" }, "y", '"+y', vim.tbl_extend("force", opts, { desc = "Yank to system clipboard" }))
vim.keymap.set("n", "Y", '"+y$', vim.tbl_extend("force", opts, { desc = "Yank to end of line (system clipboard)" }))

-- paste系も常にシステムクリップボード
vim.keymap.set({ "n", "x" }, "p", '"+p', vim.tbl_extend("force", opts, { desc = "Paste from system clipboard" }))
vim.keymap.set({ "n", "x" }, "P", '"+P', vim.tbl_extend("force", opts, { desc = "Paste before cursor (system clipboard)" }))

-- Visualモードでペースト時にヤンクレジスタを保持
vim.keymap.set("x", "p", [["_dP]], vim.tbl_extend("force", opts, { desc = "Paste without yanking" }))

-- ----------------------------------------------------------------------------
-- その他
-- ----------------------------------------------------------------------------
-- Escapeの代替（jk または kj）
vim.keymap.set("i", "jk", "<Esc>", vim.tbl_extend("force", opts, { desc = "Exit insert mode" }))
vim.keymap.set("i", "kj", "<Esc>", vim.tbl_extend("force", opts, { desc = "Exit insert mode" }))

-- 行頭・行末への移動
vim.keymap.set({ "n", "v" }, "H", "^", vim.tbl_extend("force", opts, { desc = "Go to beginning of line" }))
vim.keymap.set({ "n", "v" }, "L", "$", vim.tbl_extend("force", opts, { desc = "Go to end of line" }))

-- ページ移動時にカーソルを中央に
vim.keymap.set("n", "<C-d>", "<C-d>zz", vim.tbl_extend("force", opts, { desc = "Scroll down (centered)" }))
vim.keymap.set("n", "<C-u>", "<C-u>zz", vim.tbl_extend("force", opts, { desc = "Scroll up (centered)" }))

-- QuickFix list navigation
vim.keymap.set("n", "[q", "<cmd>cprev<cr>", vim.tbl_extend("force", opts, { desc = "Previous quickfix" }))
vim.keymap.set("n", "]q", "<cmd>cnext<cr>", vim.tbl_extend("force", opts, { desc = "Next quickfix" }))

-- Location list navigation
vim.keymap.set("n", "[l", "<cmd>lprev<cr>", vim.tbl_extend("force", opts, { desc = "Previous location" }))
vim.keymap.set("n", "]l", "<cmd>lnext<cr>", vim.tbl_extend("force", opts, { desc = "Next location" }))
