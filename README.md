# dotfiles

[chezmoi](https://www.chezmoi.io/) で複数マシンへ同期する個人のdotfiles。

zsh、Neovim、Git、Ghostty、lazygit、cmux、および Claude Code の
スキル・エージェント定義を管理する。

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
| Claude Code backend | `anthropic` または `openrouter`。下記参照 |
| 1Password path (OpenRouter API key) | backend が `openrouter` のときだけ使われる |

回答を変更したいときは `~/.config/chezmoi/chezmoi.toml` を直接編集する。
`promptStringOnce` は保存済みの値を優先するため、CLIフラグでは上書きされない。

## Claude Code のバックエンド切り替え

Claude Code CLI は Anthropic Messages API 互換のエンドポイントであれば
接続先を差し替えられる。skills・subagents・`CLAUDE.md` といった資産は
モデル非依存なので、そのまま別プロバイダのモデルで動く。

`ai.provider` の値で挙動が決まる。

### `anthropic`（既定）

AI関連の環境変数を**一切exportしない**。Claude Code は純正のまま動く。
質問に答え損ねても既定値でこちらに倒れる。

### `openrouter`

`.zsh/env.zsh` に接続先とモデルの指定が出力され、OpenRouter 経由になる。
APIキーはシェル環境に常駐させず、`claude` 起動時に 1Password から解決する
（`.zsh/functions.zsh` のラッパー関数）。

適用手順:

1. 1Password に OpenRouter の API キーを登録する
2. OpenRouter にクレジットをチャージする
   （クレジット購入には手数料がかかり最低額もあるため、小刻みなチャージは不利）
3. `chezmoi update` を実行し、backend の質問に `openrouter` と答える
4. シェルを読み込み直し、`claude` を起動して `/status` で接続先を確認する
5. `~/.claude/settings.json` の `model` をプロバイダのモデル slug に変更する
   （このファイルは chezmoi 管理外なので手動）

補助関数として `claude-anthropic` を用意している。ゲートウェイ経由のまま
Anthropic のモデルで起動したいときに使う。

### 設定してはいけない環境変数

差し替え手順を公開しているベンダーの設定例には、次の2つが含まれていることがある。
**このリポジトリでは意図的に設定していない。**

- `CLAUDE_CODE_SUBAGENT_MODEL` — subagent 定義の frontmatter の `model` と
  Agent ツールの `model` パラメータを上書きする
- `CLAUDE_CODE_EFFORT_LEVEL` — skill / subagent の frontmatter の `effort` を上書きする

`dot_claude/agents/*.md` は工程ごとに `model` と `effort` を作り分けているため、
これらを設定すると設計が丸ごと潰れる。しかも**エラーは出ず、出力は一見
もっともらしいまま**なので気づけない。

正しい対処は `ANTHROPIC_DEFAULT_SONNET_MODEL` などの**エイリアス解決を経由させる**こと。
既存の `model: sonnet` 指定がそのまま活きる。

## 構成

```
.chezmoi.toml.tmpl        初回の質問と、マシンごとに保持する値
.chezmoiignore            chezmoi 管理から外すファイル
dot_zsh/                  zsh 設定（env / alias / functions / prompt / completion / fzf）
dot_claude/               Claude Code の skills と agents
dot_config/               nvim, git, ghostty, lazygit, cmux
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
