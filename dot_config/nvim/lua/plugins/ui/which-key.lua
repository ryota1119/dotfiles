return {
  "folke/which-key.nvim",
  event = "VeryLazy",
  opts = {
    preset = "modern", -- "modern", "classic", "helix"
    delay = 300, -- ポップアップ表示までの遅延時間（ミリ秒）
    
    -- キーグループのラベル定義
    spec = {
      -- Telescope
      { "<leader>f", group = "🔍 Find (Telescope)" },
      
      -- Neo-tree
      { "<leader>e", group = "📁 Explorer (Neo-tree)" },
      
      -- Git
      { "<leader>g", group = "🔀 Git" },
      { "<leader>h", group = "📝 Git Hunks (Gitsigns)" },
      
      -- Trouble & Diagnostics
      { "<leader>x", group = "🔧 Trouble/Diagnostics" },
      
      -- Code & LSP
      { "<leader>c", group = "💻 Code/LSP" },
      
      -- Toggle & Treesitter & Tmux
      { "<leader>t", group = "⚙️  Toggle/Treesitter/Tmux" },
      
      -- Buffer (Barbar)
      { "<Space>b", group = "📑 Buffer Order" },
      
      -- その他
      { "<leader>w", desc = "💾 Save file" },
      { "<leader>q", desc = "❌ Quit window" },
      { "<leader>Q", desc = "🚫 Quit all (force)" },
    },
    
    -- ウィンドウ設定
    win = {
      border = "rounded", -- "none", "single", "double", "rounded", "solid", "shadow"
      padding = { 1, 2 }, -- 内側の余白 [top/bottom, left/right]
    },
    
    -- レイアウト設定
    layout = {
      height = { min = 4, max = 25 }, -- 最小・最大の高さ
      width = { min = 20, max = 50 }, -- 最小・最大の幅
      spacing = 3, -- カラム間のスペース
      align = "left", -- "left", "center", "right"
    },
    
    -- アイコン設定
    icons = {
      breadcrumb = "»", -- パンくずリストのセパレーター
      separator = "➜", -- キーとラベルのセパレーター
      group = "+", -- グループアイコン
    },
  },
  keys = {
    {
      "<leader>?",
      function()
        require("which-key").show({ global = false })
      end,
      desc = "❓ Buffer Local Keymaps (which-key)",
    },
  },
}