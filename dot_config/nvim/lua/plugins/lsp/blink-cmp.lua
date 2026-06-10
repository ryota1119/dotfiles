-- blink.cmp の補完設定（2026年版モダン構成）
--
-- スニペット方針:
--   * Neovim 0.10+ のネイティブ vim.snippet を blink.cmp の標準 snippets プリセットで使う
--   * friendly-snippets は壊れた snippet（python tryef 等）が混ざるため不採用
--   * LuaSnip は導入せず、必要なスニペットは LSP（basedpyright/ruff/ts_ls等）に任せる
--   * プロジェクト独自スニペットを置きたい場合は ~/.config/nvim/snippets/ に
--     VSCode形式で置くと自動で読まれる

return {
  "saghen/blink.cmp",
  event = "InsertEnter",
  version = "*",

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
            -- VSCode形式の snippet 探索先。chezmoi管理下のみを既定にして
            -- 想定外の壊れた snippet が混入しないようにする。
            -- VSCodeとユーザースニペットを共有したい場合のみ search_paths に
            --   vim.fn.expand("~/Library/Application Support/Code/User/snippets")
            -- を足す。
            search_paths = { vim.fn.stdpath("config") .. "/snippets" },
          },
        },
      },
    },

    completion = {
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
