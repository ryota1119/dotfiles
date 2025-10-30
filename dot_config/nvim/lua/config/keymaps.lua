-- ============================================================================
-- グローバルキーマップ設定
-- ============================================================================
-- このファイルには、プラグインに依存しない基本的なVim/Neovim操作のみを記述します。
-- プラグイン固有のkeymapは各プラグインファイル内で定義してください。
-- ============================================================================

-- 共通オプション
local map, opts = vim.keymap.set, { noremap = true, silent = true }

-- ----------------------------------------------------------------------------
-- 基本操作
-- ----------------------------------------------------------------------------
map("n", "<leader>w", "<cmd>w<cr>", { noremap = true, silent = true, desc = "Save file" })
map("n", "<leader>q", "<cmd>q<cr>", { noremap = true, silent = true, desc = "Quit window" })
map("n", "<leader>Q", "<cmd>qa!<cr>", { noremap = true, silent = true, desc = "Quit all (force)" })

-- ----------------------------------------------------------------------------
-- 検索
-- ----------------------------------------------------------------------------
map("n", "n", "nzzzv", { noremap = true, silent = true, desc = "Next search result (centered)" })
map("n", "N", "Nzzzv", { noremap = true, silent = true, desc = "Previous search result (centered)" })
map("n", "*", "*zzzv", { noremap = true, silent = true, desc = "Search word under cursor (centered)" })
map("n", "#", "#zzzv", { noremap = true, silent = true, desc = "Search word under cursor backward (centered)" })
map("n", "<leader>h", "<cmd>nohlsearch<cr>", { noremap = true, silent = true, desc = "Clear search highlight" })

-- ----------------------------------------------------------------------------
-- 編集
-- ----------------------------------------------------------------------------
-- Visualモードで選択範囲を移動
map("v", "<A-Up>", ":m '<-2<CR>gv=gv", { desc = "Move selection up" })
map("v", "<A-Down>", ":m '>+1<CR>gv=gv", { desc = "Move selection down" })

-- ----------------------------------------------------------------------------
-- システムクリップボード連携
-- ----------------------------------------------------------------------------
-- yank系は常にシステムクリップボード
vim.keymap.set({ "n", "x" }, "y", '"+y', { noremap = true, silent = true, desc = "Yank to system clipboard" })
vim.keymap.set("n", "Y", '"+y$', { noremap = true, silent = true, desc = "Yank to end of line (system clipboard)" })

-- paste系も常にシステムクリップボード
vim.keymap.set({ "n", "x" }, "p", '"+p', { noremap = true, silent = true, desc = "Paste from system clipboard" })
vim.keymap.set({ "n", "x" }, "P", '"+P', { noremap = true, silent = true, desc = "Paste before cursor (system clipboard)" })

-- ----------------------------------------------------------------------------
-- LSP（プラグイン依存の設定はlua/lsp/init.luaに記述）
-- ----------------------------------------------------------------------------
-- LSP補完の手動トリガー（Ctrl+Space）
vim.keymap.set('i', '<C-Space>', function()
  vim.lsp.completion.get()
end, { desc = "LSP completion" })
