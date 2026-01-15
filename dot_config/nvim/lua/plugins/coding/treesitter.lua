-- ============================================================================
-- nvim-treesitter: 構文解析とハイライト
-- ============================================================================
return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  event = { "BufReadPost", "BufNewFile", "BufNewFile", "VeryLazy" },
  lazy = vim.fn.argc(-1) == 0, -- ファイルが開かれていない場合のみ遅延読み込み
  init = function(plugin)
    -- パフォーマンス最適化: runtimepathにプラグインを追加
    require("lazy.core.loader").add_to_rtp(plugin)
    require("nvim-treesitter.query_predicates")
  end,
  cmd = { "TSUpdateSync", "TSUpdate", "TSInstall" },
  keys = {
    { "<leader>ts", "<cmd>TSUpdate<cr>", desc = "Treesitter Update" },
    { "<leader>ti", "<cmd>TSInstallInfo<cr>", desc = "Treesitter Info" },
    { "<C-space>", desc = "Increment Selection" },
    { "<bs>", desc = "Decrement Selection", mode = "x" },
  },
  opts_extend = { "ensure_installed" },
  opts = {
    highlight = { enable = true },
    indent = { enable = true },
    ensure_installed = {
      "bash",
      "c",
      "css",
      "diff",
      "go",
      "html",
      "javascript",
      "jsdoc",
      "json",
      "jsonc",
      "lua",
      "luadoc",
      "luap",
      "markdown",
      "markdown_inline",
      "printf",
      "python",
      "query",
      "regex",
      "ruby",
      "terraform",
      "toml",
      "tsx",
      "typescript",
      "vim",
      "vimdoc",
      "xml",
      "yaml",
    },
    incremental_selection = {
      enable = true,
      keymaps = {
        init_selection = "<C-space>",
        node_incremental = "<C-space>",
        scope_incremental = false,
        node_decremental = "<bs>",
      },
    },
  },
  config = function(_, opts)
    -- nvim-treesitter.configsが利用可能かチェック
    local has_configs, configs = pcall(require, "nvim-treesitter.configs")
    if has_configs then
      configs.setup(opts)
    else
      -- フォールバック: 手動でTreesitterを有効化
      vim.notify("nvim-treesitter.configs not found, using fallback config", vim.log.levels.WARN)
      
      -- 自動的にTreesitterを有効化
      vim.api.nvim_create_autocmd({ "FileType" }, {
        pattern = "*",
        callback = function()
          local buf = vim.api.nvim_get_current_buf()
          pcall(vim.treesitter.start, buf)
        end,
      })
    end
  end,
}
