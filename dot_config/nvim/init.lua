-- リーダーキーは keymap を登録する前に必ず設定する。
-- vim.keymap.set の <leader> はこの時点の値で展開されるため、
-- config.keymaps や lazy.nvim の keys = {} より先に設定する必要がある。
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- 使わない provider を無効化（:checkhealth の警告抑制）
-- Lua/JS/TS/Python は LSP で扱うため、Neovim の旧 RPC provider は不要
vim.g.loaded_python3_provider = 0
vim.g.loaded_node_provider = 0
vim.g.loaded_perl_provider = 0
vim.g.loaded_ruby_provider = 0

-- 壊れた snippet による Neovim 0.12 のパースエラーを致命的にしない安全弁。
-- 一部の VSCode 形式 snippet（friendly-snippets の python try / trya / tryf /
-- tryef 等）には ${4:raise $3} や ${2: ${3:Exception} as ${4:e}} のような
-- 入れ子プレースホルダ・タブストップ参照が含まれ、
-- runtime/lua/vim/snippet.lua の Lua パーサが失敗する。
--
-- 重要: blink.cmp は accept 時に「入力済みテキストを削除してから expand」する
-- （completion/accept/init.lua）。そのため expand が失敗すると、打った文字が
-- 消えたまま何も挿入されないという分かりにくい壊れ方になる。
-- 失敗自体を黙って捨てると原因に気付けないため、WARN で通知する。
do
  local ok, snippet = pcall(require, "vim.snippet")
  if ok and type(snippet.expand) == "function" then
    local original_expand = snippet.expand
    snippet.expand = function(input)
      local ok_expand, err = pcall(original_expand, input)
      if not ok_expand then
        vim.schedule(function()
          vim.notify(
            "snippet expand failed (ignored): " .. tostring(err),
            vim.log.levels.WARN,
            { title = "snippet" }
          )
        end)
      end
    end
  end
end

-- 基本設定を読み込む
require("config.options")
require("config.keymaps")
require("config.autocmds")

-- プラグインマネージャを読み込む
require("config.lazy")

-- lsp設定を読み込む
require("config.lsp")
