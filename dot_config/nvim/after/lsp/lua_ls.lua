-- Lua言語サーバー(lua_ls)のカスタム設定
-- nvim-lspconfigのプリセットを上書き

---@type vim.lsp.Config
return {
  settings = {
    Lua = {
      completion = {
        callSnippet = "Replace",
      },
      workspace = {
        -- Neovim runtimeのLua定義を読み込む
        library = {
          vim.env.VIMRUNTIME .. "/lua",
        },
      },
    },
  },
}
