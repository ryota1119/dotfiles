-- リーダーキーはキーマップを登録する前に設定する必要がある
-- （vim.keymap.set の <leader> はこの時点の値で展開されるため）
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- 基本設定を読み込む
require("config.options")
require("config.keymaps")
require("config.autocmds")

-- プラグインマネージャを読み込む
require("config.lazy")

-- lsp設定を読み込む
require("config.lsp")
