---
type: reference
updated: 2026-07-25
---

# gcloud CLI リソース取得コマンド一覧

すべて**読み取り専用**（`list` / `describe` / `search-all-resources`）。状態を変更する
コマンドはこのスキルの範囲外なので絶対に実行しない。

## 汎用（軸となるコマンド）

```bash
gcloud asset search-all-resources --project=<project-id>
```
Cloud Asset Inventoryでプロジェクト内の全リソースを横断的に一覧取得できる。
まずこれで全体像を掴み、詳細情報が必要なリソースを個別コマンドで補う。
`--asset-types=` でリソース種別を絞り込める（例: `compute.googleapis.com/Instance`）。

## サービス別

| サービス | コマンド |
|---|---|
| Compute Engine (VM) | `gcloud compute instances list --project=<project-id>` |
| VPC / サブネット | `gcloud compute networks list` / `gcloud compute networks subnets list` |
| ロードバランサ | `gcloud compute forwarding-rules list` / `gcloud compute backend-services list` |
| GKE | `gcloud container clusters list --project=<project-id>` |
| Cloud Run | `gcloud run services list --project=<project-id> --region=<region>` |
| Cloud SQL | `gcloud sql instances list --project=<project-id>` |
| Cloud Storage | `gcloud storage buckets list --project=<project-id>` |
| Cloud Functions | `gcloud functions list --project=<project-id>` |
| Pub/Sub | `gcloud pubsub topics list` / `gcloud pubsub subscriptions list` |
| Cloud DNS | `gcloud dns managed-zones list --project=<project-id>` |
| Firewall Rules | `gcloud compute firewall-rules list --project=<project-id>` |

## 実行上の注意

- `--project` を省略するとgcloud設定の既定プロジェクトが使われる。スコープ確認（Step 1）で
  対象プロジェクトが決まったら明示的に渡す。
- リージョン指定が必要なコマンド（Cloud Run等）は `--region` を明示する。
- 出力が大きい場合は `--format` でJSON整形・フィールド抽出をしてよい
  （例: `--format="table(name,zone,status)"`)。
- 認証エラー・権限不足が出た場合はコマンドを繰り返さず、ユーザーに認証アカウント・
  プロジェクトの設定状況を確認する。
