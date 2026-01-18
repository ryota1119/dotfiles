-- プラグイン設定のサンプル
-- このファイルをコピーして新しいプラグイン設定を作成できます

return {
  -- 例: カラースキーム
  -- {
  --   "folke/tokyonight.nvim",
  --   lazy = false, -- 起動時に読み込む
  --   priority = 1000, -- 他のプラグインより先に読み込む
  --   opts = {
  --     style = "night",
  --     transparent = false,
  --   },
  --   config = function(_, opts)
  --     require("tokyonight").setup(opts)
  --     vim.cmd([[colorscheme tokyonight]])
  --   end,
  -- },

  -- 例: ファイルエクスプローラー
  -- {
  --   "nvim-tree/nvim-tree.lua",
  --   dependencies = {
  --     "nvim-tree/nvim-web-devicons",
  --   },
  --   opts = {
  --     view = {
  --       width = 30,
  --     },
  --   },
  --   keys = {
  --     { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle File Explorer" },
  --   },
  -- },
}
