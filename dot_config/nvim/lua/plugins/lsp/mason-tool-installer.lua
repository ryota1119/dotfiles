return {
  "WhoIsSethDaniel/mason-tool-installer.nvim",
  event = "VeryLazy",
  dependencies = {
    "williamboman/mason.nvim",
    "williamboman/mason-lspconfig.nvim",
  },
  opts = {
    -- フォーマッターとリンターを自動インストール
    ensure_installed = {
      -- Formatters
      "stylua", -- Lua
      "ruff", -- Python (linter + formatter + import sorter)
      "prettier", -- JS/TS/JSON/YAML/Markdown
      "shfmt", -- Shell
      -- "rubocop", -- Ruby (オプション)
      -- "goimports", -- Go (オプション)
      -- "gofmt", -- Go (オプション)
      -- "rustfmt", -- Rust (オプション)

      -- Linters（将来追加する場合）
      -- "eslint_d", -- JS/TS
    },
    
    -- 起動時に自動インストール
    auto_update = false,
    run_on_start = true,
  },
}
