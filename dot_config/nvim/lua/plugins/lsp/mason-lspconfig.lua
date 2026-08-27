return {
  "williamboman/mason-lspconfig.nvim",
  event = { "BufReadPre", "BufNewFile" },
  dependencies = {
    "williamboman/mason.nvim",
    "neovim/nvim-lspconfig",
  },
  opts = {
    -- 言語サーバーを自動インストール
    ensure_installed = {
      "lua_ls",
      "basedpyright",
      "ruff",
      "ts_ls",
      "terraformls",
      "gopls",
    },
    -- インストール済みサーバーを vim.lsp.enable() で自動有効化
    -- 個別設定は after/lsp/<name>.lua で上書きする
    automatic_enable = true,
  },
}
