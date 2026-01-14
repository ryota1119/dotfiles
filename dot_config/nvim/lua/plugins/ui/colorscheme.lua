return {
  {
    "mitch1000/backpack.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      require("backpack").setup({
        undercurl = false,
        commentStyle = { italic = true },
        compile = false,
        functionStyle = {},
        keywordStyle = { bold = true },
        statementStyle = { bold = true },
        returnStyle = { italic = false, bold = true },
        typeStyle = {},
        transparent = false,
        dimInactive = false,
        terminalColors = true,
        contrast = "medium", -- medium, high, extreme
      })
      -- カラースキームを適用
      vim.cmd("colorscheme backpack")
    end,
  },
}
