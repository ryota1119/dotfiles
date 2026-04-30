-- Python言語サーバー(basedpyright)のカスタム設定
-- pyrightの強化フォーク。型チェック・補完・ジャンプを担当
-- フォーマット/lint/import整理は ruff に任せる

---@type vim.lsp.Config
return {
  settings = {
    basedpyright = {
      analysis = {
        typeCheckingMode = "basic",
        autoSearchPaths = true,
        useLibraryCodeForTypes = true,
        diagnosticMode = "openFilesOnly",
        -- ruff と役割が重複する診断を抑止
        diagnosticSeverityOverrides = {
          reportUnusedImport = "none",
          reportUnusedVariable = "none",
          reportUnusedFunction = "none",
        },
      },
    },
  },
}
