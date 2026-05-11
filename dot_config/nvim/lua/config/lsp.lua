-- Neovim 0.11+ のネイティブ LSP 設定
-- 参考: https://zenn.dev/ras96/articles/4d9d9493d29c06

-- 使用する言語サーバーを有効化（after/lsp/<name>.lua で個別設定を上書き）
vim.lsp.enable({
  "lua_ls",
  "ruby_lsp",
  "basedpyright",
  "ruff",
  "ts_ls",
  "terraformls",
  "gopls",
})

-- 診断 (diagnostics) UI のモダン構成
vim.diagnostic.config({
  -- 行末にエラーメッセージを薄く表示。長文はカット
  virtual_text = {
    prefix = "●",
    spacing = 2,
    source = "if_many",
  },
  -- サインカラムにアイコン
  signs = {
    text = {
      [vim.diagnostic.severity.ERROR] = " ",
      [vim.diagnostic.severity.WARN] = " ",
      [vim.diagnostic.severity.HINT] = " ",
      [vim.diagnostic.severity.INFO] = " ",
    },
  },
  -- 重要度の高いものを上に
  severity_sort = true,
  -- 下線
  underline = true,
  -- 入力中はチラつかせない
  update_in_insert = false,
  -- :h vim.diagnostic.open_float() のデフォルト
  float = {
    border = "rounded",
    source = "if_many",
    header = "",
    prefix = "",
  },
})

-- 言語サーバーがアタッチされた時に呼ばれる
vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("my-lsp", { clear = true }),
  callback = function(args)
    local client = assert(vim.lsp.get_client_by_id(args.data.client_id))
    local buf = args.buf

    local function map(mode, lhs, rhs, desc)
      vim.keymap.set(mode, lhs, rhs, { buffer = buf, desc = desc })
    end

    -- ジャンプ系（Neovim 0.11+ のデフォルト :help lsp-defaults を補強）
    if client:supports_method("textDocument/definition") then
      map("n", "gd", vim.lsp.buf.definition, "Go to definition")
    end
    if client:supports_method("textDocument/declaration") then
      map("n", "gD", vim.lsp.buf.declaration, "Go to declaration")
    end
    if client:supports_method("textDocument/references") then
      map("n", "gr", vim.lsp.buf.references, "Go to references")
    end
    if client:supports_method("textDocument/implementation") then
      map("n", "gI", vim.lsp.buf.implementation, "Go to implementation")
    end
    if client:supports_method("textDocument/typeDefinition") then
      map("n", "gy", vim.lsp.buf.type_definition, "Go to type definition")
    end

    -- ホバー
    if client:supports_method("textDocument/hover") then
      map("n", "K", function()
        vim.lsp.buf.hover({ border = "rounded" })
      end, "Hover documentation")
    end

    -- シグネチャヘルプ
    if client:supports_method("textDocument/signatureHelp") then
      map("i", "<C-k>", vim.lsp.buf.signature_help, "Signature help")
    end

    -- <leader>c* = Code / LSP
    if client:supports_method("textDocument/codeAction") then
      map({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, "Code action")
    end
    if client:supports_method("textDocument/rename") then
      map("n", "<leader>cr", vim.lsp.buf.rename, "Rename symbol")
    end
    map("n", "<leader>cf", function()
      require("conform").format({ async = true, lsp_fallback = true })
    end, "Format buffer")
    map("v", "<leader>cf", function()
      require("conform").format({ async = true, lsp_fallback = true })
    end, "Format selection")
    map("n", "<leader>cd", vim.diagnostic.open_float, "Line diagnostics")
    map("n", "<leader>cl", "<cmd>LspInfo<cr>", "LSP info")
    -- <leader>cm = Mason は mason.lua 側の keys で定義済み
    if client:supports_method("textDocument/documentSymbol") then
      map("n", "<leader>cs", "<cmd>Telescope lsp_document_symbols<cr>", "Document symbols")
    end
    if client:supports_method("workspace/symbol") then
      map("n", "<leader>cS", "<cmd>Telescope lsp_dynamic_workspace_symbols<cr>", "Workspace symbols")
    end

    -- 診断ナビゲーション
    map("n", "[d", function()
      vim.diagnostic.jump({ count = -1, float = true })
    end, "Previous diagnostic")
    map("n", "]d", function()
      vim.diagnostic.jump({ count = 1, float = true })
    end, "Next diagnostic")

    -- Toggle 系（<leader>t* に統一）
    if client:supports_method("textDocument/inlayHint") then
      map("n", "<leader>tH", function()
        vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled({ bufnr = buf }), { bufnr = buf })
      end, "Toggle inlay hints")
    end

    -- インライン補完（Copilot 等を LSP で扱う場合）
    if client:supports_method("textDocument/inlineCompletion") then
      vim.lsp.inline_completion.enable(true, { bufnr = buf })
      vim.keymap.set("i", "<Tab>", function()
        if not vim.lsp.inline_completion.get() then
          return "<Tab>"
        end
        if vim.fn.pumvisible() == 1 then
          return "<C-e>"
        end
      end, {
        expr = true,
        buffer = buf,
        desc = "Accept inline completion",
      })
    end
  end,
})
