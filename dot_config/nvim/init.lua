-- 壊れた snippet による Neovim 0.12 のパースエラーを握りつぶす安全弁。
-- 一部の VSCode 形式 snippet（friendly-snippets の python tryef 等）には
-- ${2: ${3:Exception} as ${4:e}} のような入れ子プレースホルダが含まれ、
-- runtime/lua/vim/snippet.lua の Lua パーサが失敗してエラーが赤く表示される。
-- 失敗時は静かに無視し、補完候補としては挿入されないだけにする。
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
            vim.log.levels.DEBUG,
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
