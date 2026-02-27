return {
  "numToStr/Comment.nvim",
  event = { "BufReadPre", "BufNewFile" },
  dependencies = {
    "JoosepAlviste/nvim-ts-context-commentstring",
  },
  config = function()
    -- Treesitterと統合してコンテキストに応じたコメント文字列を使用
    require("Comment").setup({
      -- LHS of toggle mappings in NORMAL mode
      toggler = {
        line = "gcc", -- 行コメント切り替え
        block = "gbc", -- ブロックコメント切り替え
      },
      -- LHS of operator-pending mappings in NORMAL and VISUAL mode
      opleader = {
        line = "gc", -- 行コメント
        block = "gb", -- ブロックコメント
      },
      -- LHS of extra mappings
      extra = {
        above = "gcO", -- 上に行コメント追加
        below = "gco", -- 下に行コメント追加
        eol = "gcA", -- 行末にコメント追加
      },
      -- Enable keybindings
      mappings = {
        basic = true,
        extra = true,
      },
      -- Treesitterとの統合
      pre_hook = require("ts_context_commentstring.integrations.comment_nvim").create_pre_hook(),
    })
  end,
}
