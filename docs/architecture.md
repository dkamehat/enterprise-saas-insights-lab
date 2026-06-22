# Architecture

## Design principle

この環境の中心は「予測モデル」ではなく、**Evidenceから営業判断までの監査可能な変換**です。

```text
Synthetic source tables
    accounts / assets / contracts / entitlements
    support cases / opportunities / competitor signals
                         |
                         v
DuckDB raw + staging tables
                         |
                         v
Asset reconciliation
    uniqueness / completeness / account alignment / staleness
                         |
                         v
Account feature mart
    installed-base / lifecycle / renewal / adoption / incident / competition
                         |
                         v
Explainable sales-play scoring
    Campus / Security / AI DC / Renewal-EA
                         |
                         v
Decision support
    priority / positioning / TCO / NBA / governance / exports
```

## Why DuckDB

ローカルでCSVを直接取り込み、SQL transformationと分析テーブルを一つのファイルで再現しやすいためです。本番ではSnowflake、BigQuery、Databricks等へ置き換えられます。

## Why deterministic scoring first

- Score contributionを営業・Finance・Complianceに説明できる
- 学習データがなくても動く
- データリーケージを避けやすい
- Business ownerがTOMLで重みを変更できる
- 将来のMLモデルに対するChampion baselineになる

## Data confidence

Assetごとに以下を検査します。

- Missing / duplicate serial
- Missing / orphan contract
- Contract-account mismatch
- Missing / orphan entitlement
- Entitlement-account mismatch
- Stale verification

結果は以下へ分類します。

- **Verified**: 定義したIssueがない
- **Reconcilable**: 軽微なIssueで照合可能
- **Unknown**: 主キーまたはAccount alignmentに重大なIssue

Account Data ConfidenceはAsset confidenceの平均です。閾値未満のAccountはForecast Commitから外し、Evidence requiredにします。

## Sales-play scoring

各スコアは0〜100に正規化されたFeatureと、`config/scoring.toml`の重みの加重和です。

### Campus Refresh

- EOL / support transition
- Support gap
- Cisco Network share
- Utilization pressure
- Incident pressure
- Contract fragmentation
- Competitive pressure

### Security Platform

- Security tool sprawl
- Cisco Network share
- Splunk presence
- Security renewal pressure
- Incident pressure
- Competitive pressure
- Contract fragmentation

### AI Data Center

- GPU cluster plan
- AI investment urgency
- Data-center refresh pressure
- High-speed port gap
- Cisco DC share
- Budget readiness
- Competitive pressure

### Renewal / EA

- Renewal value pressure
- Contract fragmentation
- EA eligibility
- Support gap
- Adoption health
- Data confidence
- Competitive pressure

## Governance boundary

| Layer | Responsibility |
|---|---|
| Deterministic SQL / rules | Asset scope, contract alignment, pricing formulas, score components |
| Optional AI | Approved evidence summarization, note classification, briefing draft |
| Human approval | Price, discount, forecast commit, customer-facing recommendation |
| Audit | Source record IDs, rule version, output, reviewer, override reason |

Generative AIをEntitlement、価格、Compliance、Forecast categoryのSource of Truthにはしません。
