return {
  "kylechui/nvim-surround",
  version = "*",
  event = { "BufReadPre", "BufNewFile" },
  config = function()
    require("nvim-surround").setup({
      -- コンフィグはデフォルトで問題なし
      -- カスタマイズしたい場合はここに追加
    })
  end,
}
