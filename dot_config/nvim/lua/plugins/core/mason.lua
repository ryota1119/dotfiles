-- local formatters = {
-- 	"stylua",
-- 	"prettierd",
-- 	"gofumpt",
-- 	"shfmt",
-- 	"php-cs-fixer",
-- }

-- local diagnostics = {
-- 	"golangci-lint",
-- 	"phpstan",
-- 	"erb_lint",
-- }

return {
  {
    "mason-org/mason.nvim",
    build = ":MasonUpdate",
    cmd = { "Mason", "MasonUpdate", "MasonLog", "MasonInstall", "MasonUninstall", "MasonUninstallAll" },
    config = function()
      require("mason").setup({
        ui = {
          border = "rounded",
          icons = {
            package_installed = "✓",
            package_pending = "➜",
            package_uninstalled = "✗"
          }
        }
      })
    end,
  },
  {
    "mason-org/mason-lspconfig.nvim",
    dependencies = {
      { "mason-org/mason.nvim" },
      { "neovim/nvim-lspconfig" },
    },
    event = { "BufReadPre", "BufNewFile" },
  },
}
