return {
  "folke/which-key.nvim",
  event = "VeryLazy",
  opts = {
    preset = "modern",
    delay = 300,
    icons = {
      breadcrumb = "»",
      separator = "➜",
      group = "+",
    },
    win = {
      border = "rounded",
      padding = { 1, 2 },
    },
  },
  keys = {
    {
      "<leader>?",
      function()
        require("which-key").show({ global = false })
      end,
      desc = "Buffer keymaps (which-key)",
    },
  },
  config = function(_, opts)
    local wk = require("which-key")
    wk.setup(opts)

    -- <leader> 配下のグループ名と単発キーを集中管理
    -- 個別の <leader>X 系キーは各プラグインの keys = {} か、
    -- LSP attach 時の vim.keymap.set で desc 付きで登録することで自動的に出る。
    wk.add({
      mode = { "n", "v" },

      -- グループ名
      { "<leader>b", group = "Buffer" },
      { "<leader>c", group = "Code / LSP" },
      { "<leader>f", group = "Find" },
      { "<leader>g", group = "Git" },
      { "<leader>gh", group = "Hunk" },
      { "<leader>s", group = "Split" },
      { "<leader>t", group = "Toggle / Terminal" },

      -- 単発キー
      { "<leader>w", "<cmd>w<cr>", desc = "Save" },
      { "<leader>q", "<cmd>q<cr>", desc = "Quit" },
      { "<leader>h", "<cmd>nohlsearch<cr>", desc = "No highlight" },
      { "<leader>e", vim.diagnostic.open_float, desc = "Diagnostics float" },

      -- Buffer
      { "<leader>bd", "<cmd>bdelete<cr>", desc = "Delete buffer" },
      { "<leader>bn", "<cmd>bnext<cr>", desc = "Next buffer" },
      { "<leader>bp", "<cmd>bprevious<cr>", desc = "Previous buffer" },

      -- Split
      { "<leader>sv", "<cmd>vsplit<cr>", desc = "Vertical split" },
      { "<leader>sh", "<cmd>split<cr>", desc = "Horizontal split" },
      { "<leader>sx", "<C-w>q", desc = "Close split" },
      { "<leader>so", "<C-w>o", desc = "Only window" },
    })
  end,
}
