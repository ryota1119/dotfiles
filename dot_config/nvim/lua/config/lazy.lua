-- ============================================================================
-- lazy.nvim ブートストラップと設定
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Leader キーの設定（lazy.nvim読み込み前に設定必須）
-- ----------------------------------------------------------------------------
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- ----------------------------------------------------------------------------
-- lazy.nvim のブートストラップ
-- ----------------------------------------------------------------------------
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "--branch=stable",
    lazyrepo,
    lazypath,
  })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

-- ----------------------------------------------------------------------------
-- lazy.nvim のセットアップ
-- ----------------------------------------------------------------------------
require("lazy").setup({
  -- プラグイン仕様
  spec = {
    { import = "plugins" },
  },

  -- インストール設定
  install = {
    colorscheme = { "habamax" },  -- インストール時の仮カラースキーム
  },

  -- UI設定
  ui = {
    border = "rounded",  -- ウィンドウの境界線スタイル
    size = {
      width = 0.8,
      height = 0.8,
    },
    icons = {
      cmd = "⌘",
      config = "🛠",
      event = "📅",
      ft = "📂",
      init = "⚙",
      keys = "🗝",
      plugin = "🔌",
      runtime = "💻",
      require = "🌙",
      source = "📄",
      start = "🚀",
      task = "📌",
      lazy = "💤 ",
    },
  },

  -- パフォーマンス設定
  performance = {
    rtp = {
      disabled_plugins = {
        "gzip",
        "matchit",
        "matchparen",
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },

  -- 変更検知設定
  change_detection = {
    enabled = true,      -- 設定ファイルの変更を自動検知
    notify = false,      -- 通知は無効（うるさいので）
  },

  -- 自動更新チェック
  checker = {
    enabled = true,      -- 自動更新チェックを有効化
    notify = false,      -- 通知は無効
    frequency = 3600,    -- チェック頻度（秒）
  },

  -- Luarocks無効化（パフォーマンス向上）
  rocks = {
    enabled = false,
  },
})
