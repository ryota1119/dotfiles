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

      -- ハンク間ナビゲーション
      map("n", "]c", function()
        if vim.wo.diff then
          return "]c"
        end
        vim.schedule(function()
          gs.next_hunk()
        end)
        return "<Ignore>"
      end, { expr = true, desc = "Next hunk" })

      map("n", "[c", function()
        if vim.wo.diff then
          return "[c"
        end
        vim.schedule(function()
          gs.prev_hunk()
        end)
        return "<Ignore>"
      end, { expr = true, desc = "Prev hunk" })

      -- Git hunk 系は <leader>gh* に統一
      map("n", "<leader>ghs", gs.stage_hunk, { desc = "Stage hunk" })
      map("n", "<leader>ghr", gs.reset_hunk, { desc = "Reset hunk" })
      map("v", "<leader>ghs", function()
        gs.stage_hunk({ vim.fn.line("."), vim.fn.line("v") })
      end, { desc = "Stage selection" })
      map("v", "<leader>ghr", function()
        gs.reset_hunk({ vim.fn.line("."), vim.fn.line("v") })
      end, { desc = "Reset selection" })
      map("n", "<leader>ghS", gs.stage_buffer, { desc = "Stage buffer" })
      map("n", "<leader>ghu", gs.undo_stage_hunk, { desc = "Undo stage hunk" })
      map("n", "<leader>ghR", gs.reset_buffer, { desc = "Reset buffer" })
      map("n", "<leader>ghp", gs.preview_hunk, { desc = "Preview hunk" })
      map("n", "<leader>ghd", gs.diffthis, { desc = "Diff this" })
      map("n", "<leader>ghD", function()
        gs.diffthis("~")
      end, { desc = "Diff against last commit" })

      -- Blame
      map("n", "<leader>gb", function()
        gs.blame_line({ full = true })
      end, { desc = "Blame line" })

      -- Toggle 系
      map("n", "<leader>tB", gs.toggle_current_line_blame, { desc = "Toggle line blame" })
      map("n", "<leader>tD", gs.toggle_deleted, { desc = "Toggle deleted" })

      -- テキストオブジェクト
      map({ "o", "x" }, "ih", ":<C-U>Gitsigns select_hunk<CR>", { desc = "Git hunk" })
    end,
  },
}
