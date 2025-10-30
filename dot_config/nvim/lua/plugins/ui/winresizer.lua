return {
  "simeji/winresizer",
  keys = {
    { "<C-e>", mode = "n", desc = "WinResizer: enter resize mode" },
    -- { "<leader>wr", mode = "n", desc = "WinResizer: enter resize mode" },
  },
  init = function()
    local g = vim.g
    g.winresizer_enable = 1
    g.winresizer_gui_enable = 1
    g.winresizer_finish_with_escape = 1
    g.winresizer_vert_resize = 5
    g.winresizer_horiz_resize = 2

    g.winresizer_start_key = "<C-e>"
    -- 例: <leader>wr にしたい場合
    -- g.winresizer_start_key = "<leader>wr"

    -- キャンセルキー（q以外にしたい場合）
    -- g.winresizer_keycode_cancel = 122   -- 'z' のASCII

    -- 矢印キーでリサイズしたい場合（環境によって効かない端末もある）
    -- g.winresizer_keycode_left  = "<Left>"
    -- g.winresizer_keycode_right = "<Right>"
    -- g.winresizer_keycode_up    = "<Up>"
    -- g.winresizer_keycode_down  = "<Down>"
  end,
}
