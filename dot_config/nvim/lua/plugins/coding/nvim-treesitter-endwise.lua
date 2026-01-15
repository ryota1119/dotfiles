return {
  "https://github.com/AbaoFromCUG/nvim-treesitter-endwise",
  dependencies = { "nvim-treesitter/nvim-treesitter" },
  ft = { "ruby", "eruby", "lua", "bash", "sh" },
  enabled = false, -- 一時的に無効化（mainブランチ対応待ち）
  config = function()
    -- mainブランチ対応版の設定
    require("nvim-treesitter-endwise").init()
  end,
}