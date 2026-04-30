return {
  "stevearc/conform.nvim",
  event = { "BufWritePre" },
  cmd = { "ConformInfo" },
  -- <leader>cf は LSP attach 側でフォーマット可能なバッファに対してのみ
  -- 設定する。conform 単独の keys は LSP 非対応の言語でも使えるよう保険として残す。
  keys = {
    {
      "<leader>cF",
      function()
        require("conform").format({ async = true, lsp_fallback = true })
      end,
      mode = { "n", "v" },
      desc = "Format (conform)",
    },
  },
  opts = {
    -- ファイルタイプごとのフォーマッター設定
    formatters_by_ft = {
      lua = { "stylua" },
      python = { "ruff_organize_imports", "ruff_format" },
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
      -- ruff は高速だが、Pythonインタプリタ経由のフォーマッタも考慮して余裕を持たせる
      timeout_ms = 3000,
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
