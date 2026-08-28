-- ローカル LLM によるインライン補完（AI ゴーストテキスト）。
--
-- 構成:
--   * llama.cpp の llama-server を launchd で常駐させ、FIM の /infill を叩く
--     （plist は ansible の launchd role が配布する。ポートは 8012 で、
--      workstation-provisioning の group_vars/all.yml の llama_server_port と
--      揃える必要がある。片方だけ変えると接続できなくなる）
--   * モデルは Qwen2.5-Coder-3B。M5 / 24GB での実測は
--     TTFT 29ms、25トークン 675ms、37 tok/s、RSS 2.0GB。
--     7B は同条件で 17 tok/s しか出ず、25トークンに 1.48秒かかる。
--     llama.vim の既定 t_max_predict_ms = 1000 を超えて提案が打ち切られるため使わない。
--     7B + 0.5B draft の投機的デコーディングは /infill 経路で速度が改善せず、
--     メモリが 4.1GB → 9.1GB に倍増するだけだったので採用しない。
--   * 補完メニュー（LSP / snippet）は blink.cmp、AI の継続予測は llama.vim、と役割を分ける。
--
-- サーバが落ちていても llama.vim は静かに何も出さないだけなので、
-- nvim 側でサーバの生死を気にする必要はない。
--
-- キーマップの方針:
--   llama.vim は提案表示中だけバッファローカルに inoremap を張り、提案を消すときに
--   `iunmap <buffer>` で外す（autoload/llama.vim:236-252）。この iunmap は
--   「llama.vim が張ったマップ」ではなく「そのキーのバッファローカルマップ」を消すため、
--   他が張ったバッファローカルの挿入モードマップを巻き添えで恒久的に破壊する。
--   したがって、他とぶつかるキーは llama.vim に渡してはいけない。
--   空文字を渡すとその機能のマップ自体を張らない（同 1485-1500 行）。
return {
  "ggml-org/llama.vim",
  event = "InsertEnter",
  init = function()
    vim.g.llama_config = {
      endpoint_fim = "http://127.0.0.1:8012/infill",
      auto_fim = true,
      show_info = 2,

      -- 提案の採用。既定は <Tab> だが、それは blink.cmp の snippet_forward と
      -- 衝突し、AI 提案が出ている瞬間だけ snippet の tabstop 移動が効かなくなる。
      -- <C-l> は挿入モードでは誰も使っていない（実 config の <C-l> は
      -- ノーマルモードのウィンドウ移動のみ）ので安全。
      keymap_fim_accept_full = "<C-l>",

      -- 以下は割り当てず無効化する。既定値が実 config と衝突し、
      -- 上記の iunmap によって相手側のマップを恒久的に壊すため。
      --   accept_line 既定 <S-Tab> … blink.cmp の snippet_backward
      --   fim_prev    既定 <C-K>   … lua/config/lsp.lua の signature_help
      --                              （vim.keymap.set に buffer = buf 指定あり）
      --   fim_next    既定 <C-J>   … prev だけ無効だと非対称なので揃えて無効化
      -- 使いたくなったら、他とぶつからない空きキーを選んで割り当てる。
      keymap_fim_accept_line = "",
      keymap_fim_next = "",
      keymap_fim_prev = "",
    }
  end,
}
