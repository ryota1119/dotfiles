-- blink.cmp の補完設定（2026年版モダン構成）
--
-- スニペット方針:
--   * Neovim 0.10+ のネイティブ vim.snippet を blink.cmp の標準 snippets プリセットで使う
--   * friendly-snippets でコミュニティスニペットを提供（runtimepath から自動検索）
--   * LuaSnip は導入せず、プラグインレス構成を維持する

return {
  "saghen/blink.cmp",
  event = "InsertEnter",
  version = "*",
  dependencies = { "rafamadriz/friendly-snippets" },

  opts = {
    keymap = {
      preset = "default",
      ["<C-space>"] = { "show", "show_documentation", "hide_documentation" },
      ["<C-e>"] = { "hide" },
      ["<C-y>"] = { "select_and_accept" },

      ["<CR>"] = { "accept", "fallback" },

      ["<C-p>"] = { "select_prev", "fallback" },
      ["<C-n>"] = { "select_next", "fallback" },

      ["<C-b>"] = { "scroll_documentation_up", "fallback" },
      ["<C-f>"] = { "scroll_documentation_down", "fallback" },

      ["<Tab>"] = { "snippet_forward", "fallback" },
      ["<S-Tab>"] = { "snippet_backward", "fallback" },
    },

    appearance = {
      use_nvim_cmp_as_default = true,
      nerd_font_variant = "mono",
    },

    snippets = {
      preset = "default",
    },

    sources = {
      default = { "lsp", "path", "snippets", "buffer" },
      providers = {
        snippets = {
          opts = {
            -- friendly-snippets は registry の friendly_snippets = true（デフォルト）が
            -- runtimepath から自動で拾う。ここに明示すると二重スキャンになり、
            -- friendly 由来の候補が全部2件ずつ並ぶので書かない。
            search_paths = {
              vim.fn.stdpath("config") .. "/snippets",
            },
          },

          -- Neovim 0.12 の native snippet パーサで展開できない snippet を候補から外す。
          -- friendly-snippets の python try / trya / tryf / tryef のように
          -- ${4:raise $3} や入れ子プレースホルダを含むものは vim.snippet.expand が
          -- 失敗し、選んでも何も挿入されない。候補に出さないのが唯一まともな扱い。
          transform_items = function(_, items)
            local safe_parse = require("blink.cmp.sources.snippets.utils").safe_parse
            return vim.tbl_filter(function(item)
              local text = item.textEdit and item.textEdit.newText or item.insertText
              if text == nil then return true end
              return safe_parse(text) ~= nil
            end, items)
          end,
        },
      },
    },

    completion = {
      list = {
        selection = {
          preselect = true,
          -- auto_insert は無効にする。有効だと選択を動かすたびに候補の1行目だけが
          -- バッファへ先行挿入され、複数行 snippet では `try` が `try:` になる。
          -- カーソルが keyword でない `:` の直後へ動くため
          -- completion/trigger/init.lua の on_cursor_moved が hide を呼び、
          -- 以降の <C-n> が Vim 組み込み補完に fallback して無関係な語を挿入する。
          auto_insert = false,
        },
      },

      accept = {
        auto_brackets = {
          enabled = true,
        },
      },
      menu = {
        draw = {
          treesitter = { "lsp" },
        },
      },
      documentation = {
        auto_show = true,
        auto_show_delay_ms = 200,
      },
      ghost_text = {
        enabled = true,
      },
    },

    signature = {
      enabled = true,
    },
  },
  opts_extend = { "sources.default" },
}
