return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  config = function()
    local configs = require("nvim-treesitter.configs")

    configs.setup({
      ensure_installed = {
        "javascript",
        "typescript",
        "tsx",
        "json", "html",
        "css",
        "go",
        "lua",
        "luadoc",
        "luap",
        "ruby",
      },
      incremental_selection = {
        enable = true,
        keymaps = {
          init_selection = "<CR>",
          node_incremental = "<CR>",
          scope_incremental = "<TAB>",
          node_decremental = "<S-CR>",
        },
      },
      sync_install = false,
      highlight = { enable = true },
      indent = { enable = true },
    })

    -- Treesitter関連のキーマップ
    vim.keymap.set("n", "<leader>ts", "<cmd>TSUpdate<cr>", { desc = "Treesitter Update" })
    vim.keymap.set("n", "<leader>th", "<cmd>TSBufToggle highlight<cr>", { desc = "Treesitter Toggle Highlight" })
  end,
}
