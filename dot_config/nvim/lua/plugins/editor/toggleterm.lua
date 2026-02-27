return {
  "akinsho/toggleterm.nvim",
  version = "*",
  config = function()
    require("toggleterm").setup({
      -- ターミナルのサイズ（横分割の場合は高さ、縦分割の場合は幅）
      size = function(term)
        if term.direction == "horizontal" then
          return 15
        elseif term.direction == "vertical" then
          return vim.o.columns * 0.4
        end
      end,
      -- ターミナルを開く/閉じるキーマップ
      open_mapping = [[<c-\>]],
      -- 挿入モードでもマッピングを有効化
      insert_mappings = true,
      -- ターミナルモードでもマッピングを有効化
      terminal_mappings = true,
      -- 行番号を非表示
      hide_numbers = true,
      -- ターミナルの背景を暗くする
      shade_terminals = true,
      shading_factor = -30,
      -- 挿入モードで開始
      start_in_insert = true,
      -- サイズを保持
      persist_size = true,
      -- モードを保持
      persist_mode = true,
      -- デフォルトの方向（'vertical' | 'horizontal' | 'tab' | 'float'）
      direction = "float",
      -- プロセス終了時にターミナルウィンドウを閉じる
      close_on_exit = true,
      -- シェルの設定
      shell = vim.o.shell,
      -- 自動スクロール
      auto_scroll = true,
      -- フローティングウィンドウの設定
      float_opts = {
        border = "curved",
        winblend = 3,
      },
      -- winbar設定（Neovim 0.8+）
      winbar = {
        enabled = false,
        name_formatter = function(term)
          return term.name
        end,
      },
    })

    -- ターミナルモードでのキーマップ設定
    function _G.set_terminal_keymaps()
      local opts = { buffer = 0 }
      -- ターミナルモードから抜ける
      vim.keymap.set("t", "<esc>", [[<C-\><C-n>]], opts)
      vim.keymap.set("t", "jk", [[<C-\><C-n>]], opts)
      -- ウィンドウ間の移動
      vim.keymap.set("t", "<C-h>", [[<Cmd>wincmd h<CR>]], opts)
      vim.keymap.set("t", "<C-j>", [[<Cmd>wincmd j<CR>]], opts)
      vim.keymap.set("t", "<C-k>", [[<Cmd>wincmd k<CR>]], opts)
      vim.keymap.set("t", "<C-l>", [[<Cmd>wincmd l<CR>]], opts)
      vim.keymap.set("t", "<C-w>", [[<C-\><C-n><C-w>]], opts)
    end

    -- ターミナルを開いたときに自動的にキーマップを設定
    vim.cmd("autocmd! TermOpen term://*toggleterm#* lua set_terminal_keymaps()")

    -- カスタムターミナルの例: lazygit
    local Terminal = require("toggleterm.terminal").Terminal
    local lazygit = Terminal:new({
      cmd = "lazygit",
      dir = "git_dir",
      direction = "float",
      float_opts = {
        border = "double",
      },
      -- ターミナルを開いたときの処理
      on_open = function(term)
        vim.cmd("startinsert!")
        vim.api.nvim_buf_set_keymap(term.bufnr, "n", "q", "<cmd>close<CR>", { noremap = true, silent = true })
      end,
      -- ターミナルを閉じたときの処理
      on_close = function(term)
        vim.cmd("startinsert!")
      end,
    })

    function _LAZYGIT_TOGGLE()
      lazygit:toggle()
    end

    -- lazygitのキーマップ
    vim.api.nvim_set_keymap("n", "<leader>gg", "<cmd>lua _LAZYGIT_TOGGLE()<CR>", { noremap = true, silent = true, desc = "LazyGit" })

    -- その他の便利なターミナルコマンド
    -- 水平分割ターミナル
    vim.api.nvim_set_keymap("n", "<leader>th", "<cmd>ToggleTerm size=15 direction=horizontal<CR>", { noremap = true, silent = true, desc = "水平分割ターミナル" })
    -- 垂直分割ターミナル
    vim.api.nvim_set_keymap("n", "<leader>tv", "<cmd>ToggleTerm size=80 direction=vertical<CR>", { noremap = true, silent = true, desc = "垂直分割ターミナル" })
    -- フローティングターミナル
    vim.api.nvim_set_keymap("n", "<leader>tf", "<cmd>ToggleTerm direction=float<CR>", { noremap = true, silent = true, desc = "フローティングターミナル" })
  end,
}
