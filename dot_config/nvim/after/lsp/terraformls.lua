-- Terraform言語サーバー(terraformls)のカスタム設定
-- タイムアウト対策: terraform-lsは初期化やTerraform実行に時間がかかることがある

---@type vim.lsp.Config
return {
  -- terraform-lsはsettingsではなくinit_optionsで設定を渡す必要がある
  -- https://github.com/hashicorp/terraform-ls/blob/main/docs/SETTINGS.md
  init_options = {
    terraform = {
      -- Terraform実行のタイムアウトを延長（デフォルトより長く）
      timeout = "60s",
    },
  },
}
