-- ============================================================================
-- lspsaga.nvim: LSP UIの強化
-- ============================================================================
return {
  "nvimdev/lspsaga.nvim",
  event = "LspAttach",
  dependencies = {
    "nvim-treesitter/nvim-treesitter",
    "nvim-tree/nvim-web-devicons",
  },
  keys = {
    { "<leader>ca", "<cmd>Lspsaga code_action<cr>", desc = "Code action" },
    { "<leader>rn", "<cmd>Lspsaga rename<cr>", desc = "Rename" },
    { "<leader>pd", "<cmd>Lspsaga peek_definition<cr>", desc = "Peek definition" },
    { "<leader>pt", "<cmd>Lspsaga peek_type_definition<cr>", desc = "Peek type definition" },
    { "gd", "<cmd>Lspsaga goto_definition<cr>", desc = "Goto definition" },
    { "gt", "<cmd>Lspsaga goto_type_definition<cr>", desc = "Goto type definition" },
    { "[e", "<cmd>Lspsaga diagnostic_jump_prev<cr>", desc = "Previous diagnostic" },
    { "]e", "<cmd>Lspsaga diagnostic_jump_next<cr>", desc = "Next diagnostic" },
    { "[E", function()
      require("lspsaga.diagnostic"):goto_prev({ severity = vim.diagnostic.severity.ERROR })
    end, desc = "Previous error" },
    { "]E", function()
      require("lspsaga.diagnostic"):goto_next({ severity = vim.diagnostic.severity.ERROR })
    end, desc = "Next error" },
    { "<leader>o", "<cmd>Lspsaga outline<cr>", desc = "Outline" },
  },
  opts = {
    ui = {
      border = "rounded",
      devicon = true,
      title = true,
      expand = "",
      collapse = "",
      code_action = "💡",
      actionfix = " ",
      lines = { "┗", "┣", "┃", "━", "┏" },
      kind = nil,
      imp_sign = "󰳛 ",
    },
    symbol_in_winbar = {
      enable = true,
      separator = "  ",
      hide_keyword = true,
      show_file = true,
      folder_level = 2,
      color_mode = true,
    },
    lightbulb = {
      enable = false, -- 必要に応じて有効化
      sign = true,
      virtual_text = false,
    },
    diagnostic = {
      on_insert = false,
      on_insert_follow = false,
      show_code_action = true,
      show_source = true,
      jump_num_shortcut = true,
      max_width = 0.7,
      max_height = 0.6,
      text_hl_follow = false,
      border_follow = true,
      extend_relatedInformation = false,
      diagnostic_only_current = false,
      keys = {
        exec_action = "o",
        quit = { "q", "<ESC>" },
        expand_or_jump = "<CR>",
        quit_in_show = { "q", "<ESC>" },
      },
    },
    code_action = {
      num_shortcut = true,
      show_server_name = true,
      extend_gitsigns = true,
      keys = {
        quit = { "q", "<ESC>" },
        exec = "<CR>",
      },
    },
    rename = {
      in_select = true,
      auto_save = false,
      project_max_width = 0.5,
      project_max_height = 0.5,
      keys = {
        quit = "<C-c>",
        exec = "<CR>",
        select = "x",
      },
    },
    outline = {
      win_position = "right",
      win_width = 30,
      auto_preview = true,
      detail = true,
      auto_close = true,
      close_after_jump = false,
      keys = {
        toggle_or_jump = "<CR>",
        quit = "q",
      },
    },
    callhierarchy = {
      layout = "float",
      keys = {
        edit = "e",
        vsplit = "s",
        split = "i",
        tabe = "t",
        quit = "q",
        shuttle = "[w",
        toggle_or_req = "u",
      },
    },
    finder = {
      max_height = 0.5,
      left_width = 0.3,
      right_width = 0.3,
      methods = {},
      default = "ref+imp",
      layout = "float",
      filter = {},
      keys = {
        shuttle = "[w",
        toggle_or_open = "<CR>",
        vsplit = "s",
        split = "i",
        tabe = "t",
        tabnew = "r",
        quit = "q",
        close = "<ESC>",
      },
    },
    definition = {
      width = 0.6,
      height = 0.5,
      keys = {
        edit = "<C-c>o",
        vsplit = "<C-c>v",
        split = "<C-c>s",
        tabe = "<C-c>t",
        quit = "q",
        close = "<ESC>",
      },
    },
    hover = {
      max_width = 0.9,
      max_height = 0.8,
      open_link = "gx",
      open_cmd = "!open",
    },
    beacon = {
      enable = true,
      frequency = 7,
    },
  },
}