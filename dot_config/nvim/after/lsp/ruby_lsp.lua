-- Ruby言語サーバー(ruby_lsp)のカスタム設定
-- masonが入れるruby-lspはshebangにインストール時のruby(4.0.6)が焼き込まれ、
-- プロジェクトのmise.toml/.ruby-versionを無視してbundlerがRubyVersionMismatchで落ちる。
-- miseのshim経由で起動し、カレントディレクトリのruby versionに追従させる。

---@type vim.lsp.Config
return {
  cmd = { vim.fn.expand("~/.local/share/mise/shims/ruby-lsp") },
  settings = {},
}
