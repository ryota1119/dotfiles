return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main", -- 重要: mainブランチを明示
    build = ":TSUpdate",
    event = { "BufReadPost", "BufNewFile" }, -- 遅延読み込みの設定
    config = function()
      -- 新仕様では、setup関数は「パーサの管理」のみを行います
      require("nvim-treesitter").setup({
        -- インストールしておくべき言語パーサのリスト
        ensure_installed = {
          "bash",
          "c",
          "diff",
          "html",
          "javascript",
          "jsdoc",
          "json",
          "jsonc",
          "lua",
          "luadoc",
          "markdown",
          "markdown_inline",
          "python",
          "query",
          "regex",
          "ruby",
          "toml",
          "tsx",
          "typescript",
          "vim",
          "vimdoc",
          "yaml",
        },
        
        -- 未インストールの言語ファイルを開いた時に自動でインストールするか
        auto_install = true,
      })
    end,
  },
}