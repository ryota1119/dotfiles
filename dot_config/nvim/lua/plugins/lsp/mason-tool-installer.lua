return {
  "WhoIsSethDaniel/mason-tool-installer.nvim",
  dependencies = {
    "williamboman/mason.nvim",
  },
  opts = {
    -- フォーマッターとリンターを自動インストール
    ensure_installed = {
      -- Formatters
      "stylua", -- Lua
      "black", -- Python
      "isort", -- Python
      "prettier", -- JS/TS/JSON/YAML/Markdown
      "shfmt", -- Shell
      -- "rubocop", -- Ruby (オプション)
      -- "goimports", -- Go (オプション)
      -- "gofmt", -- Go (オプション)
      -- "rustfmt", -- Rust (オプション)
      
      -- Linters（将来追加する場合）
      -- "eslint_d", -- JS/TS
      -- "pylint", -- Python
    },
    
    -- 起動時に自動インストール
    auto_update = false,
    run_on_start = true,
  },
}
