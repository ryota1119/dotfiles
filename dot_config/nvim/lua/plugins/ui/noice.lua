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
    "rcarriga/nvim-notify",
  },
}