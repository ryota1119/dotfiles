return {
  "windwp/nvim-autopairs",
  event = "InsertEnter",
  opts = {
    check_ts = true, -- treesitterと統合
    ts_config = {
      lua = { "string" }, -- Lua文字列内では無効化
      javascript = { "template_string" },
      java = false, -- Javaでは無効化
    },
    disable_filetype = { "TelescopePrompt", "vim" },
    fast_wrap = {
      map = "<M-e>",
      chars = { "{", "[", "(", '"', "'" },
      pattern = [=[[%'%"%>%]%)%}%,]]=],
      end_key = "$",
      keys = "qwertyuiopzxcvbnmasdfghjkl",
      check_comma = true,
      highlight = "Search",
      highlight_grey = "Comment",
    },
  },
  config = function(_, opts)
    local npairs = require("nvim-autopairs")
    npairs.setup(opts)

    -- blink.cmpと統合（補完確定時に括弧を自動挿入）
    local cmp_autopairs = require("nvim-autopairs.completion.cmp")
    local cmp = require("blink.cmp")
    
    -- blink.cmpの確定イベントにフック
    cmp.on_confirm = function()
      cmp_autopairs.on_confirm()
    end
  end,
}
