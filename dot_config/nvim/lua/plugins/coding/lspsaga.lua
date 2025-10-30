return {
  "nvimdev/lspsaga.nvim",
  config = function()
      require("lspsaga").setup({
          symbol_in_winbar = {
              separator = "  ",
          },
          lightbulb = {
              virtual_text = true,
              enable = true,
          },
          diagnostic = {
              on_insert = false,
              on_insert_follow = false,
              insert_winblend = 0,
              extend_relatedInformation = true,
              show_code_action = true,
              show_source = true,
              jump_num_shortcut = true,
              max_width = 0.5,
              custom_fix = nil,
              custom_msg = nil,
              text_hl_follow = false,
              border_style = "rounded",
              keys = {
                  exec_action = "o",
                  quit_in_show = { "<ESC>" },
              },
          },
          code_action = {
              num_shortcut = true,
              show_server_name = false,
              extend_gitsigns = true,
              keys = {
                  quit = "<ESC>",
                  exec = "<CR>",
              },
          },
          hover_doc = {
              max_width = 0.5,
              max_height = 0.8,
              border_style = "rounded",
              use_lspsaga_scroll = true,
          },
      })
  end,
  dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "nvim-tree/nvim-web-devicons",
  },
  event = { "BufRead", "BufNewFile" },
}