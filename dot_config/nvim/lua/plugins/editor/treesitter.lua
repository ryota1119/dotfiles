-- nvim-treesitter (main ブランチ / v2.x 系)
-- master ブランチは 2025年にアーカイブ済み。
-- main は完全な書き直しで Neovim 0.12+ 専用。lazy-loading 非対応。
-- 必須: tree-sitter CLI (brew install tree-sitter-cli) と C コンパイラ。
return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    opts = {
      install_dir = vim.fn.stdpath("data") .. "/site",
    },
    config = function(_, opts)
      require("nvim-treesitter").setup(opts)

      local parsers = {
        "bash",
        "c",
        "diff",
        "go",
        "gomod",
        "gosum",
        "html",
        "javascript",
        "jsdoc",
        "json",
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
      }

      require("nvim-treesitter").install(parsers)

      -- main ブランチでは highlight / fold / indent は自動有効化されない。
      vim.api.nvim_create_autocmd("FileType", {
        pattern = parsers,
        callback = function(args)
          pcall(vim.treesitter.start, args.buf)
          vim.wo[0][0].foldexpr = "v:lua.vim.treesitter.foldexpr()"
          vim.wo[0][0].foldmethod = "expr"
          vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
        end,
      })
    end,
  },
}
