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
    },

    -- 保存時に自動フォーマット
    format_on_save = function(bufnr)
      -- Python は black/isort の起動が重くタイムアウトしやすいので
      -- 同期フォーマットはスキップし、後続の非同期フォーマットで処理する
      if vim.bo[bufnr].filetype == "python" then
        return nil
      end
      return {
        timeout_ms = 3000,
        lsp_fallback = true,
      }
    end,

    -- Python など時間のかかるフォーマッターは保存後に非同期で実行する
    format_after_save = function(bufnr)
      if vim.bo[bufnr].filetype ~= "python" then
        return nil
      end
      return {
        lsp_fallback = true,
      }
    end,

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
