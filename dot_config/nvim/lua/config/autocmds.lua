-- オートコマンド設定

local augroup = vim.api.nvim_create_augroup
local autocmd = vim.api.nvim_create_autocmd

-- 一般設定グループ
local general = augroup("General", { clear = true })

-- ファイル保存時に末尾の空白を削除
-- - modifiable でないバッファ（help, checkhealth, terminal 等）はスキップ
-- - 一部の filetype では末尾空白に意味があるためスキップ
autocmd("BufWritePre", {
  group = general,
  pattern = "*",
  callback = function(args)
    if not vim.bo[args.buf].modifiable then
      return
    end
    local skipped_filetypes = {
      ["diff"] = true,
      ["gitcommit"] = true,
      ["markdown"] = true,
    }
    if skipped_filetypes[vim.bo[args.buf].filetype] then
      return
    end
    local save_cursor = vim.fn.getpos(".")
    pcall(vim.cmd, [[%s/\s\+$//e]])
    vim.fn.setpos(".", save_cursor)
  end,
})

-- ヤンク時にハイライト
autocmd("TextYankPost", {
  group = general,
  pattern = "*",
  callback = function()
    vim.highlight.on_yank({ higroup = "IncSearch", timeout = 200 })
  end,
})

-- ファイルを開いた時に最後のカーソル位置に移動
autocmd("BufReadPost", {
  group = general,
  pattern = "*",
  callback = function()
    local mark = vim.api.nvim_buf_get_mark(0, '"')
    local lcount = vim.api.nvim_buf_line_count(0)
    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})

-- ターミナルモードで行番号を非表示
autocmd("TermOpen", {
  group = general,
  pattern = "*",
  callback = function()
    vim.opt_local.number = false
    vim.opt_local.relativenumber = false
  end,
})

-- Treesitter highlight / fold（main ブランチは自動では有効にならないため手動設定）
local ts_group = augroup("TreesitterFeatures", { clear = true })
autocmd("FileType", {
  group = ts_group,
  callback = function()
    local ok = pcall(vim.treesitter.start)
    if ok then
      -- Treesitter ベースの折り畳み
      vim.wo[0][0].foldmethod = "expr"
      vim.wo[0][0].foldexpr = "v:lua.vim.treesitter.foldexpr()"
      vim.wo[0][0].foldenable = false
    end
  end,
})

