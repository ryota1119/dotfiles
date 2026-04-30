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

-- Oil.nvim設定グループ
local oil_group = augroup("OilPreview", { clear = true })

-- Oilバッファを開いた時に自動的にプレビューを表示
autocmd("FileType", {
  group = oil_group,
  pattern = "oil",
  callback = function()
    -- 少し遅延させてからプレビューを開く（バッファが完全に読み込まれてから）
    vim.defer_fn(function()
      -- プレビューウィンドウが既に開いているかチェック
      local has_preview = false
      for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
        if vim.wo[win].previewwindow then
          has_preview = true
          break
        end
      end

      -- プレビューウィンドウがまだ開いていない場合のみ開く
      if not has_preview then
        pcall(function()
          require("oil.actions").preview.callback()
        end)
      end
    end, 100)
  end,
})
