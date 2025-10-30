-- 設定ファイルの読み込み
require("config.lazy")

-- 基本設定
require("config.options")
require("config.keymaps")
require("config.autocmds")
require("config.filetype")

-- lsp設定
require("lsp")
