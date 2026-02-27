return {
  "lewis6991/gitsigns.nvim",
  event = { "BufReadPre", "BufNewFile" },
  opts = {
    signs = {
      add = { text = "│" },
      change = { text = "│" },
      delete = { text = "_" },
      topdelete = { text = "‾" },
      changedelete = { text = "~" },
      untracked = { text = "┆" },
    },
    signcolumn = true,
    numhl = false,
    linehl = false,
    word_diff = false,
    watch_gitdir = {
      follow_files = true,
    },
    attach_to_untracked = true,
    current_line_blame = false,
    current_line_blame_opts = {
      virt_text = true,
      virt_text_pos = "eol",
      delay = 1000,
      ignore_whitespace = false,
    },
    on_attach = function(bufnr)
      local gs = package.loaded.gitsigns

      local function map(mode, l, r, opts)
        opts = opts or {}
        opts.buffer = bufnr
        vim.keymap.set(mode, l, r, opts)
      end

      -- ナビゲーション
      map("n", "]c", function()
        if vim.wo.diff then
          return "]c"
        end
        vim.schedule(function()
          gs.next_hunk()
        end)
        return "<Ignore>"
      end, { expr = true, desc = "次の変更箇所へ" })

      map("n", "[c", function()
        if vim.wo.diff then
          return "[c"
        end
        vim.schedule(function()
          gs.prev_hunk()
        end)
        return "<Ignore>"
      end, { expr = true, desc = "前の変更箇所へ" })

      -- アクション
      map("n", "<leader>hs", gs.stage_hunk, { desc = "ハンクをステージング" })
      map("n", "<leader>hr", gs.reset_hunk, { desc = "ハンクをリセット" })
      map("v", "<leader>hs", function()
        gs.stage_hunk({ vim.fn.line("."), vim.fn.line("v") })
      end, { desc = "選択範囲をステージング" })
      map("v", "<leader>hr", function()
        gs.reset_hunk({ vim.fn.line("."), vim.fn.line("v") })
      end, { desc = "選択範囲をリセット" })
      map("n", "<leader>hS", gs.stage_buffer, { desc = "バッファ全体をステージング" })
      map("n", "<leader>hu", gs.undo_stage_hunk, { desc = "ステージングを取り消し" })
      map("n", "<leader>hR", gs.reset_buffer, { desc = "バッファ全体をリセット" })
      map("n", "<leader>hp", gs.preview_hunk, { desc = "ハンクをプレビュー" })
      map("n", "<leader>hb", function()
        gs.blame_line({ full = true })
      end, { desc = "行のブレイムを表示" })
      map("n", "<leader>tb", gs.toggle_current_line_blame, { desc = "行ブレイム表示を切替" })
      map("n", "<leader>hd", gs.diffthis, { desc = "差分を表示" })
      map("n", "<leader>hD", function()
        gs.diffthis("~")
      end, { desc = "前回のコミットとの差分" })
      map("n", "<leader>td", gs.toggle_deleted, { desc = "削除行の表示を切替" })

      -- テキストオブジェクト
      map({ "o", "x" }, "ih", ":<C-U>Gitsigns select_hunk<CR>", { desc = "Git ハンクを選択" })
    end,
  },
}
