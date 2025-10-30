return {
  "stevearc/conform.nvim",
  event = { "BufReadPre", "BufNewFile" },
  opts = {
    -- 外部フォーマッタを使いたい言語だけ列挙
    formatters_by_ft = {
      lua = { "stylua" },
      -- JS/TS は Prettier 優先（LSP では整えない）
      html = { "prettier" },
      css = { "prettier" },
      scss = { "prettier" },
      sass = { "prettier" },
      javascript = { "prettier" },
      javascriptreact = { "prettier" },
      typescript = { "prettier" },
      typescriptreact = { "prettier" },
      json = { "prettier" },
      yaml = { "prettier" },
      yml = { "prettier" },
      markdown = { "prettier" },

      -- シェル
      sh = { "shfmt" },
      -- php
      php = { "php_cs_fixer" },
      -- go
      go = { "gofumpt" },
      -- -- ruby
      -- ruby = { "rubocop" },
      -- -- erb
      -- eruby = { "erb_lint" },
      -- ["html.erb"] = { "erb_lint" },

      -- LSP フォーマットにフォールバック
      -- python
      -- python = { "black" },
    },

    -- 保存時の自動フォーマット（外部なければLSPを使う）
    format_on_save = function(bufnr)
      -- 大きすぎるファイルを避けたい場合などはここで条件分岐も可能
      return { timeout_ms = 5000, lsp_fallback = true }
    end,
  },
}
