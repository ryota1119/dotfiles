# dotfiles

[chezmoi](https://www.chezmoi.io/) で複数マシンへ同期する個人のdotfiles。

zsh、Neovim、Git、Ghostty、lazygit、cmux、Claude Code の
スキル・エージェント定義、および OpenCode・Codex CLI のグローバル設定・MCP・Agentを管理する。

## Setup

新しいマシンでは次の1コマンドで取得から適用まで行う。

```sh
chezmoi init --apply git@github.com:ryota1119/dotfiles.git
```

初回だけ以下を質問される。回答は `~/.config/chezmoi/chezmoi.toml`
（chezmoi管理外）へ保存され、以降は再質問されない。

| 質問 | 意味 |
| --- | --- |
| 1Password account for op://Personal references | `op://Personal/...` を引くときに `op read` へ渡すアカウント。個人アカウントを指定する |
| 1Password account for git identity | Git identity を引くときのアカウント。会社PCでは会社アカウントを指定する |
| 1Password path (git username / email / SSH signing key) | Git identity の取得元。マシンごとに使い分ける |

アカウント指定を2つに分けているのは、git identity は会社アカウント・MCPの認証情報は
個人アカウントのPersonalボルト、というマシンがあるため。1つの変数では両立できない。

回答を変更したいときは `~/.config/chezmoi/chezmoi.toml` を直接編集する。
`promptStringOnce` は保存済みの値を優先するため、CLIフラグでは上書きされない。

## 構成

```
.chezmoi.toml.tmpl        初回の質問と、マシンごとに保持する値
.chezmoiignore            chezmoi 管理から外すファイル
dot_zsh/                  zsh 設定（env / alias / functions / prompt / completion / fzf）
dot_claude/               Claude Code の skills と agents
dot_config/               nvim, git, ghostty, lazygit, cmux, opencode
dot_agents/               Codex CLI が読む user-level skills（`~/.claude/skills`へのsymlink）
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

X API MCPの`CLIENT_ID`/`CLIENT_SECRET`、Socialdata MCPの`SOCIALDATA_API_KEY`は、
`dot_config/opencode/private_opencode.jsonc.tmpl`内で`onepasswordRead`により1Passwordから
解決される（`chezmoi apply`のたびに再解決されるため、ローテーション後は1Password側を
更新してから`chezmoi apply`するだけでよい）。参照先は個人アカウントのPersonalボルトなので、
アカウント指定には`personalOnepasswordAccount`を使う。

実値はchezmoi source（git管理下）へは保存しないが、適用先の
`~/.config/opencode/opencode.jsonc`には平文で書き込まれる（OpenCodeが`{env:VAR}`形式でしか
環境変数を解決できず、その環境変数を常時供給する手段を別途持たないため）。平文が残ることを
前提に、ソース側を`private_`プレフィックスにしてモード0600で展開する。

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

## Claude Code

`~/.claude.json`はchezmoi管理外（Claude Code自身の内部状態ファイル）のため、MCPは
`claude mcp add`で登録する。シークレットは1Passwordから読み、登録するスクリプトを
`scripts/setup-claude-mcp.sh`に用意している。

```sh
bash scripts/setup-claude-mcp.sh
```

- `xapi`（userスコープ、全プロジェクト共通）：1Password「X Developer Client Secret」
  （Personal）
- `xserver`（localスコープ、shino_music_school案件固有）：1Password「Xserver」
  （**Development**ボルト。案件固有クレデンシャルは`Muumuu-domain`とあわせて
  Personalから移動済み）。対象リポジトリが存在しない場合は登録をスキップする

## Codex CLI

CodexはOpenCodeと異なり`~/.claude/skills/`を直接読まず、`~/.agents/skills/`
（user-level）と各プロジェクトの`.agents/skills/`（repo rootまで遡って探索）しか見ない。
そのため`dot_agents/skills/`配下にchezmoiの`symlink_`機構でsecretary / pm / research /
marketing / engineeringへのsymlinkを配置し、`~/.agents/skills/{同名}`として
実体化させている。

MCPは`~/.codex/config.toml`を直接編集せず、`codex mcp add`で登録する。
`~/.codex/config.toml`はChatGPT Desktopアプリと共有する実行時状態ファイル
（projects/marketplaces/hooks.state等を含む）のため、chezmoiでは管理しない。

6件すべて登録済み。シークレットは1Passwordから読み、`codex mcp add`で登録する
スクリプトを`scripts/setup-codex-mcp.sh`に用意している（`scripts/`はchezmoi管理外の
セットアップ用ディレクトリ、`.chezmoiignore`参照）。新しいマシンでの初回セットアップ、
シークレットローテーション後の再登録どちらもこのスクリプト再実行だけで済む。

```sh
bash scripts/setup-codex-mcp.sh
```

xapiは1Password「X Developer Client Secret」（Personal）、socialdata-mcpは
「SocialData」（Personal）の`api_key`フィールドを参照する。どちらも個人アカウント側の
ボルトなので、`op read`には個人アカウントを渡す必要がある。

Google Calendar/Gmail/Google Drive（remote MCP）はOpenCode専用の組み込みOAuthクライアントに
依存しており、Codex側で同等の認証経路が未確認のため対象外。Notionも従来通り対象外。

claude-obsidianの15 skillはchezmoi管理に含めず、
`~/Workspace/repos/github.com/AgriciDaniel/claude-obsidian/bin/setup-multi-agent.sh`
を新しいマシンで実行して揃える（OpenCode側`~/.config/opencode/skills/`と同じ方針）。

```sh
bash bin/setup-multi-agent.sh --host codex --apply
bash bin/setup-multi-agent.sh --host codex --check
```
