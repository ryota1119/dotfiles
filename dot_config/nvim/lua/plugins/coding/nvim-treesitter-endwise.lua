return {
  "RRethy/nvim-treesitter-endwise",
  dependencies = { "nvim-treesitter/nvim-treesitter" },
  ft = { "ruby", "eruby" },
  config = function()
    require("nvim-treesitter.configs").setup({ endwise = { enable = true } })
  end,
}