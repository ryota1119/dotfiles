return {
  'mitch1000/backpack.nvim',
  config = function ()
    require('backpack').setup({
      theme = "dark", -- dark, light, palette
      contrast = "medium", -- medium, high, extreme
    })
  end,
}
