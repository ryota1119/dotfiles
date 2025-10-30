return {
  "christoomey/vim-tmux-navigator",
  cmd = {
    "TmuxNavigateLeft",
    "TmuxNavigateDown",
    "TmuxNavigateUp",
    "TmuxNavigateRight",
    "TmuxNavigatePrevious",
    "TmuxNavigatorProcessList",
  },
  keys = {
    { "<c-h>", "<cmd><C-U>TmuxNavigateLeft<cr>", desc = "Tmux Navigate Left" },
    { "<c-j>", "<cmd><C-U>TmuxNavigateDown<cr>", desc = "Tmux Navigate Down" },
    { "<c-k>", "<cmd><C-U>TmuxNavigateUp<cr>", desc = "Tmux Navigate Up" },
    { "<c-l>", "<cmd><C-U>TmuxNavigateRight<cr>", desc = "Tmux Navigate Right" },
    -- <C-\> はtoggletremと衝突するため <leader>tp に変更
    { "<leader>tp", "<cmd><C-U>TmuxNavigatePrevious<cr>", desc = "Tmux Navigate Previous" },
  },
}
