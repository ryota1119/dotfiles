return {
  "stevearc/conform.nvim",
  event = { "BufWritePre" },
  cmd = { "ConformInfo" },
  keys = {
    {
      "<leader>cf",
      function()
        require("conform").format({ async = true, lsp_fallback = true })
      end,
      mode = { "n", "v" },
      desc = "Format buffer",
    },
  },
  opts = {
    -- ファイルタイプごとのフォーマッター設定
    formatters_by_ft = {
      lua = { "stylua" },
      python = { "isort", "black" },
      javascript = { "prettier" },
      typescript = { "prettier" },
      javascriptreact = { "prettier" },
      typescriptreact = { "prettier" },
      vue = { "prettier" },
      css = { "prettier" },
      scss = { "prettier" },
      html = { "prettier" },
      json = { "prettier" },
      jsonc = { "prettier" },
      yaml = { "prettier" },
      markdown = { "prettier" },
      ruby = { "rubocop" },
      go = { "goimports", "gofmt" },
      rust = { "rustfmt" },
      sh = { "shfmt" },
      terraform = { "terraform_fmt" },
      ["terraform-vars"] = { "terraform_fmt" },
    },

    -- 保存時に自動フォーマット
    format_on_save = {
      -- タイムアウト時間（ミリ秒）
      timeout_ms = 500,
      -- LSPフォーマッターにフォールバック
      lsp_fallback = true,
    },

    -- フォーマッター設定のカスタマイズ
    formatters = {
      shfmt = {
        prepend_args = { "-i", "2" },
      },
    },
  },
  init = function()
    -- formatexprを設定して gq でフォーマット可能にする
    vim.o.formatexpr = "v:lua.require'conform'.formatexpr()"
  end,
}
