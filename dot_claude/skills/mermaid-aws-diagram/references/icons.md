---
type: reference
updated: 2026-07-25
---

# AWSサービス → Iconifyアイコンslug マッピング表

`https://api.iconify.design/logos/<slug>.svg` の形式でSVG画像URLとして使う。

**確認方法**：`curl -s "https://api.iconify.design/search?query=<キーワード>&limit=20&prefix=logos"`
（2026-07-25、`logos:aws-*`で63件ヒットを確認。以下はその時点の実在確認済み一覧）

## 前提

- 出典：Iconify `logos` コレクション（コミュニティ管理、Apache 2.0ベースのSVG Logosセット）。
- AWSには`gcp`のような網羅的な公式Iconifyセットが存在しない
  （[iconify/icon-sets#152](https://github.com/iconify/icon-sets/issues/152)）。
  このため主要サービスはカバーできるが、マイナーサービス・新サービスは都度ライブ確認が必要。
- 表にないサービスは SKILL.md Step 3 の手順でライブ検索し、見つかったらこの表に追記すること。

## 確認済み一覧（2026-07-25時点）

### Compute / Container / Serverless

| サービス | slug |
|---|---|
| EC2 | `aws-ec2` |
| Lambda | `aws-lambda` |
| ECS | `aws-ecs` |
| EKS | `aws-eks` |
| Fargate | `aws-fargate` |
| Elastic Beanstalk | `aws-elastic-beanstalk` |
| Lightsail | `aws-lightsail` |
| Batch | `aws-batch` |
| App Mesh | `aws-app-mesh` |
| OpsWorks | `aws-opsworks` |

### Storage / Database

| サービス | slug |
|---|---|
| S3 | `aws-s3` |
| RDS | `aws-rds` |
| DynamoDB | `aws-dynamodb` |
| Aurora | `aws-aurora` |
| ElastiCache | `aws-elasticache` |
| DocumentDB | `aws-documentdb` |
| Neptune | `aws-neptune` |
| Redshift | `aws-redshift` |
| Keyspaces | `aws-keyspaces` |
| Timestream | `aws-timestream`|
| Glacier | `aws-glacier` |
| Backup | `aws-backup` |
| Lake Formation | `aws-lake-formation` |

### Networking / Delivery

| サービス | slug |
|---|---|
| ELB | `aws-elb` |
| VPC | `aws-vpc` |
| CloudFront | `aws-cloudfront` |
| Route 53 | `aws-route53` |
| API Gateway | `aws-api-gateway` |

### Integration / Messaging

| サービス | slug |
|---|---|
| SNS | `aws-sns` |
| SQS | `aws-sqs` |
| EventBridge | `aws-eventbridge` |
| Step Functions | `aws-step-functions` |
| AppSync | `aws-appsync` |
| AppFlow | `aws-appflow` |
| Kinesis | `aws-kinesis` |
| MQ | `aws-mq` |
| MSK | `aws-msk` |

### Security / IAM / Ops

| サービス | slug |
|---|---|
| IAM | `aws-iam` |
| KMS | `aws-kms` |
| Cognito | `aws-cognito` |
| Secrets Manager | `aws-secrets-manager` |
| Certificate Manager | `aws-certificate-manager` |
| Shield | `aws-shield` |
| WAF | `aws-waf` |
| Systems Manager | `aws-systems-manager` |
| CloudTrail | `aws-cloudtrail` |
| CloudWatch | `aws-cloudwatch` |
| Config | `aws-config` |
| X-Ray | `aws-xray` |

### Analytics / Dev Tools

| サービス | slug |
|---|---|
| Athena | `aws-athena` |
| Glue | `aws-glue` |
| QuickSight | `aws-quicksight` |
| OpenSearch | `aws-open-search` |
| CloudSearch | `aws-cloudsearch` |
| CloudFormation | `aws-cloudformation` |
| CodeBuild | `aws-codebuild` |
| CodeCommit | `aws-codecommit` |
| CodeDeploy | `aws-codedeploy` |
| CodePipeline | `aws-codepipeline` |
| CodeStar | `aws-codestar` |
| Amplify | `aws-amplify` |

### 汎用ロゴ（専用アイコン未検出時のフォールバック）

| 用途 | slug |
|---|---|
| AWS全般ロゴ | `aws` （`logos:aws`） |

## 追記ログ

- 2026-07-25: 初版作成。上記はすべてIconify Search APIで実在確認済み。
