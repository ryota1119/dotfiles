-- 自動コマンド設定
local api = vim.api

-- 自動コマンドグループの作成
local augroup = api.nvim_create_augroup
local autocmd = api.nvim_create_autocmd

-- ファイルタイプ別の設定をテーブルベースで管理
local filetype_configs = {
	-- Lua/Vim設定
	["lua"] = {
		shiftwidth = 2,
		tabstop = 2,
		commentstring = "-- %s",
	},
	["vim"] = {
		shiftwidth = 2,
		tabstop = 2,
		commentstring = "-- %s",
	},
	-- JavaScript/TypeScript設定
	["javascript"] = { commentstring = "// %s" },
	["typescript"] = { commentstring = "// %s" },
	["javascriptreact"] = { commentstring = "// %s" },
	["typescriptreact"] = { commentstring = "// %s" },
	-- HTML/CSS設定
	["html"] = { commentstring = "<!-- %s -->" },
	["css"] = { commentstring = "<!-- %s -->" },
	["scss"] = { commentstring = "<!-- %s -->" },
	["sass"] = { commentstring = "<!-- %s -->" },
	-- Ruby設定
	["ruby"] = {
		shiftwidth = 2,
		tabstop = 2,
		commentstring = "# %s",
	},
	-- Python/Dockerfile設定
	["python"] = {
		shiftwidth = 4,
		tabstop = 4,
	},
	["dockerfile"] = {
		shiftwidth = 4,
		tabstop = 4,
	},
	-- YAML設定
	["yaml"] = {
		shiftwidth = 2,
		tabstop = 2,
	},
	["yml"] = {
		shiftwidth = 2,
		tabstop = 2,
	},
	-- Go設定
	["go"] = {
		shiftwidth = 8,
		tabstop = 8,
		expandtab = false,
	},
	-- Terraform設定
	["terraform"] = {
		shiftwidth = 2,
		tabstop = 2,
		commentstring = "# %s",
	},
}

-- ファイルタイプ設定を適用する関数
local function apply_filetype_config()
	local filetype = vim.bo.filetype
	local config = filetype_configs[filetype]
	if config then
		for option, value in pairs(config) do
			vim.opt_local[option] = value
		end
	end
end

-- ファイルタイプ設定の適用
augroup("FileTypeSettings", { clear = true })
autocmd("FileType", {
	group = "FileTypeSettings",
	pattern = vim.tbl_keys(filetype_configs),
	callback = apply_filetype_config,
})

-- カーソル位置を復元する関数
local function restore_cursor_position()
	local mark = vim.api.nvim_buf_get_mark(0, '"')
	local lcount = vim.api.nvim_buf_line_count(0)
	if mark[1] > 0 and mark[1] <= lcount then
		pcall(vim.api.nvim_win_set_cursor, 0, mark)
	end
end

-- カーソル位置の復元
augroup("CursorRestore", { clear = true })
autocmd("BufReadPost", {
	group = "CursorRestore",
	callback = restore_cursor_position,
})
