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

-- Oil.nvim設定グループ
local oil_group = augroup("OilPreview", { clear = true })

-- Oilバッファでカーソルがエントリ行に乗った最初のタイミングでプレビューを開く
-- FileType 時点ではバッファ描画が未完了なため CursorMoved まで待つ
autocmd("FileType", {
  group = oil_group,
  pattern = "oil",
  callback = function(args)
    local opened = false
    local id
    id = vim.api.nvim_create_autocmd("CursorMoved", {
      buffer = args.buf,
      once = false,
      callback = function()
        if opened then
          vim.api.nvim_del_autocmd(id)
          return
        end
        -- エントリが取得できる行にいる場合のみプレビューを開く
        local ok, entry = pcall(require("oil").get_cursor_entry)
        if ok and entry then
          opened = true
          vim.api.nvim_del_autocmd(id)
          -- プレビューが既に開いていなければ開く
          local has_preview = false
          for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
            if vim.wo[win].previewwindow then
              has_preview = true
              break
            end
          end
          if not has_preview then
            pcall(require("oil.actions").preview.callback)
          end
        end
      end,
    })
  end,
})
