-- Neovim 0.11のネイティブLSP設定
-- 参考: https://zenn.dev/ras96/articles/4d9d9493d29c06

-- 診断（Diagnostics）の表示設定
vim.diagnostic.config({
  virtual_text = {
    source = "if_many",
    prefix = "●",
  },
  severity_sort = true,
  float = {
    border = "rounded",
    source = "if_many",
    header = "",
    prefix = "",
  },
})

-- 使用する言語サーバーを有効化
vim.lsp.enable({
  -- nvim-lspconfigのプリセットを使用
  "lua_ls",
  -- 他の言語サーバーをここに追加
  "ruby_lsp",
  "pyright",
  "ts_ls",
  "terraformls",
})

-- 言語サーバーがアタッチされた時に呼ばれる
vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("my-lsp", { clear = true }),
  callback = function(args)
    local client = assert(vim.lsp.get_client_by_id(args.data.client_id))
    local buf = args.buf

    -- デフォルトのキーマップに追加設定
    -- Neovim 0.11では多くのキーマップがデフォルトで設定されている
    -- See :help lsp-defaults

    -- 定義へジャンプ
    if client:supports_method("textDocument/definition") then
      vim.keymap.set("n", "gd", vim.lsp.buf.definition, {
        buffer = buf,
        desc = "Go to definition",
      })
    end

    -- ホバードキュメント
    if client:supports_method("textDocument/hover") then
      vim.keymap.set("n", "K", function()
        vim.lsp.buf.hover({ border = "rounded" })
      end, {
        buffer = buf,
        desc = "Show hover documentation",
      })
    end

    -- 参照を表示
    if client:supports_method("textDocument/references") then
      vim.keymap.set("n", "gr", vim.lsp.buf.references, {
        buffer = buf,
        desc = "Go to references",
      })
    end

    -- 実装へジャンプ
    if client:supports_method("textDocument/implementation") then
      vim.keymap.set("n", "gI", vim.lsp.buf.implementation, {
        buffer = buf,
        desc = "Go to implementation",
      })
    end

    -- 型定義へジャンプ
    if client:supports_method("textDocument/typeDefinition") then
      vim.keymap.set("n", "gy", vim.lsp.buf.type_definition, {
        buffer = buf,
        desc = "Go to type definition",
      })
    end

    -- コードアクション
    if client:supports_method("textDocument/codeAction") then
      vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, {
        buffer = buf,
        desc = "Code action",
      })
    end

    -- リネーム
    if client:supports_method("textDocument/rename") then
      vim.keymap.set("n", "<leader>cr", vim.lsp.buf.rename, {
        buffer = buf,
        desc = "Rename",
      })
    end

    -- ネイティブ補完を有効化
    -- blink.cmpを使用するためコメントアウト
    -- if client:supports_method("textDocument/completion") then
    --   vim.lsp.completion.enable(true, client.id, buf, { autotrigger = true })
    -- end

    -- 保存時に自動フォーマット
    -- conform.nvimを使用するためコメントアウト
    -- if
    --   not client:supports_method("textDocument/willSaveWaitUntil")
    --   and client:supports_method("textDocument/formatting")
    -- then
    --   vim.api.nvim_create_autocmd("BufWritePre", {
    --     group = vim.api.nvim_create_augroup("my-lsp-format", { clear = false }),
    --     buffer = buf,
    --     callback = function()
    --       vim.lsp.buf.format({ bufnr = buf, id = client.id, timeout_ms = 1000 })
    --     end,
    --   })
    -- end

    -- Inlay hintsを有効化
    -- <leader>ch（Code Hints）: <leader>th は toggleterm と競合するため移動
    if client:supports_method("textDocument/inlayHint") then
      vim.keymap.set("n", "<leader>ch", function()
        vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled({ bufnr = buf }), { bufnr = buf })
      end, {
        buffer = buf,
        desc = "Toggle inlay hints",
      })
    end

    -- インライン補完（GitHub Copilot用など）
    if client:supports_method("textDocument/inlineCompletion") then
      vim.lsp.inline_completion.enable(true, { bufnr = buf })
      vim.keymap.set("i", "<Tab>", function()
        if not vim.lsp.inline_completion.get() then
          return "<Tab>"
        end
        -- 補完ポップアップが開いていたら閉じる
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
