return {
  "catppuccin/nvim",
  name = "catppuccin",
  priority = 1000,
  config = function()
    require("catppuccin").setup({
      flavour = "mocha",
      integrations = {
        blink_cmp = true,
        bufferline = true,
        gitsigns = true,
        noice = true,
        telescope = { enabled = true },
        treesitter = true,
        which_key = true,
      },
    })
    vim.cmd.colorscheme("catppuccin")
  end,
}
