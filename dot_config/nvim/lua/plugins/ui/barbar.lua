return {
	"romgrk/barbar.nvim",
	dependencies = {
		"lewis6991/gitsigns.nvim", -- OPTIONAL: for git status
		"nvim-tree/nvim-web-devicons", -- OPTIONAL: for file icons
	},
	init = function()
		vim.g.barbar_auto_setup = true
	end,
	opts = {
		-- lazy.nvim will automatically call setup for you. put your options here, anything missing will use the default:
		animation = true,
		auto_hide = false,
		clickable = true,

		-- アイコン設定
		icons = {
			button = "×",
			modified = { button = "●" },
			pinned = { button = "📌", filename = true },
			separator = { left = "▎", right = "" },
			inactive = { separator = { left = "▎", right = "" } },
		},

		-- 最大バッファ名の長さ
		maximum_padding = 2,
		minimum_padding = 1,
		maximum_length = 30,

		-- セパレーターを表示
		separator = { left = "▎", right = "" },
		separator_at_end = false,
	},
	-- version = '^1.0.0', -- optional: only update when a new 1.x version is released
	config = function()
		local map = vim.api.nvim_set_keymap
		local opts = { noremap = true, silent = true }

		-- ============================================================================
		-- Barbar キーマップ
		-- ============================================================================
		-- バッファ間の移動
		map("n", "<A-,>", "<Cmd>BufferPrevious<CR>", vim.tbl_extend("force", opts, { desc = "Previous buffer" }))
		map("n", "<A-.>", "<Cmd>BufferNext<CR>", vim.tbl_extend("force", opts, { desc = "Next buffer" }))

		-- バッファの並び替え
		map("n", "<A-<>", "<Cmd>BufferMovePrevious<CR>", vim.tbl_extend("force", opts, { desc = "Move buffer left" }))
		map("n", "<A->>", "<Cmd>BufferMoveNext<CR>", vim.tbl_extend("force", opts, { desc = "Move buffer right" }))

		-- 番号でバッファへ移動
		map("n", "<A-1>", "<Cmd>BufferGoto 1<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 1" }))
		map("n", "<A-2>", "<Cmd>BufferGoto 2<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 2" }))
		map("n", "<A-3>", "<Cmd>BufferGoto 3<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 3" }))
		map("n", "<A-4>", "<Cmd>BufferGoto 4<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 4" }))
		map("n", "<A-5>", "<Cmd>BufferGoto 5<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 5" }))
		map("n", "<A-6>", "<Cmd>BufferGoto 6<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 6" }))
		map("n", "<A-7>", "<Cmd>BufferGoto 7<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 7" }))
		map("n", "<A-8>", "<Cmd>BufferGoto 8<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 8" }))
		map("n", "<A-9>", "<Cmd>BufferGoto 9<CR>", vim.tbl_extend("force", opts, { desc = "Go to buffer 9" }))
		map("n", "<A-0>", "<Cmd>BufferLast<CR>", vim.tbl_extend("force", opts, { desc = "Go to last buffer" }))

		-- バッファのピン留め
		map("n", "<A-p>", "<Cmd>BufferPin<CR>", vim.tbl_extend("force", opts, { desc = "Pin/unpin buffer" }))

		-- バッファを閉じる
		map("n", "<A-c>", "<Cmd>BufferClose<CR>", vim.tbl_extend("force", opts, { desc = "Close buffer" }))

		-- バッファピッカー
		map("n", "<C-p>", "<Cmd>BufferPick<CR>", vim.tbl_extend("force", opts, { desc = "Pick buffer" }))
		map("n", "<C-s-p>", "<Cmd>BufferPickDelete<CR>", vim.tbl_extend("force", opts, { desc = "Pick buffer to delete" }))

		-- バッファのソート
		map("n", "<Space>bb", "<Cmd>BufferOrderByBufferNumber<CR>", vim.tbl_extend("force", opts, { desc = "Order by buffer number" }))
		map("n", "<Space>bn", "<Cmd>BufferOrderByName<CR>", vim.tbl_extend("force", opts, { desc = "Order by name" }))
		map("n", "<Space>bd", "<Cmd>BufferOrderByDirectory<CR>", vim.tbl_extend("force", opts, { desc = "Order by directory" }))
		map("n", "<Space>bl", "<Cmd>BufferOrderByLanguage<CR>", vim.tbl_extend("force", opts, { desc = "Order by language" }))
		map("n", "<Space>bw", "<Cmd>BufferOrderByWindowNumber<CR>", vim.tbl_extend("force", opts, { desc = "Order by window number" }))

		-- ============================================================================
		-- カラースキーム設定
		-- ============================================================================
		-- backpack.nvimのカラースキームに統一
		-- カラースキーム読み込み後に実行されるように、少し遅延させる
		vim.defer_fn(function()
			-- backpackの色を取得
			local normal = vim.api.nvim_get_hl(0, { name = "Normal" })
			local comment = vim.api.nvim_get_hl(0, { name = "Comment" })
			local pmenu = vim.api.nvim_get_hl(0, { name = "Pmenu" })
			local pmenusel = vim.api.nvim_get_hl(0, { name = "PmenuSel" })
			local visual = vim.api.nvim_get_hl(0, { name = "Visual" })
			local string = vim.api.nvim_get_hl(0, { name = "String" })
			local warning = vim.api.nvim_get_hl(0, { name = "WarningMsg" })
			local error = vim.api.nvim_get_hl(0, { name = "ErrorMsg" })

			-- アクティブなバッファ（現在開いているバッファ）
			-- Visualのような選択状態の色を使用
			vim.api.nvim_set_hl(0, "BufferCurrent", {
				bg = visual.bg or pmenusel.bg,
				fg = normal.fg,
				bold = true,
			})
			vim.api.nvim_set_hl(0, "BufferCurrentIndex", {
				bg = visual.bg or pmenusel.bg,
				fg = normal.fg,
				bold = true,
			})
			vim.api.nvim_set_hl(0, "BufferCurrentMod", {
				bg = visual.bg or pmenusel.bg,
				fg = warning.fg or string.fg,
				bold = true,
				italic = true,
			})
			vim.api.nvim_set_hl(0, "BufferCurrentSign", {
				bg = visual.bg or pmenusel.bg,
				fg = comment.fg,
			})
			vim.api.nvim_set_hl(0, "BufferCurrentTarget", {
				bg = visual.bg or pmenusel.bg,
				fg = error.fg,
				bold = true,
			})

			-- 表示されているが非アクティブなバッファ
			vim.api.nvim_set_hl(0, "BufferVisible", {
				bg = pmenu.bg,
				fg = normal.fg,
			})
			vim.api.nvim_set_hl(0, "BufferVisibleIndex", {
				bg = pmenu.bg,
				fg = normal.fg,
			})
			vim.api.nvim_set_hl(0, "BufferVisibleMod", {
				bg = pmenu.bg,
				fg = warning.fg or string.fg,
				italic = true,
			})
			vim.api.nvim_set_hl(0, "BufferVisibleSign", {
				bg = pmenu.bg,
				fg = comment.fg,
			})
			vim.api.nvim_set_hl(0, "BufferVisibleTarget", {
				bg = pmenu.bg,
				fg = error.fg,
				bold = true,
			})

			-- 非表示のバッファ（インアクティブ）
			vim.api.nvim_set_hl(0, "BufferInactive", {
				bg = normal.bg,
				fg = comment.fg,
			})
			vim.api.nvim_set_hl(0, "BufferInactiveIndex", {
				bg = normal.bg,
				fg = comment.fg,
			})
			vim.api.nvim_set_hl(0, "BufferInactiveMod", {
				bg = normal.bg,
				fg = warning.fg or string.fg,
				italic = true,
			})
			vim.api.nvim_set_hl(0, "BufferInactiveSign", {
				bg = normal.bg,
				fg = comment.fg,
			})
			vim.api.nvim_set_hl(0, "BufferInactiveTarget", {
				bg = normal.bg,
				fg = error.fg,
			})

			-- オフセット（neo-treeなどのサイドバー）
			vim.api.nvim_set_hl(0, "BufferOffset", {
				bg = normal.bg,
				fg = comment.fg,
			})
		end, 100)
	end,
}
