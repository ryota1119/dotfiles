# dotfiles

[chezmoi](https://www.chezmoi.io/) で複数マシンへ同期する個人のdotfiles。

zsh、Neovim、Git、Ghostty、lazygit、cmux、Claude Code の
スキル・エージェント定義、および OpenCode のグローバル設定・MCP・Agentを管理する。

## Setup

新しいマシンでは次の1コマンドで取得から適用まで行う。

```sh
chezmoi init --apply git@github.com:ryota1119/dotfiles.git
```

初回だけ以下を質問される。回答は `~/.config/chezmoi/chezmoi.toml`
（chezmoi管理外）へ保存され、以降は再質問されない。

| 質問 | 意味 |
| --- | --- |
| 1Password account | `op read` に渡すアカウント。複数アカウントへ同時サインインしていると `account` 未指定では `multiple accounts found` になるため必須 |
| 1Password path (git username / email / SSH signing key) | Git identity の取得元。マシンごとに使い分ける |

回答を変更したいときは `~/.config/chezmoi/chezmoi.toml` を直接編集する。
`promptStringOnce` は保存済みの値を優先するため、CLIフラグでは上書きされない。

## 構成

```
.chezmoi.toml.tmpl        初回の質問と、マシンごとに保持する値
.chezmoiignore            chezmoi 管理から外すファイル
dot_zsh/                  zsh 設定（env / alias / functions / prompt / completion / fzf）
dot_claude/               Claude Code の skills と agents
dot_config/               nvim, git, ghostty, lazygit, cmux, opencode
```

`*.tmpl` は Go template として展開される。OS・アーキテクチャ差の吸収と、
マシンごとの分岐に使っている。

## 秘匿情報の扱い

**このリポジトリは public なので、秘匿情報を含むファイルは追跡しない。**

- APIキー・トークン・認証情報の実値は置かない。1Password の参照パスを
  `~/.config/chezmoi/chezmoi.toml`（管理外）に保持し、実値は実行時に `op read` で解決する
- 認証情報を含みうるファイルは `.chezmoiignore` で管理外にする（`gh` の `hosts.yml` など）
- `~/.claude/settings.json` は管理対象に含めていない。マシン固有の設定と
  資格情報が混ざるため

なお**シェル設定一式は管理対象**である。「秘匿情報はシェルプロファイルへ」という
一般的な助言はこの構成では成立せず、書けば全マシンへ伝播する。
マシン固有の値を置く場所を選ぶときは、ファイルの性質から推測せず
`chezmoi managed` で管理対象を確認すること。

## OpenCode

`dot_claude/skills`はClaude CodeとOpenCodeで共用する。ランタイム固有のAgent、モデル、ツールは
実行時に利用可否を確認し、専用Agentが利用できない場合はメインセッションで直接実行する。

MCPは Google Calendar、Gmail、Google Drive、Playwright、X API、Hacker News、
Qiita、Zenn、Socialdataの9個を設定している。

Google系MCPのOAuth認証は、chezmoi適用後に各マシンで実行する。

```sh
opencode mcp auth google-calendar
opencode mcp auth gmail
opencode mcp auth google-drive
```

X API MCPには環境変数 `CLIENT_ID` と `CLIENT_SECRET` が必要である。
実値はdotfilesへ保存しない。

Socialdata MCPには環境変数 `SOCIALDATA_API_KEY` が必要である。実値はdotfilesへ保存しない。

Hacker News、Qiita、Zenn、SocialdataのローカルMCPは、それぞれ
`~/Workspace/repos/github.com/RayLabOrg/` 配下の `hn-mcp`、`qiita-mcp`、
`zenn-mcp`、`socialdata-mcp` を利用する。新しいマシンでは
workstation-provisioningの`workspace-repositories`ロールが、これらをghq配下へclone/更新し、
`uv sync --frozen`で依存関係を復元する。

設定、Agent定義、共用スキルは次のコマンドで検証する。

```sh
tests/test-opencode-config.sh
tests/test-shared-skills.sh
```
