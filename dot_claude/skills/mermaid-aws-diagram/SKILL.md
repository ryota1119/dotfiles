---
name: mermaid-aws-diagram
description: >
  Mermaid Flowchart記法 + Iconifyアイコンで、テキストベースのAWS構成図を生成するスキル。
  AWS CLIで実際のリソースを取得し、サービスごとのIconifyアイコン画像URLを解決したうえで、
  AWSマネジメントコンソールへのディープリンク付きMermaid図を組み立てる。Markdownにそのまま
  埋め込めてGit差分管理・Notion/Obsidianでのネイティブ表示ができる、draw.io系の重い生成チェーン
  より軽量な代替として使う。「AWS構成図を作って」「AWSのインフラ図が欲しい」「AWSのアーキテクチャ図を
  Mermaidで」「この構成をAWSの図にして」「AWS環境を可視化して」等で使う。
  Also triggers on: "AWS構成図", "AWSアーキテクチャ図", "AWSインフラ図", "Mermaidで構成図",
  "AWSの図を書いて", "AWS環境の図".
---

# Mermaid AWS構成図生成スキル

[Qiita記事](https://qiita.com/b-mente/items/0172289e5b62645e550c)で紹介された手法をベースに、
Mermaid Flowchart + Iconify画像ノードでAWS構成図を作る。既存の draw.io ベースの生成チェーン
（構成図1枚で約17万トークン消費する二段エージェント方式）を置き換えるものではなく、
**テキストベースでGit管理・Markdown埋め込みができる軽量な代替**として位置づける。

## このスキルが向く場面 / 向かない場面

- 向く：Markdown/Notion/GitHubにそのまま埋め込みたい、Git差分でレビューしたい、
  トークンを抑えたい、リージョン単位の中〜小規模構成を素早く図にしたい。
- 向かない：巨大構成で精密なレイアウトが必要、既存の draw.io チェーンで作った資産と
  形式を揃えたい（その場合は既存チェーンを使う）。

## 全体の流れ

```
Step 1  スコープ確認（リージョン・対象・グルーピング方針）
Step 2  AWS CLIでリソースを取得（読み取り専用コマンドのみ）
Step 3  サービス→Iconifyアイコンslugを解決
Step 4  Mermaid Flowchartを生成
Step 5  提示・検証（構文チェック・ディープリンクの扱いを明記）
```

---

## Step 1 — スコープ確認

- AWS公式ガイドラインに準拠し、**単一リージョンに絞る**（元記事の方針）。ユーザーが
  複数リージョンを求める場合は、リージョンごとに図を分けることを提案する。
- グルーピング方針の既定は **AWS → VPC → 層（Web/App/Data等）** の3段階。ユーザーの
  構成に合わせて層の名前・粒度は調整してよい。
- 対象を絞る軸（VPC ID、タグ、プロジェクト名など）が曖昧な場合はここで確認する。
  既に会話上で対象が明確なら確認をスキップしてよい。

## Step 2 — AWS CLIでリソースを取得

`references/cli.md` に取得コマンドの一覧がある。読み取り専用（`describe-*` / `list-*` / `get-*`）
コマンドのみを使い、状態を変更するコマンドは絶対に実行しない。

- 汎用リソース一覧は `aws resourcegroupstaggingapi get-resources` を軸にする。
- ELB/EC2/ECS/RDS等、タグ付けされていない・詳細情報が必要なリソースは
  `references/cli.md` の個別コマンドで補う。
- AWS CLIの認証情報・プロファイル・リージョンが未設定/不明な場合はユーザーに確認する。
  ここは実インフラへの読み取りアクセスが発生するステップなので、対象アカウント・
  プロファイルが曖昧なまま実行しない。
- ユーザーが「このリストから作って」とリソース一覧を直接貼ってきた場合は、CLI実行を
  スキップしてそれを使ってよい。
- 取得対象が広い（VPC全体、複数サービス種別等）場合は、CLI実行と生JSONの整形をAgentへ
  委任し、「サービス種別・ID・名前・関連関係」のみを抽出した圧縮済みリストだけを
  メインへ返させる。生のdescribe/list出力をそのままメインの会話に取り込まない。
  対象が単一リソースや少数に絞られている場合はAgentを介さず直接実行してよい。

## Step 3 — サービス→Iconifyアイコンslugを解決

**重要な前提（要確認済み）**：GCPと違い、AWSには網羅的な公式Iconifyセット（`gcp`プレフィックス
のような）は存在しない（[iconify/icon-sets#152](https://github.com/iconify/icon-sets/issues/152)
で要望はあるが未実装）。代わりに `logos` コレクションに `logos:aws-*` / `logos:amazon-*` という
コミュニティ管理のAWSサービスロゴが**63個ほど**存在し、主要サービス（Lambda, S3, EC2, ECS, EKS,
RDS, DynamoDB, CloudFront, CloudWatch, API Gateway, Step Functions, EventBridge, IAM,
Secrets Manager等）はこれでカバーできる。`references/icons.md` に実際にAPIで存在確認済みの
一覧がある。

解決の手順：

1. まず `references/icons.md` の一覧に対象サービスがあるか確認する。
2. 無ければ、以下のコマンドで**都度ライブ確認**する（キャッシュされた記憶で slug を
   でっち上げない — Iconifyのslugは年々増減する）。
   ```bash
   curl -s "https://api.iconify.design/search?query=<サービス名>&limit=20&prefix=logos"
   ```
   - **`WebFetch`ツールは `api.iconify.design` に対して403を返すことを確認済み**
     （Cloudflareのbot対策と見られる）。ライブ確認は必ず Bash 経由の `curl` を使うこと。
3. 見つかったslugは `references/icons.md` に追記し、次回以降の呼び出しで再利用できるようにする
   （このスキルの表は自己成長させる想定）。
4. 適切なslugが見つからない場合は、汎用ロゴ `logos:aws` または `logos:amazon-web-services`
   を使い、ノードのラベルにサービス名を明記したうえで、最終出力に「専用アイコン未検出」と
   一言注記する（黙ってごまかさない）。
5. **`aws-mermaid-icons`のような`mermaid.registerIconPacks()`が必要なカスタムアイコンパック方式は使わない**。
   Obsidian/GitHub/NotionのMermaidレンダラは静的な```mermaid```コードブロックをレンダリング
   するだけで、事前のJS登録処理を実行できないため、そのままでは表示できない。
   本スキルはIconifyの画像URL（`https://api.iconify.design/<prefix>/<slug>.svg`）を
   `img`拡張ノード構文で直接埋め込む方式のみを使う。

## Step 4 — Mermaid Flowchartを生成

元記事の記法をそのまま使う。

**アイコンノード**：
```
ノードID@{img: https://api.iconify.design/logos/aws-lambda.svg, label: Lambda, pos: b, h: 60, constraint: "on"}
```

**重要**：`w`と`h`を両方指定すると、`constraint`（既定`off`）が縦横比を保持しないため、
subgraph・ラベル幅の都合でノード枠がレイアウトエンジンにより横に広げられた際に**画像が非等比に
引き伸ばされる**（Obsidian特有の不具合ではなくMermaidの仕様）。`h`のみを指定し`constraint: "on"`を
必ず付けて、枠が広がっても縦横比を保つこと。

**グルーピング**（AWS → VPC → 層の3段階、`subgraph`をネスト）：
```
subgraph AWS["AWS"]
  subgraph VPC["VPC (10.0.0.0/16)"]
    subgraph Web["Web層"]
      alb@{img: ..., label: ALB, pos: b, h: 60, constraint: "on"}
    end
    subgraph App["App層"]
      ec2@{img: ..., label: EC2, pos: b, h: 60, constraint: "on"}
    end
    subgraph Data["Data層"]
      rds@{img: ..., label: RDS, pos: b, h: 60, constraint: "on"}
    end
  end
end
alb --> ec2 --> rds
```

**設定**（元記事の推奨値＋subgraphタイトル重なり対策）：
```
config:
  theme: neutral
  flowchart:
    nodeSpacing: 10
    rankSpacing: 30
    subGraphTitleMargin:
      top: 5
      bottom: 10
```

**重要**：`subGraphTitleMargin`は既定`{top: 0, bottom: 0}`。3段階ネスト（AWS→VPC→層）のように
subgraphを重ねると、タイトル文字の直下に余白が無く、直後のアイコンノードとタイトルが**重なって
表示される**（[mermaid-js/mermaid#7264](https://github.com/mermaid-js/mermaid/issues/7264)等で
報告されている既知の挙動）。`bottom`に余白を持たせて重なりを防ぐこと。

**ディープリンク**（`click`構文）：
```
click ec2 "https://console.aws.amazon.com/ec2/home?region=<region>#InstanceDetails:instanceId=<id>"
```
AWSコンソールのURL形式はサービスごとに異なり、かつAWS側の仕様変更で変わることがある
（**未検証事項**としてタスクに明記済み）。生成時は分かる範囲の形式を組み立てるが、
**実際にブラウザで開いて遷移することを確認してから**「動作確認済み」と報告する。
未確認のまま「リンクは動きます」と言い切らない。

## Step 5 — 提示・検証

1. 生成したMermaidコードをコードブロックで提示する。
2. 構文上の明らかな誤り（対応していないカッコ、`subgraph`の閉じ忘れ等）がないか読み返す。
3. アイコンが見つからず汎用ロゴで代替した箇所、ディープリンクが未検証の箇所を報告に明記する。
4. ユーザーが希望すれば、Exocortexの`wiki/`（実例として記録する場合）や対象リポジトリへの
   保存を提案する（実際の保存はsecretary/engineeringの承認ルールに従う）。

## 参考

- `references/icons.md` — AWSサービス→Iconifyアイコンslugのマッピング表（API確認済み分＋追記運用）
- `references/cli.md` — AWS CLIでのリソース取得コマンド一覧
