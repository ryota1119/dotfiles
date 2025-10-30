-- 基本設定とcapabilities
local capabilities = require('cmp_nvim_lsp').default_capabilities()

-- 診断設定（Neovim 0.11の標準機能）
vim.diagnostic.config({
  virtual_text = {
    severity = vim.diagnostic.severity.ERROR,
    source = "always",
    format = function(diagnostic)
      return string.format("%s: %s", diagnostic.source, diagnostic.message)
    end,
  },
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = {
    border = "rounded",
    source = "always",
    header = "",
    prefix = "",
  },
})

-- グローバルLSP設定
vim.lsp.config('*', {
  capabilities = capabilities,
  on_attach = function(client, bufnr)
    -- ============================================================================
    -- LSP キーマップ
    -- ============================================================================
    local opts = { noremap = true, silent = true, buffer = bufnr }

    -- 定義ジャンプ
    vim.keymap.set('n', 'gd', vim.lsp.buf.definition, vim.tbl_extend('force', opts, { desc = 'Go to definition' }))
    vim.keymap.set('n', 'gD', vim.lsp.buf.declaration, vim.tbl_extend('force', opts, { desc = 'Go to declaration' }))
    vim.keymap.set('n', 'gi', vim.lsp.buf.implementation, vim.tbl_extend('force', opts, { desc = 'Go to implementation' }))
    vim.keymap.set('n', 'gr', vim.lsp.buf.references, vim.tbl_extend('force', opts, { desc = 'Go to references' }))

    -- ホバー情報（lspsaga.nvimを使用）
    vim.keymap.set('n', 'K', function()
      require('lspsaga.hover').render_hover_doc()
    end, vim.tbl_extend('force', opts, { desc = 'Show hover documentation' }))

    -- -- リネーム（lspsaga.nvimを使用）
    -- vim.keymap.set('n', '<leader>rn', function()
    --   require('lspsaga.rename').rename()
    -- end, opts)

    -- -- コードアクション（lspsaga.nvimを使用）
    -- vim.keymap.set('n', '<leader>ca', function()
    --   require('lspsaga.codeaction').code_action()
    -- end, opts)

    -- フォーマット
    vim.keymap.set('n', '<leader>cf', function()
      vim.lsp.buf.format({ async = true })
    end, vim.tbl_extend('force', opts, { desc = 'Format code' }))

    -- 診断情報（Neovim 0.11の標準機能を使用）
    vim.keymap.set('n', '<leader>cd', vim.diagnostic.open_float, vim.tbl_extend('force', opts, { desc = 'Show diagnostic' }))
    vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, vim.tbl_extend('force', opts, { desc = 'Previous diagnostic' }))
    vim.keymap.set('n', ']d', vim.diagnostic.goto_next, vim.tbl_extend('force', opts, { desc = 'Next diagnostic' }))
  end,
})

-- LSPサーバーのインストール
local lsp_servers = {
  "gopls",
  "lua_ls",
  "ruby_lsp",
  "jsonls",
  "bashls",
  "yamlls",
  "terraformls",
  "vtsls",
}

require("mason").setup()
require("mason-lspconfig").setup({
  ensure_installed = lsp_servers,
  automatic_installation = true,
})

-- 各言語サーバーの個別設定は after/lsp/ フォルダに配置

-- 言語サーバーを有効化
vim.lsp.enable(lsp_servers)

-- LSPクライアント確認用のコマンド
vim.api.nvim_create_user_command("LspStatus", function()
  local clients = vim.lsp.get_clients({ bufnr = vim.api.nvim_get_current_buf() })
  print("=== LSP Status ===")
  print("Buffer:", vim.api.nvim_get_current_buf())
  print("FileType:", vim.bo.filetype)
  print("Attached clients:")
  for _, client in ipairs(clients) do
    print("  -", client.name, "(ID:", client.id, ")", "Status:", client.is_stopped() and "stopped" or "running")
  end
  if #clients == 0 then
    print("  No LSP clients attached")
  end
end, { desc = "Show LSP status for current buffer" })

-- 診断の表示切り替えコマンド
vim.api.nvim_create_user_command("DiagnosticToggle", function()
  local config = vim.diagnostic.config()
  vim.diagnostic.config({
    virtual_text = not config.virtual_text,
  })
  print("Virtual text:", config.virtual_text and "OFF" or "ON")
end, { desc = "Toggle diagnostic virtual text" })
