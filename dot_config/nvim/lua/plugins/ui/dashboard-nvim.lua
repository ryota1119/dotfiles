-- ============================================================================
-- dashboard-nvim: スタート画面
-- ============================================================================
return {
  "nvimdev/dashboard-nvim",
  event = "VimEnter",
  dependencies = { "nvim-tree/nvim-web-devicons" },
  opts = function()
    local logo = [[
      ███╗   ██╗██╗   ██╗██╗███╗   ███╗
      ████╗  ██║██║   ██║██║████╗ ████║
      ██╔██╗ ██║██║   ██║██║██╔████╔██║
      ██║╚██╗██║╚██╗ ██╔╝██║██║╚██╔╝██║
      ██║ ╚████║ ╚████╔╝ ██║██║ ╚═╝ ██║
      ╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═╝     ╚═╝

         ▸ Where code becomes poetry
    ]]

    logo = string.rep("\n", 8) .. logo .. "\n\n"

    local opts = {
      theme = "doom",
      hide = {
        statusline = false,
      },
      config = {
        header = vim.split(logo, "\n"),
        center = {
          {
            icon = "  ",
            desc = "Explorer                ",
            key = "e",
            key_format = " %s",
            action = "Neotree float",
          },
          {
            icon = "  ",
            desc = "Find File               ",
            key = "f",
            key_format = " %s",
            action = "Telescope find_files",
          },
          {
            icon = "  ",
            desc = "Recent Files            ",
            key = "r",
            key_format = " %s",
            action = "Telescope oldfiles",
          },
          {
            icon = "  ",
            desc = "Find Text               ",
            key = "g",
            key_format = " %s",
            action = "Telescope live_grep",
          },
          {
            icon = "  ",
            desc = "Lazy Git                ",
            key = "l",
            key_format = " %s",
            action = "LazyGit",
          },
          {
            icon = "  ",
            desc = "New File                ",
            key = "n",
            key_format = " %s",
            action = "enew",
          },
          {
            icon = "  ",
            desc = "Lazy Manager            ",
            key = "p",
            key_format = " %s",
            action = "Lazy",
          },
          {
            icon = "  ",
            desc = "Mason Manager           ",
            key = "m",
            key_format = " %s",
            action = "Mason",
          },
          {
            icon = "  ",
            desc = "Quit                    ",
            key = "q",
            key_format = " %s",
            action = "qa",
          },
        },
        footer = function()
          local stats = require("lazy").stats()
          local ms = (math.floor(stats.startuptime * 100 + 0.5) / 100)
          return {
            "",
            "⚡ Neovim loaded " .. stats.loaded .. "/" .. stats.count .. " plugins in " .. ms .. "ms",
          }
        end,
      },
    }

    return opts
  end,
}
