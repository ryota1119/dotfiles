---
type: reference
updated: 2026-07-25
---

# GCPサービス → Iconify(`gcp`セット)アイコンslug マッピング表

`https://api.iconify.design/gcp/<slug>.svg` の形式でSVG画像URLとして使う。

**確認方法**：`curl -s "https://api.iconify.design/collection?prefix=gcp"`
（2026-07-25、公式GCPアイコンセット・214アイコン・Apache 2.0を実在確認済み）

## 前提

- 出典：Iconify `gcp` コレクション（Google Cloud公式アイコン由来、214アイコン）。
- AWSと違いこのセット1つで主要サービスをほぼ網羅できるが、slug名は必ずしも直感的な
  サービス名と一致しない（例: VPCは`virtual-private-cloud`、Cloud CDNは`cloud-cdn`）。
  表にないサービスは SKILL.md Step 3 の手順でライブ確認し、見つかったらこの表に追記すること。

## 確認済み一覧（2026-07-25時点、主要サービス抜粋）

### Compute / Container / Serverless

| サービス | slug |
|---|---|
| Compute Engine | `compute-engine` |
| GKE (Google Kubernetes Engine) | `google-kubernetes-engine` |
| Cloud Run | `cloud-run` |
| App Engine | `app-engine` |
| Cloud Functions | `cloud-functions` |
| Batch | `batch` |
| GKE on-prem | `gke-on-prem` |
| KubeRun | `kuberun` |
| Container Registry | `container-registry` |
| Artifact Registry | `artifact-registry` |

### Storage / Database

| サービス | slug |
|---|---|
| Cloud Storage | `cloud-storage` |
| Cloud SQL | `cloud-sql` |
| Cloud Spanner | `cloud-spanner` |
| BigQuery | `bigquery` |
| Bigtable | `bigtable` |
| Firestore | `firestore` |
| Datastore | `datastore` |
| Memorystore | `memorystore` |
| Filestore | `filestore` |
| Persistent Disk | `persistent-disk` |
| Local SSD | `local-ssd` |

### Networking

| サービス | slug |
|---|---|
| VPC | `virtual-private-cloud` |
| Cloud Load Balancing | `cloud-load-balancing` |
| Cloud CDN | `cloud-cdn` |
| Cloud DNS | `cloud-dns` |
| Cloud NAT | `cloud-nat` |
| Cloud VPN | `cloud-vpn` |
| Cloud Interconnect | `cloud-interconnect` |
| Cloud Router | `cloud-router` |
| Cloud Armor | `cloud-armor` |
| Network Connectivity Center | `network-connectivity-center` |
| Private Service Connect | `private-service-connect` |
| Traffic Director | `traffic-director` |

### Integration / Messaging / Workflow

| サービス | slug |
|---|---|
| Pub/Sub | `pubsub` |
| Cloud Tasks | `cloud-tasks` |
| Cloud Scheduler | `cloud-scheduler` |
| Workflows | `workflows` |
| Eventarc | `eventarc` |
| Cloud Composer | `cloud-composer` |

### Security / IAM / Ops

| サービス | slug |
|---|---|
| IAM | `identity-and-access-management` |
| Identity-Aware Proxy | `identity-aware-proxy` |
| Identity Platform | `identity-platform` |
| Key Management Service | `key-management-service` |
| Secret Manager | `secret-manager` |
| Certificate Manager | `certificate-manager` |
| Security Command Center | `security-command-center` |
| Cloud Logging | `cloud-logging` |
| Cloud Monitoring | `cloud-monitoring` |
| Cloud Audit Logs | `cloud-audit-logs` |
| Error Reporting | `error-reporting` |
| Trace | `trace` |
| Debugger | `debugger` |
| Profiler | `profiler` |

### Data / Analytics / AI

| サービス | slug |
|---|---|
| Dataflow | `dataflow` |
| Dataproc | `dataproc` |
| Data Fusion | `cloud-data-fusion` |
| Vertex AI | `vertexai` |
| AutoML | `automl` |
| Document AI | `document-ai` |
| Speech-to-Text | `speech-to-text` |
| Text-to-Speech | `text-to-speech` |

### 汎用ロゴ（専用アイコン未検出時のフォールバック）

| 用途 | slug |
|---|---|
| GCP全般ロゴ（`logos`セット・CC0） | `google-cloud-platform`（`logos:google-cloud-platform`） |
| GCPプロジェクト | `project`（`gcp`セット） |

## 追記ログ

- 2026-07-25: 初版作成。上記はすべてIconify Collection APIで実在確認済み。
