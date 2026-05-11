return {
  "williamboman/mason-lspconfig.nvim",
  event = { "BufReadPre", "BufNewFile" },
  dependencies = {
    "williamboman/mason.nvim",
    "neovim/nvim-lspconfig",
  },
  opts = {
    -- vim.lsp.enable() で有効化する言語サーバーを自動インストール
    ensure_installed = {
      "lua_ls",
      "ruby_lsp",
      "basedpyright",
      "ruff",
      "ts_ls",
      "terraformls",
      "gopls",
    },
    automatic_installation = true,
  },
}
