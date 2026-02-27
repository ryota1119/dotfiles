return {
  "nvim-neo-tree/neo-tree.nvim",
  branch = "v3.x",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-tree/nvim-web-devicons",
    "MunifTanjim/nui.nvim",
  },
  cmd = "Neotree",
  keys = {
    { "<leader>ee", "<cmd>Neotree toggle<cr>", desc = "Neo-tree toggle" },
    { "<leader>ef", "<cmd>Neotree float<cr>", desc = "Neo-tree float" },
  },
  opts = {
    close_if_last_window = true,
    popup_border_style = "rounded",
    enable_git_status = true,
    enable_diagnostics = true,
    open_files_do_not_replace_types = { "terminal", "trouble", "qf" },
    window = {
      position = "left",
      width = 35,
      mappings = {
        ["<space>"] = { "toggle_node", nowait = false },
        ["<cr>"] = "open",
        ["<esc>"] = "cancel",
        ["P"] = { "toggle_preview", config = { use_float = true } },
        ["l"] = "open",
        ["h"] = "close_node",
        ["z"] = "close_all_nodes",
        ["Z"] = "expand_all_nodes",
        ["a"] = { "add", config = { show_path = "none" } },
        ["A"] = "add_directory",
        ["d"] = "delete",
        ["r"] = "rename",
        ["y"] = "copy_to_clipboard",
        ["x"] = "cut_to_clipboard",
        ["p"] = "paste_from_clipboard",
        ["c"] = "copy",
        ["m"] = "move",
        ["q"] = "close_window",
        ["R"] = "refresh",
        ["?"] = "show_help",
        ["<"] = "prev_source",
        [">"] = "next_source",
      },
    },
    filesystem = {
      follow_current_file = { enabled = true },
      hijack_netrw_behavior = "open_default",
      use_libuv_file_watcher = true,
    },
  },
  config = function(_, opts)
    require("neo-tree").setup(opts)

    -- float モードのときはプレビューを自動表示
    local events = require("neo-tree.events")
    local Preview = require("neo-tree.sources.common.preview")
    local manager = require("neo-tree.sources.manager")
    events.subscribe({
      event = events.AFTER_RENDER,
      handler = function(state)
        if
          state
          and state.current_position == "float"
          and state.tree
          and not Preview.is_active()
        then
          vim.schedule(function()
            local current_state = manager.get_state(state.name, state.tabid, state.winid)
            if current_state and current_state.tree then
              -- マッピング経由でない呼び出しでは state.config が nil になるため設定
              current_state.config = current_state.config or { use_float = true }
              pcall(Preview.show, current_state)
            end
          end)
        end
      end,
    })

    -- Fix: state.tree が nil のときに filter が呼ばれると E5108 エラーになる
    local filter = require("neo-tree.sources.filesystem.lib.filter")
    local original_show_filter = filter.show_filter
    filter.show_filter = function(state, ...)
      if not state or not state.tree then
        vim.notify("Neo-tree: ツリーの読み込みを待ってからフィルターを使用してください。", vim.log.levels.WARN)
        return
      end
      return original_show_filter(state, ...)
    end
  end,
}
