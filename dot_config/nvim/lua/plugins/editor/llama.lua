-- ローカル LLM によるインライン補完（AI ゴーストテキスト）。
--
-- 構成:
--   * llama.cpp の llama-server を launchd で常駐させ、FIM の /infill を叩く
--     （plist: ~/Library/LaunchAgents/local.llama-server.plist）
--   * モデルは Qwen2.5-Coder-3B。M5 / 24GB での実測は
--     TTFT 29ms、25トークン 675ms、37 tok/s、RSS 4.3GB。
--     7B は同条件で 17 tok/s しか出ず、25トークンに 1.48秒かかる。
--     llama.vim の既定 t_max_predict_ms = 1000 を超えて提案が打ち切られるため使わない。
--     7B + 0.5B draft の投機的デコーディングは /infill 経路で速度が改善せず、
--     メモリが 4.1GB → 9.1GB に倍増するだけだったので採用しない。
--   * 補完メニュー（LSP / snippet）は blink.cmp、AI の継続予測は llama.vim、と役割を分ける。
--
-- サーバが落ちていても llama.vim は静かに何も出さないだけなので、
-- nvim 側でサーバの生死を気にする必要はない。
return {
  "ggml-org/llama.vim",
  event = "InsertEnter",
  init = function()
    vim.g.llama_config = {
      endpoint_fim = "http://127.0.0.1:8012/infill",
      auto_fim = true,
      show_info = 2,

      -- 既定の accept キーは <Tab> / <S-Tab> だが、これは blink.cmp の
      -- snippet_forward / snippet_backward と衝突する。llama.vim は提案表示中だけ
      -- バッファローカルに <Tab> を上書きするため、AI 提案が出ている瞬間だけ
      -- snippet の tabstop 移動が効かなくなる（実測で確認）。
      -- accept 側を退避させて、<Tab> は blink に残す。
      keymap_fim_accept_full = "<C-l>",
      keymap_fim_accept_line = "<C-k>",
    }
  end,
}
