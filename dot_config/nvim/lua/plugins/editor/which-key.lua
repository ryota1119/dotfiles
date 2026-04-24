return {
  "folke/which-key.nvim",
  event = "VeryLazy",
  opts = {
    preset = "modern",
    delay = 300,
    icons = {
      breadcrumb = "»",
      separator = "➜",
      group = "+",
    },
    win = {
      border = "rounded",
      padding = { 1, 2 },
    },
  },
  keys = {
    {
      "<leader>?",
      function()
        require("which-key").show({ global = false })
      end,
      desc = "Buffer Keymaps (which-key)",
    },
  },
  config = function(_, opts)
    local wk = require("which-key")
    wk.setup(opts)

    -- ============================================================
    -- <leader> 配下のキーマップ見出し
    -- ※ 実際のバインド先は各プラグイン/keymaps.lua/lsp.lua で定義
    --   which-key は見出し（グループ名 + 単発キーの説明）のみ登録
    -- ============================================================
    wk.add({
      mode = { "n" },

      -- -----------------------------------------------------------
      -- 単発キー（<leader> のトップレベル）
      -- -----------------------------------------------------------
      { "<leader>w", desc = "Save" },
      { "<leader>q", desc = "Quit" },
      { "<leader>?", desc = "Buffer Keymaps (which-key)" },

      -- -----------------------------------------------------------
      -- <leader>b : Buffer
      -- -----------------------------------------------------------
      { "<leader>b", group = "Buffer" },
      { "<leader>bd", desc = "Close Buffer" },

      -- -----------------------------------------------------------
      -- <leader>c : Code / LSP
      -- -----------------------------------------------------------
      { "<leader>c", group = "Code / LSP" },
      { "<leader>ca", desc = "Code Action" },
      { "<leader>cd", desc = "診断一覧（location list）トグル" },
      { "<leader>cD", desc = "診断一覧（quickfix）トグル" },
      { "<leader>ce", desc = "診断をフロートで表示" },
      { "<leader>cf", desc = "Format Buffer" },
      { "<leader>ch", desc = "Toggle Inlay Hints" },
      { "<leader>cm", desc = "Mason" },
      { "<leader>cr", desc = "Rename" },

      -- -----------------------------------------------------------
      -- <leader>e : Explorer (neo-tree)
      -- -----------------------------------------------------------
      { "<leader>e", group = "Explorer" },
      { "<leader>ee", desc = "Neo-tree toggle" },
      { "<leader>ef", desc = "Neo-tree float" },

      -- -----------------------------------------------------------
      -- <leader>f : Find (Telescope)
      -- -----------------------------------------------------------
      { "<leader>f", group = "Find (Telescope)" },
      { "<leader>fb", desc = "Buffers" },
      { "<leader>fc", desc = "Commands" },
      { "<leader>ff", desc = "Find Files" },
      { "<leader>fg", desc = "Live Grep" },
      { "<leader>fh", desc = "Help Tags" },
      { "<leader>fk", desc = "Keymaps" },
      { "<leader>fr", desc = "Recent Files" },
      { "<leader>fs", desc = "Buffer Search" },

      -- -----------------------------------------------------------
      -- <leader>g : Git（lazygit / gitsigns の大粒アクション）
      -- -----------------------------------------------------------
      { "<leader>g", group = "Git" },
      { "<leader>gg", desc = "LazyGit" },
      -- 以下は gitsigns.lua で <leader>h 配下に集約済み（重複配置しない）

      -- -----------------------------------------------------------
      -- <leader>h : Git Hunks (gitsigns)
      -- -----------------------------------------------------------
      { "<leader>h", group = "Git Hunks" },
      { "<leader>hb", desc = "Blame line (full)" },
      { "<leader>hd", desc = "Diff this" },
      { "<leader>hD", desc = "Diff with last commit" },
      { "<leader>hp", desc = "Preview hunk" },
      { "<leader>hr", desc = "Reset hunk" },
      { "<leader>hR", desc = "Reset buffer" },
      { "<leader>hs", desc = "Stage hunk" },
      { "<leader>hS", desc = "Stage buffer" },
      { "<leader>hu", desc = "Undo stage hunk" },

      -- -----------------------------------------------------------
      -- <leader>n : No Highlight
      -- -----------------------------------------------------------
      { "<leader>n", group = "Misc" },
      { "<leader>nh", desc = "No Highlight" },

      -- -----------------------------------------------------------
      -- <leader>s : Split
      -- -----------------------------------------------------------
      { "<leader>s", group = "Split" },
      { "<leader>sv", desc = "Vertical Split" },
      { "<leader>sh", desc = "Horizontal Split" },

      -- -----------------------------------------------------------
      -- <leader>t : Toggle 系（インラインヒント以外の各種トグル）
      -- -----------------------------------------------------------
      { "<leader>t", group = "Toggle" },
      { "<leader>tb", desc = "Toggle line blame" },
      { "<leader>td", desc = "Toggle deleted lines" },
      { "<leader>tt", desc = "Toggle Floating Terminal" },

      -- -----------------------------------------------------------
      -- <leader>T : Terminal (分割)
      -- -----------------------------------------------------------
      { "<leader>T", group = "Terminal (分割)" },
      { "<leader>Th", desc = "水平分割ターミナル" },
      { "<leader>Tv", desc = "垂直分割ターミナル" },

      -- -----------------------------------------------------------
      -- <leader>x : Lists
      -- -----------------------------------------------------------
      { "<leader>x", group = "Lists" },
      { "<leader>xl", desc = "Location list トグル" },
      { "<leader>xq", desc = "Quickfix トグル" },
    })

    -- ============================================================
    -- ビジュアルモードでの <leader>
    -- ============================================================
    wk.add({
      mode = { "v" },
      { "<leader>c", group = "Code / LSP" },
      { "<leader>ca", desc = "Code Action" },
      { "<leader>cf", desc = "Format Selection" },

      { "<leader>h", group = "Git Hunks" },
      { "<leader>hs", desc = "Stage selection" },
      { "<leader>hr", desc = "Reset selection" },
    })

    -- ============================================================
    -- g プレフィックス（LSP のジャンプ系・Comment.nvim）
    -- LSP 系は LspAttach 時にバッファローカルで登録されるため、
    -- which-key にグループ見出しを明示しておく
    -- ============================================================
    wk.add({
      mode = { "n" },
      { "g", group = "Goto / Comment" },
      { "gd", desc = "Go to Definition" },
      { "gr", desc = "Go to References" },
      { "gI", desc = "Go to Implementation" },
      { "gy", desc = "Go to Type Definition" },
      -- Comment.nvim
      { "gcc", desc = "Toggle Line Comment" },
      { "gbc", desc = "Toggle Block Comment" },
      { "gcO", desc = "Comment Above" },
      { "gco", desc = "Comment Below" },
      { "gcA", desc = "Comment End of Line" },
    })

    -- ============================================================
    -- [ / ] プレフィックス（診断・Git hunk のジャンプ）
    -- ============================================================
    wk.add({
      mode = { "n" },
      { "[", group = "Prev" },
      { "]", group = "Next" },
      { "[d", desc = "Prev Diagnostic" },
      { "]d", desc = "Next Diagnostic" },
      { "[c", desc = "Prev Git Hunk" },
      { "]c", desc = "Next Git Hunk" },
    })
  end,
}
