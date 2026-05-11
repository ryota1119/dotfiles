-- Go言語サーバー(gopls)のカスタム設定
-- 補完・定義ジャンプ・型チェック・インレイヒントを担当
-- フォーマット/import整理は conform.nvim (goimports → gofmt) に任せる

---@type vim.lsp.Config
return {
  settings = {
    gopls = {
      analyses = {
        unusedparams = true,
        shadow = true,
      },
      staticcheck = true,
      gofumpt = false,
      -- インレイヒント（<leader>tH でトグル可能）
      hints = {
        assignVariableTypes = true,
        compositeLiteralFields = true,
        compositeLiteralTypes = true,
        constantValues = true,
        functionTypeParameters = true,
        parameterNames = true,
        rangeVariableTypes = true,
      },
    },
  },
}
