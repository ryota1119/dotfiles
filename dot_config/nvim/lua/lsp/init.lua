-- ============================================================================
-- LSP設定の初期化（Neovim 0.11+対応）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 基本設定
-- ----------------------------------------------------------------------------
local capabilities = require("cmp_nvim_lsp").default_capabilities()

-- 診断設定
vim.diagnostic.config({
  virtual_text = {
    severity = vim.diagnostic.severity.ERROR,
    source = "if_many",
    prefix = "●",
  },
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = {
    border = "rounded",
    source = "if_many",
    header = "",
    prefix = "",
    focusable = false,
  },
})

-- 診断記号
local signs = {
  { name = "DiagnosticSignError", text = "" },
  { name = "DiagnosticSignWarn", text = "" },
  { name = "DiagnosticSignHint", text = "" },
  { name = "DiagnosticSignInfo", text = "" },
}
for _, sign in ipairs(signs) do
  vim.fn.sign_define(sign.name, { texthl = sign.name, text = sign.text, numhl = "" })
end

-- ----------------------------------------------------------------------------
-- on_attach関数
-- ----------------------------------------------------------------------------
local function on_attach(client, bufnr)
  local opts = { noremap = true, silent = true, buffer = bufnr }

  -- ナビゲーション
  vim.keymap.set("n", "gd", vim.lsp.buf.definition, vim.tbl_extend("force", opts, { desc = "Go to definition" }))
  vim.keymap.set("n", "gD", vim.lsp.buf.declaration, vim.tbl_extend("force", opts, { desc = "Go to declaration" }))
  vim.keymap.set("n", "gi", vim.lsp.buf.implementation, vim.tbl_extend("force", opts, { desc = "Go to implementation" }))
  vim.keymap.set("n", "gr", vim.lsp.buf.references, vim.tbl_extend("force", opts, { desc = "Go to references" }))
  vim.keymap.set("n", "gy", vim.lsp.buf.type_definition, vim.tbl_extend("force", opts, { desc = "Go to type definition" }))

  -- ドキュメント
  vim.keymap.set("n", "K", vim.lsp.buf.hover, vim.tbl_extend("force", opts, { desc = "Hover documentation" }))

  -- 編集
  vim.keymap.set("n", "<leader>cr", vim.lsp.buf.rename, vim.tbl_extend("force", opts, { desc = "Rename symbol" }))
  vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, vim.tbl_extend("force", opts, { desc = "Code action" }))

  -- フォーマット
  vim.keymap.set("n", "<leader>cf", function()
    local conform_ok, conform = pcall(require, "conform")
    if conform_ok then
      conform.format({ async = true, lsp_fallback = true })
    else
      vim.lsp.buf.format({ async = true })
    end
  end, vim.tbl_extend("force", opts, { desc = "Format code" }))

  -- 診断
  vim.keymap.set("n", "<leader>cd", vim.diagnostic.open_float, vim.tbl_extend("force", opts, { desc = "Show diagnostic" }))
  vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, vim.tbl_extend("force", opts, { desc = "Previous diagnostic" }))
  vim.keymap.set("n", "]d", vim.diagnostic.goto_next, vim.tbl_extend("force", opts, { desc = "Next diagnostic" }))
  vim.keymap.set("n", "<leader>cl", "<cmd>LspInfo<cr>", vim.tbl_extend("force", opts, { desc = "LSP Info" }))

  -- ドキュメントハイライト
  if client.server_capabilities.documentHighlightProvider then
    local group = vim.api.nvim_create_augroup("lsp_document_highlight", { clear = false })
    vim.api.nvim_clear_autocmds({ buffer = bufnr, group = group })
    vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
      group = group,
      buffer = bufnr,
      callback = vim.lsp.buf.document_highlight,
    })
    vim.api.nvim_create_autocmd("CursorMoved", {
      group = group,
      buffer = bufnr,
      callback = vim.lsp.buf.clear_references,
    })
  end
end

-- ----------------------------------------------------------------------------
-- グローバルLSP設定（全サーバー共通）
-- ----------------------------------------------------------------------------
vim.lsp.config("*", {
  capabilities = capabilities,
  on_attach = on_attach,
})

-- ----------------------------------------------------------------------------
-- 個別LSPサーバー設定（vim.lsp.config使用）
-- ----------------------------------------------------------------------------
-- lua_ls
vim.lsp.config.lua_ls = {
  cmd = { "lua-language-server" },
  root_markers = { ".luarc.json", ".luarc.jsonc", ".luacheckrc", ".stylua.toml", "stylua.toml", "selene.toml", "selene.yml", ".git" },
  settings = {
    Lua = {
      diagnostics = {
        globals = { "vim" },
      },
      workspace = {
        library = {
          vim.env.VIMRUNTIME,
        },
        checkThirdParty = false,
      },
      telemetry = {
        enable = false,
      },
    },
  },
}

-- gopls
vim.lsp.config.gopls = {
  cmd = { "gopls" },
  root_markers = { "go.work", "go.mod", ".git" },
  settings = {
    gopls = {
      gofumpt = true,
      staticcheck = true,
      usePlaceholders = true,
      completeUnimported = true,
    },
  },
}

-- jsonls
vim.lsp.config.jsonls = {
  cmd = { "vscode-json-language-server", "--stdio" },
  root_markers = { "package.json", ".git" },
  settings = {
    json = {
      schemas = require("schemastore").json.schemas(),
      validate = { enable = true },
    },
  },
}

-- yamlls
vim.lsp.config.yamlls = {
  cmd = { "yaml-language-server", "--stdio" },
  root_markers = { ".git" },
  settings = {
    yaml = {
      schemas = require("schemastore").yaml.schemas(),
    },
  },
}

-- bashls
vim.lsp.config.bashls = {
  cmd = { "bash-language-server", "start" },
  root_markers = { ".git" },
}

-- vtsls (TypeScript/JavaScript)
vim.lsp.config.vtsls = {
  cmd = { "vtsls", "--stdio" },
  root_markers = { "package.json", "tsconfig.json", "jsconfig.json", ".git" },
}

-- terraformls
vim.lsp.config.terraformls = {
  cmd = { "terraform-ls", "serve" },
  root_markers = { ".terraform", ".git" },
}

-- ruby_lsp
vim.lsp.config.ruby_lsp = {
  cmd = { "ruby-lsp" },
  root_markers = { "Gemfile", ".git" },
}

-- ----------------------------------------------------------------------------
-- LSPサーバーの有効化
-- ----------------------------------------------------------------------------
local servers = {
  "bashls",
  "gopls",
  "jsonls",
  "lua_ls",
  "ruby_lsp",
  "terraformls",
  "vtsls",
  "yamlls",
}

vim.lsp.enable(servers)

-- ----------------------------------------------------------------------------
-- ユーティリティコマンド
-- ----------------------------------------------------------------------------
vim.api.nvim_create_user_command("LspStatus", function()
  local clients = vim.lsp.get_clients({ bufnr = vim.api.nvim_get_current_buf() })
  print("=== LSP Status ===")
  print("Buffer:", vim.api.nvim_get_current_buf())
  print("FileType:", vim.bo.filetype)
  print("Attached clients:")
  for _, client in ipairs(clients) do
    print("  -", client.name, "(ID:", client.id, ")")
  end
  if #clients == 0 then
    print("  No LSP clients attached")
  end
end, { desc = "Show LSP status for current buffer" })

vim.api.nvim_create_user_command("DiagnosticToggle", function()
  local config = vim.diagnostic.config()
  vim.diagnostic.config({
    virtual_text = not config.virtual_text,
  })
  print("Virtual text:", config.virtual_text and "OFF" or "ON")
end, { desc = "Toggle diagnostic virtual text" })
