return {
  "williamboman/mason-lspconfig.nvim",
  dependencies = {
    "williamboman/mason.nvim",
    "neovim/nvim-lspconfig",
  },
  config = function()
    require("mason-lspconfig").setup({
      -- vim.lsp.enable()で指定した言語サーバーを自動インストール
      ensure_installed = {
        "lua_ls",
        "ruby_lsp",
        "pyright",
        "ts_ls",
        "terraformls",
      },
      -- Masonでインストール可能なサーバーは自動インストール
      automatic_installation = true,
    })
  end,
}
