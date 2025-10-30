return {
	"lewis6991/gitsigns.nvim",
	event = { "BufReadPre", "BufNewFile" },
	config = function()
		require("gitsigns").setup({
			signs = {
				add = { text = "┃" },
				change = { text = "┃" },
				delete = { text = "_" },
				topdelete = { text = "‾" },
				changedelete = { text = "~" },
				untracked = { text = "┆" },
			},
			signs_staged = {
				add = { text = "┃" },
				change = { text = "┃" },
				delete = { text = "_" },
				topdelete = { text = "‾" },
				changedelete = { text = "~" },
				untracked = { text = "┆" },
			},
			signs_staged_enable = true,
			signcolumn = true,
			auto_attach = true,
			attach_to_untracked = false,

			on_attach = function(bufnr)
				local gs = require("gitsigns")
				local function map(mode, lhs, rhs, opts)
					opts = opts or {}
					opts.buffer = bufnr
					opts.silent = opts.silent ~= false
					vim.keymap.set(mode, lhs, rhs, opts)
				end

				-- ============================================================================
				-- Gitsigns キーマップ
				-- ============================================================================
				-- Hunk操作
				map("n", "]c", function()
					if vim.wo.diff then
						vim.cmd.normal({ "]c", bang = true })
					else
						gs.nav_hunk("next")
					end
				end, { desc = "Next hunk" })
				map("n", "[c", function()
					if vim.wo.diff then
						vim.cmd.normal({ "[c", bang = true })
					else
						gs.nav_hunk("prev")
					end
				end, { desc = "Previous hunk" })
				map("n", "<leader>hs", gs.stage_hunk, { desc = "Stage hunk" })
				map("n", "<leader>hr", gs.reset_hunk, { desc = "Reset hunk" })
				map("v", "<leader>hs", function()
					gs.stage_hunk({ vim.fn.line("."), vim.fn.line("v") })
				end, { desc = "Stage hunk (visual)" })
				map("v", "<leader>hr", function()
					gs.reset_hunk({ vim.fn.line("."), vim.fn.line("v") })
				end, { desc = "Reset hunk (visual)" })
				map("n", "<leader>hS", gs.stage_buffer, { desc = "Stage buffer" })
				map("n", "<leader>hR", gs.reset_buffer, { desc = "Reset buffer" })
				map("n", "<leader>hp", gs.preview_hunk, { desc = "Preview hunk" })
				map("n", "<leader>hi", gs.preview_hunk_inline, { desc = "Preview hunk inline" })
				map("n", "<leader>hb", function()
					gs.blame_line({ full = true })
				end, { desc = "Blame line" })
				map("n", "<leader>hd", gs.diffthis, { desc = "Diff this" })
				map("n", "<leader>hD", function()
					gs.diffthis("~")
				end, { desc = "Diff this (cached)" })
				map("n", "<leader>hQ", function()
					gs.setqflist("all")
				end, { desc = "Send all hunks to quickfix" })
				map("n", "<leader>hq", gs.setqflist, { desc = "Send hunks to quickfix" })
				map("n", "<leader>tb", gs.toggle_current_line_blame, { desc = "Toggle blame line" })
				map("n", "<leader>tw", gs.toggle_word_diff, { desc = "Toggle word diff" })
				map({ "o", "x" }, "ih", gs.select_hunk, { desc = "Select hunk" })
			end,
		})
	end,
}
