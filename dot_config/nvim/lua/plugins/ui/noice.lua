return {
  "folke/noice.nvim",
  event = "VeryLazy",
  opts = {
    lsp = {
      -- LSPのhover/signature/markdown表示を Treesitter で整形
      override = {
        ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
        ["vim.lsp.util.stylize_markdown"] = true,
      },
      -- LSPの進捗通知（✔ pyright など）を無効化
      progress = {
        enabled = false,
      },
    },
    presets = {
      bottom_search = true,
      command_palette = true,
      long_message_to_split = true,
      inc_rename = false,
      lsp_doc_border = true,
    },
  },
  dependencies = {
    "MunifTanjim/nui.nvim",
    -- background_colour: 透過100%時の代替色。未指定だと警告が出るためcolorschemeの背景色を明示
    { "rcarriga/nvim-notify", opts = { background_colour = "#0d1117" } },
  },
}