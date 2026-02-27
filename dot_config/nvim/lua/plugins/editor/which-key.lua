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
      desc = "Buffer Keymaps (which-key)",
    },
  },
  config = function(_, opts)
    local wk = require("which-key")
    wk.setup(opts)

    -- キーマップグループを定義
    wk.add({
      mode = { "n", "v" },
      { "<leader>b", group = "Buffer" },
      { "<leader>bd", "<cmd>bdelete<cr>", desc = "Buffer delete" },
      { "<leader>c", group = "Code" },
      { "<leader>f", group = "Find" },
      { "<leader>g", group = "Git" },
      { "<leader>s", group = "Split" },
      { "<leader>t", group = "Toggle" },
      { "<leader>e", group = "Explorer" },
      { "<leader>ee", "<cmd>Neotree toggle<cr>", desc = "Neo-tree toggle" },
      { "<leader>ef", "<cmd>Neotree float<cr>", desc = "Neo-tree float" },
      { "<leader>w", "<cmd>w<cr>", desc = "Save" },
      { "<leader>q", "<cmd>q<cr>", desc = "Quit" },
      { "<leader>h", "<cmd>nohlsearch<cr>", desc = "No Highlight" },
    })
  end,
}