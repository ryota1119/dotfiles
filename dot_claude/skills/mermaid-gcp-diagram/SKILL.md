---
name: mermaid-gcp-diagram
description: >
  Mermaid Flowchart記法 + Iconifyの`gcp`公式アイコンセットで、テキストベースのGCP構成図を
  生成するスキル。gcloud CLI（Cloud Asset Inventory中心）で実際のリソースを取得し、
  サービスごとのIconifyアイコン画像URLを解決したうえで、GCPコンソールへのディープリンク付き
  Mermaid図を組み立てる。Markdownにそのまま埋め込めてGit差分管理・Notion/Obsidianでの
  ネイティブ表示ができる、既存のdraw.ioベース自動生成チェーン（gcp-architect等）より軽量な
  代替として使う。「GCP構成図を作って」「GCPのインフラ図が欲しい」「GCPのアーキテクチャ図を
  Mermaidで」「この構成をGCPの図にして」「GCP環境を可視化して」等で使う。
  Also triggers on: "GCP構成図", "GCPアーキテクチャ図", "GCPインフラ図", "Mermaidで構成図",
  "GCPの図を書いて", "GCP環境の図".
---

# Mermaid GCP構成図生成スキル

[Qiita記事のAWS向け手法](https://qiita.com/b-mente/items/0172289e5b62645e550c)をGCPへ
適用したもの。Mermaid Flowchart + Iconify画像ノードでGCP構成図を作る。既存の draw.io ベースの
自動生成チェーン（`gcp-architect` → `diagram-reviewer` → drawio-mcp、構成図1枚で約17万トークン
消費する二段エージェント方式）を**置き換えるものではなく**、テキストベースでGit管理・Markdown
埋め込みができる軽量な代替として位置づける。両者は用途が異なるので、精密なレイアウト・既存資産との
形式統一が必要な場合は既存チェーンを案内する。

## このスキルが向く場面 / 向かない場面

- 向く：Markdown/Notion/GitHubにそのまま埋め込みたい、Git差分でレビューしたい、
  トークンを抑えたい、プロジェクト単位の中〜小規模構成を素早く図にしたい。
- 向かない：巨大構成で精密なレイアウトが必要、既存の`gcp-architect`チェーンの資産と
  形式を揃えたい（その場合は既存チェーンを使う）。

## 全体の流れ

```
Step 1  スコープ確認（プロジェクト・リージョン・グルーピング方針）
Step 2  gcloud CLIでリソースを取得（読み取り専用コマンドのみ）
Step 3  サービス→Iconifyアイコンslugを解決
Step 4  Mermaid Flowchartを生成
Step 5  提示・検証（構文チェック・ディープリンクの扱いを明記）
```

---

## Step 1 — スコープ確認

- **単一プロジェクト・単一リージョンに絞る**（AWS版と同じ方針。まずプロジェクト内で
  リージョンを1つに絞る）。複数リージョンが必要な場合は図を分けることを提案する。
- グルーピング方針の既定は **Project → VPC/サブネット → 層（Compute/Data/Network等）** の
  3段階。ユーザーの構成に合わせて層の名前・粒度は調整してよい。
- 対象プロジェクトID・対象範囲が曖昧な場合はここで確認する。既に会話上で明確なら
  確認をスキップしてよい。

## Step 2 — gcloud CLIでリソースを取得

`references/cli.md` に取得コマンドの一覧がある。読み取り専用（`list` / `describe` /
`search-all-resources`）コマンドのみを使い、状態を変更するコマンドは絶対に実行しない。

- 汎用リソース一覧は `gcloud asset search-all-resources` を軸にする（Cloud Asset Inventory）。
- GKE/Cloud Run/Cloud SQL等、個別に詳細情報が必要なリソースは`references/cli.md`の
  個別コマンドで補う。
- `gcloud`の認証アカウント・プロジェクト・リージョンが未設定/不明な場合はユーザーに確認する。
  ここは実インフラへの読み取りアクセスが発生するステップなので、対象プロジェクトが
  曖昧なまま実行しない。
- ユーザーが「このリストから作って」とリソース一覧を直接貼ってきた場合は、CLI実行を
  スキップしてそれを使ってよい。
- 取得対象が広い（プロジェクト全体、複数サービス種別等）場合は、CLI実行と生JSONの整形を
  Agentへ委任し、「サービス種別・ID・名前・関連関係」のみを抽出した圧縮済みリストだけを
  メインへ返させる。生のlist/describe出力をそのままメインの会話に取り込まない。
  対象が単一リソースや少数に絞られている場合はAgentを介さず直接実行してよい。

## Step 3 — サービス→Iconifyアイコンslugを解決

GCPには**公式のIconifyアイコンセット（プレフィックス`gcp`、214アイコン、Apache 2.0）が
存在する**（2026-07-25時点でIconify Collection APIにより実在確認済み）。AWS版と異なり、
主要サービスはこのセット1つでほぼ揃う。`references/icons.md`に確認済みの主要slugがある。

解決の手順：

1. まず `references/icons.md` の一覧に対象サービスがあるか確認する。
2. 無ければ、以下のコマンドで**都度ライブ確認**する（キャッシュされた記憶で slug を
   でっち上げない）。
   ```bash
   curl -s "https://api.iconify.design/collection?prefix=gcp" | python3 -c \
     "import json,sys; print([s for s in json.load(sys.stdin)['uncategorized'] if '<キーワード>' in s])"
   ```
   - **`WebFetch`ツールは `api.iconify.design` / `icon-sets.iconify.design` に対して
     403を返すことを確認済み**（Cloudflareのbot対策と見られる）。ライブ確認は必ず
     Bash 経由の `curl` を使うこと。
3. 見つかったslugは `references/icons.md` に追記し、次回以降の呼び出しで再利用できるようにする。
4. どうしても見つからない場合は汎用ロゴ `logos:google-cloud-platform`（CC0、帰属表示不要）
   を使い、ノードのラベルにサービス名を明記したうえで、最終出力に「専用アイコン未検出」と
   一言注記する。

画像URLは `https://api.iconify.design/gcp/<slug>.svg` の形式。

## Step 4 — Mermaid Flowchartを生成

AWS版と同じ記法を使う。

**アイコンノード**：
```
ノードID@{img: https://api.iconify.design/gcp/compute-engine.svg, label: Compute Engine, pos: b, h: 60, constraint: "on"}
```

**重要**：`w`と`h`を両方指定すると、`constraint`（既定`off`）が縦横比を保持しないため、
subgraph・ラベル幅の都合でノード枠がレイアウトエンジンにより横に広げられた際に**画像が非等比に
引き伸ばされる**（Obsidian特有の不具合ではなくMermaidの仕様）。`h`のみを指定し`constraint: "on"`を
必ず付けて、枠が広がっても縦横比を保つこと。

**グルーピング**（Project → VPC/サブネット → 層の3段階、`subgraph`をネスト）：
```
subgraph Project["GCPプロジェクト"]
  subgraph VPC["VPC (default)"]
    subgraph Network["Network層"]
      lb@{img: ..., label: Load Balancing, pos: b, h: 60, constraint: "on"}
    end
    subgraph Compute["Compute層"]
      gce@{img: ..., label: Compute Engine, pos: b, h: 60, constraint: "on"}
    end
    subgraph Data["Data層"]
      sql@{img: ..., label: Cloud SQL, pos: b, h: 60, constraint: "on"}
    end
  end
end
lb --> gce --> sql
```

**設定**（AWS版と共通、subgraphタイトル重なり対策込み）：
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

**重要**：`subGraphTitleMargin`は既定`{top: 0, bottom: 0}`。3段階ネスト（Project→VPC→層）のように
subgraphを重ねると、タイトル文字の直下に余白が無く、直後のアイコンノードとタイトルが**重なって
表示される**（[mermaid-js/mermaid#7264](https://github.com/mermaid-js/mermaid/issues/7264)等で
報告されている既知の挙動）。`bottom`に余白を持たせて重なりを防ぐこと。

**ディープリンク**（`click`構文）：
```
click gce "https://console.cloud.google.com/compute/instances?project=<project-id>"
```
GCPコンソールのURLはサービスパス＋`?project=<project-id>`という比較的単純な形式が多いが、
一部サービス（VPCサブネット等）はリージョン・リソースIDまで含む形式になる。生成時は
分かる範囲の形式を組み立てるが、**実際にブラウザで開いて遷移することを確認してから**
「動作確認済み」と報告する。未確認のまま「リンクは動きます」と言い切らない。

## Step 5 — 提示・検証

1. 生成したMermaidコードをコードブロックで提示する。
2. 構文上の明らかな誤り（対応していないカッコ、`subgraph`の閉じ忘れ等）がないか読み返す。
3. アイコンが見つからず汎用ロゴで代替した箇所、ディープリンクが未検証の箇所を報告に明記する。
4. 既存の`gcp-architect`（draw.io版）チェーンと比較したい／統合したいという要望が出たら、
   両方式の特性の違い（軽量・Git管理向き vs 精密レイアウト・トークン重め）を説明し、
   統合判断はユーザーに委ねる。
5. ユーザーが希望すれば、Exocortexの`wiki/`（実例として記録する場合）や対象リポジトリへの
   保存を提案する（実際の保存はsecretary/engineeringの承認ルールに従う）。

## 参考

- `references/icons.md` — GCPサービス→Iconify(`gcp`セット)アイコンslugのマッピング表
- `references/cli.md` — gcloud CLIでのリソース取得コマンド一覧
