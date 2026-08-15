# X（旧Twitter）投稿の実務リファレンス

marketingスキルがX投稿を制作・実行する際に参照する。ここは実務詳細のみを扱う。
戦略・企画・承認ルールはSKILL.md本体を正とする。

## アカウントと認証

- 運用アカウント：`@RayLab`
- 接続に使うXアプリ：`opencode-x-mcp`（X Developer Portal `console.x.com`に登録済み）
- 認証方式：OAuth 2.0ユーザートークン（`tweet.write`を含むread-writeスコープ）
- 認証情報の保存場所：`~/.xurl/auth.yml`（`client_id`/`client_secret`/`access_token`/
  `refresh_token`）。トークンの更新は`xurl`が自動で行う。
- Claude Codeに設定済みの読み取り専用MCP（`mcp__xapi__*`）とは別物。読み取り専用MCPは
  X公式ホストMCP（`api.x.com/mcp`）経由で、投稿系ツールを一切公開していない
  （2026-08時点で実機確認済み。詳細はexocortex
  `wiki/sources/x-official-mcp-servers-2026-08.md`）。

## 実行コマンド

投稿・削除は`xurl`（`@xdevplatform/xurl`、X公式CLI）をBash経由で直接叩く。MCPツール化は
していない（2026-08時点、意図的に見送り。頻度が上がれば再検討）。

```bash
# 投稿
npx -y @xdevplatform/xurl -X POST /2/tweets -d '{"text":"投稿本文"}'

# 削除（投稿時に返るidを使う）
npx -y @xdevplatform/xurl -X DELETE /2/tweets/<id>
```

これらのコマンドは`~/.claude/settings.json`の`permissions.ask`に登録済みで、
auto modeでも分類器を経由せず必ず確認プロンプトが出る（2026-08-16設定）。
`xurl post/delete/reply/quote/repost`のショートカット形式も同様に登録済み。

**このゲートを外部発信の唯一の技術的強制力として扱う。** SKILL.mdの承認ルールは
運用上の手順であり、実際に実行を止めるのはこの`permissions.ask`登録である。

## 投稿本文の制約

- **文字数上限は280（加重カウント）**。日本語・中国語・韓国語（CJK）の文字と絵文字は
  1文字あたり重み2でカウントされるため、**日本語のみの本文では実質140文字が上限**。
  英数字・半角記号は重み1。
- **リンクは実際の長さに関わらずt.coで23文字固定**として加重される。
- 上記はXの無料/Basicティアの標準仕様。`@RayLab`がX Premiumでロング投稿
  （最大25,000文字）に対応しているかは未確認。不明な場合は280加重を前提にする。
- ドラフト作成の時点で文字数（加重）を意識する。公開前チェックで初めて超過に
  気づく設計にしない。

## 失敗時の扱い

- **投稿系コマンドは失敗時に自動リトライしない。** タイムアウトしても実際には
  投稿が成立している場合があり、機械的な再送信は二重投稿を招く。
- タイムアウトやエラーが出た場合は、まず`get_users_posts`等の読み取りツールで
  実際に投稿が成立しているか確認してから、次の対応（再送 or 報告）を判断する。

## 誤投稿からの復旧

- 投稿直後に返る`id`を必ず保持する。
- 取り消す場合は`npx -y @xdevplatform/xurl -X DELETE /2/tweets/<id>`を実行する
  （このコマンドも`permissions.ask`の対象なので確認プロンプトが出る）。
- 削除後は`get_posts_by_id`等で実際に削除されたことを確認できる
  （削除済みの投稿IDは`Not Found Error`を返す）。

## 経緯・関連情報

- xmcpセルフホスト・OAuth1・launchd常駐という初期案は、Opusによるセカンドオピニオン
  レビューで「前提が誤り」と指摘され撤回した。X APIはOAuth2ユーザートークンで
  `POST /2/tweets`を正式サポートしており、既存の`~/.xurl/auth.yml`のトークンで
  追加インフラなしに投稿できることを実機確認済み（2026-08）。
- 詳細な調査経緯はexocortex `wiki/sources/x-official-mcp-servers-2026-08.md`を参照。
