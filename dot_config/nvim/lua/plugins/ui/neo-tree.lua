return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "echasnovski/mini.icons",
    },
    lazy = false,
    keys = {
      { "<leader>ee", "<cmd>Neotree left<cr>",   desc = "Open Neo-Tree" },
      { "<leader>ef", "<cmd>Neotree float<cr>",  desc = "Open Neo-Tree Float" },
      { "<leader>et", "<cmd>Neotree toggle<cr>", desc = "Open Neo-Tree Tab" },
      { "<leader>ec", "<cmd>Neotree close<cr>",  desc = "Close Neo-Tree" },
    },
    config = function()
      require("neo-tree").setup({
        filesystem = {
          use_libuv_file_watcher = true, -- パフォーマンス向上のためlibuvファイルウォッチャーを使用
          follow_current_file = {
            enabled = false,             -- 自動追従を無効化してパフォーマンス向上
          },
          hijack_netrw_behavior = "open_default",
          -- パフォーマンス向上のため、大きなディレクトリのウォッチャーを無効化
          filesystem_watchers = {
            ignore_dirs = {
              "node_modules",
              ".git",
              ".next",
              ".nuxt",
              "dist",
              "build",
              ".cache",
              "__pycache__",
              ".venv",
              "venv",
            },
          },
          git_status = {
            async = true, -- 非同期でGitステータスを取得
            -- パフォーマンスが遅い場合は以下を有効化してGit statusを無効化
            -- enabled = false,
          },
          -- 診断機能を無効化してパフォーマンス向上（必要に応じて有効化）
          enable_diagnostics = false,
          filtered_items = {
            visible = false, -- デフォルトで非表示アイテムを表示しない
            hide_dotfiles = false,
            hide_gitignored = false,
            hide_hidden = false,
            hide_by_name = {
              -- 大きなファイルやディレクトリを除外
              ".git",
              "node_modules",
              ".DS_Store",
              "__pycache__",
              ".pytest_cache",
              ".mypy_cache",
              ".venv",
              "venv",
              ".next",
              ".nuxt",
              "dist",
              "build",
              ".cache",
            },
          },
          window = {
            position = "left",
            width = 30,
            mapping_options = {
              noremap = true,
              nowait = true,
            },
          },
        },
        buffers = {
          follow_current_file = {
            enabled = false,
          },
        },
      })
    end,
  },
  {
    "antosha417/nvim-lsp-file-operations",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-neo-tree/neo-tree.nvim", -- makes sure that this loads after Neo-tree.
    },
    config = function()
      require("lsp-file-operations").setup()
    end,
  },
  {
    "s1n7ax/nvim-window-picker",
    version = "2.*",
    config = function()
      require("window-picker").setup({
        filter_rules = {
          include_current_win = false,
          autoselect_one = true,
          -- filter using buffer options
          bo = {
            -- if the file type is one of following, the window will be ignored
            filetype = { "neo-tree", "neo-tree-popup", "notify" },
            -- if the buffer type is one of following, the window will be ignored
            buftype = { "terminal", "quickfix" },
          },
        },
      })
    end,
  },
}
