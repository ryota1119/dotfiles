---
type: reference
updated: 2026-07-25
---

# AWS CLI リソース取得コマンド一覧

すべて**読み取り専用**（`describe-*` / `list-*` / `get-*`）。状態を変更するコマンドは
このスキルの範囲外なので絶対に実行しない。

## 汎用（軸となるコマンド）

```bash
aws resourcegroupstaggingapi get-resources --region <region>
```
タグ付けされたリソースを横断的に一覧取得できる。まずこれで全体像を掴み、
タグが付いていない/詳細情報が必要なリソースを個別コマンドで補う。

## サービス別

| サービス | コマンド |
|---|---|
| EC2 | `aws ec2 describe-instances --region <region>` |
| VPC | `aws ec2 describe-vpcs --region <region>` / `describe-subnets` |
| ELB (ALB/NLB) | `aws elbv2 describe-load-balancers --region <region>` |
| ECS | `aws ecs list-clusters --region <region>` → `describe-clusters` / `list-services` |
| EKS | `aws eks list-clusters --region <region>` → `describe-cluster` |
| Lambda | `aws lambda list-functions --region <region>` |
| RDS | `aws rds describe-db-instances --region <region>` |
| DynamoDB | `aws dynamodb list-tables --region <region>` |
| S3 | `aws s3api list-buckets`（バケットはグローバル。リージョンは`get-bucket-location`で確認） |
| CloudFront | `aws cloudfront list-distributions`（グローバルサービス） |
| Route 53 | `aws route53 list-hosted-zones`（グローバルサービス） |
| API Gateway | `aws apigateway get-rest-apis --region <region>` |

## 実行上の注意

- `--region` を省略するとCLI設定の既定リージョンが使われる。スコープ確認（Step 1）で
  対象リージョンが決まったら明示的に渡す。
- `--profile <name>` でプロファイルを切り替えられる。対象アカウントが複数ある場合は
  ユーザーに確認する。
- 出力が大きい場合は `--query` でJMESPathフィルタをかけ、必要な項目だけ抽出してよい
  （例: `--query 'Reservations[].Instances[].{Id:InstanceId,Type:InstanceType}'`）。
- 認証エラー・権限不足が出た場合はコマンドを繰り返さず、ユーザーに認証情報の設定状況を確認する。
