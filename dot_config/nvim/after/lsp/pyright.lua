-- Python言語サーバー(pyright)のカスタム設定

---@type vim.lsp.Config
return {
  settings = {
    python = {
      analysis = {
        typeCheckingMode = "basic",
        autoSearchPaths = true,
        useLibraryCodeForTypes = true,
      },
    },
  },
}
