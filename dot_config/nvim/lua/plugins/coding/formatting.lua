-- ============================================================================
-- conform.nvim: コードフォーマッター
-- ============================================================================
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
    -- 言語ごとのフォーマッター設定
    formatters_by_ft = {
      -- Lua
      lua = { "stylua" },
      
      -- JavaScript/TypeScript
      javascript = { "prettier" },
      javascriptreact = { "prettier" },
      typescript = { "prettier" },
      typescriptreact = { "prettier" },
      
      -- Web
      html = { "prettier" },
      css = { "prettier" },
      scss = { "prettier" },
      sass = { "prettier" },
      
      -- 設定ファイル
      json = { "prettier" },
      jsonc = { "prettier" },
      yaml = { "prettier" },
      yml = { "prettier" },
      toml = { "taplo" },
      
      -- ドキュメント
      markdown = { "prettier" },
      
      -- その他の言語
      sh = { "shfmt" },
      bash = { "shfmt" },
      go = { "gofumpt", "goimports" },
      python = { "black", "isort" },
      rust = { "rustfmt" },
      
      -- コメントアウト例
      -- ruby = { "rubocop" },
      -- php = { "php_cs_fixer" },
      -- eruby = { "erb_lint" },
    },

    -- デフォルトフォーマットオプション
    default_format_opts = {
      lsp_fallback = true,
    },

    -- 保存時の自動フォーマット
    format_on_save = function(bufnr)
      -- 大きすぎるファイルはスキップ
      local max_filesize = 100 * 1024 -- 100 KB
      local ok, stats = pcall(vim.loop.fs_stat, vim.api.nvim_buf_get_name(bufnr))
      if ok and stats and stats.size > max_filesize then
        return
      end

      return {
        timeout_ms = 500,
        lsp_fallback = true,
      }
    end,

    -- フォーマッター設定のカスタマイズ
    formatters = {
      shfmt = {
        prepend_args = { "-i", "2" }, -- インデント2スペース
      },
    },

    -- 通知設定
    notify_on_error = true,
  },
}
