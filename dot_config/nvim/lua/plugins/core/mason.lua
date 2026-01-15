-- ============================================================================
-- Mason: LSP/DAP/Linter/Formatter のパッケージマネージャー
-- ============================================================================
return {
  -- Mason本体
  {
    "williamboman/mason.nvim",
    build = ":MasonUpdate",
    cmd = { "Mason", "MasonUpdate", "MasonLog", "MasonInstall", "MasonUninstall", "MasonUninstallAll" },
    opts = {
      ui = {
        border = "rounded",
        width = 0.8,
        height = 0.8,
        icons = {
          package_installed = "✓",
          package_pending = "➜",
          package_uninstalled = "✗",
        },
      },
      -- パッケージのインストール先
      install_root_dir = vim.fn.stdpath("data") .. "/mason",
      -- 最大同時ダウンロード数
      max_concurrent_installers = 4,
    },
  },

  -- Mason-LSPConfig: Masonとlspconfigの連携
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = {
      "williamboman/mason.nvim",
      "neovim/nvim-lspconfig",
    },
    event = { "BufReadPre", "BufNewFile" },
    opts = {
      -- 自動インストールするLSPサーバー
      ensure_installed = {
        "bashls",       -- Bash
        "gopls",        -- Go
        "jsonls",       -- JSON
        "lua_ls",       -- Lua
        "ruby_lsp",     -- Ruby
        "terraformls",  -- Terraform
        "vtsls",        -- TypeScript/JavaScript
        "yamlls",       -- YAML
      },
      -- LSPが見つからない場合に自動インストール
      automatic_installation = true,
    },
  },
}
