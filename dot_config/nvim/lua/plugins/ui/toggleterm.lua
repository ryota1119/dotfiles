return {
  'akinsho/toggleterm.nvim',
  version = "*",
  config = function()
    -- メインの設定
    require("toggleterm").setup({
      -- ターミナルのサイズ
      size = 20,
      -- ターミナルを開く方向
      direction = "horizontal",
      -- ターミナルのシェーディング（他のウィンドウより暗くする）
      shade_terminals = true,
      -- サイズを永続化するか
      persist_size = true,
      -- ターミナルを開く時の処理
      on_open = function(term)
        vim.cmd("startinsert!")
      end,
    })

    -- ============================================================================
    -- ToggleTerm キーマップ
    -- ============================================================================
    -- ターミナルトグル
    vim.keymap.set("n", "<C-\\>", "<cmd>ToggleTerm<CR>", { desc = "Toggle terminal" })
    
    -- ターミナルモードでの操作
    vim.keymap.set("t", "<esc>", [[<C-\><C-n>]], { desc = "Exit terminal mode" })
    vim.keymap.set("t", "jk", [[<C-\><C-n>]], { desc = "Exit terminal mode" })
    
    -- ターミナルモードでのウィンドウ移動
    vim.keymap.set("t", "<C-h>", [[<Cmd>wincmd h<CR>]], { desc = "Move to left window" })
    vim.keymap.set("t", "<C-j>", [[<Cmd>wincmd j<CR>]], { desc = "Move to down window" })
    vim.keymap.set("t", "<C-k>", [[<Cmd>wincmd k<CR>]], { desc = "Move to up window" })
    vim.keymap.set("t", "<C-l>", [[<Cmd>wincmd l<CR>]], { desc = "Move to right window" })
    vim.keymap.set("t", "<C-w>", [[<C-\><C-n><C-w>]], { desc = "Window commands" })
  end,
}
