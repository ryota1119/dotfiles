-- Ruff言語サーバーの設定
-- lint / format / import整理 を担当
-- 補完 / hover は basedpyright に譲る（重複防止 & snippet パースエラー回避）

---@type vim.lsp.Config
return {
  on_attach = function(client, _bufnr)
    -- basedpyright と役割を分離する
    client.server_capabilities.hoverProvider = false
    -- ruff の補完は snippet 形式で blink.cmp がパースエラーを起こすことがあるため無効化
    client.server_capabilities.completionProvider = nil
  end,
  init_options = {
    settings = {
      -- 必要に応じて lineLength や lint.select などをここで上書き可能
      -- 例:
      -- lineLength = 100,
      -- lint = { select = { "E", "F", "I", "UP" } },
    },
  },
}
