return {
	"nvimdev/dashboard-nvim",
	event = "VimEnter",
	config = function()
		require("dashboard").setup({
			theme = "doom",
			config = {
				header = {
					"",
					"███╗   ██╗██╗   ██╗██╗███╗   ███╗",
					"████╗  ██║██║   ██║██║████╗ ████║",
					"██╔██╗ ██║██║   ██║██║██╔████╔██║",
					"██║╚██╗██║╚██╗ ██╔╝██║██║╚██╔╝██║",
					"██║ ╚████║ ╚████╔╝ ██║██║ ╚═╝ ██║",
					"╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═╝     ╚═╝",
					"",
					"    ▸ Where code becomes poetry",
					"",
				},
				center = {
					{
						icon = "󰙅  ",
						desc = "Explorer",
						key = "e",
						key_format = " [%s]",
						action = "Neotree float",
					},
					{
						icon = "󰱼  ",
						desc = "Find File",
						key = "f",
						key_format = " [%s]",
						action = "Telescope find_files",
					},
					{
						icon = "󰋚  ",
						desc = "Recent Files",
						key = "r",
						key_format = " [%s]",
						action = "Telescope oldfiles",
					},
					{
						icon = "󰊢  ",
						desc = "Lazy Git",
						key = "g",
						key_format = " [%s]",
						action = "LazyGit",
					},

					{
						icon = "󰝒  ",
						desc = "New File",
						key = "n",
						key_format = " [%s]",
						action = "enew",
					},
					{
						icon = "󰚰  ",
						desc = "Update Plugins",
						key = "u",
						key_format = " [%s]",
						action = "Lazy update",
					},
					{
						icon = "󰗼  ",
						desc = "Quit",
						key = "q",
						key_format = " [%s]",
						action = "quit",
					},
				},
				footer = {
					"",
					"▸ In code we trust, in bugs we learn",
					"⚡ Every commit is a step forward",
					">> The terminal is my canvas",
					"",
				},
				vertical_center = true, -- Center the Dashboard on the vertical (from top to bottom)
			},
		})

		-- footerの背景色を透明にする
		vim.api.nvim_set_hl(0, "DashboardFooter", { bg = "NONE", fg = "#ffffff" })
	end,
	dependencies = { { "nvim-tree/nvim-web-devicons" } },
}
