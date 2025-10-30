return {
	"lukas-reineke/indent-blankline.nvim",
	main = "ibl",

	event = { "BufReadPost", "BufNewFile" },
	opts = {},

	config = function(_, opts)
		local ibl = require("ibl")

		-- 無効化したいファイルタイプを指定
		vim.api.nvim_create_autocmd("FileType", {
			pattern = { "dashboard" },
			callback = function()
				vim.b.ibl_disable = true
			end,
		})

		ibl.setup(opts)
	end,
}
