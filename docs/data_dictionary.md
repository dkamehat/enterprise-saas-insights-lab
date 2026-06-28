# Data Dictionary

## Raw entities

### accounts

Account属性、Industry、Business model、Sales theater、Sales group、AE、Partner、
Segment、AI投資時期、Security tool数などの営業コンテキスト。

### assets

Subscription inventoryの最小粒度。Asset ID、Serial、Account、Site、Vendor、Product family、
Portfolio domain、Deployment model、Commercial model、Lifecycle、Contract / Entitlement参照を持つ。

### contracts

Vendor、Product family、Contract type、Start / End、Annual value、Adoption、Enterprise Plan eligibility。

### entitlements

Assetに紐づく利用権、Support level、Consumption、End date。

### support_cases

障害Severity、Open / Closed、Resolution hours。

### competitor_signals

AE note、RFP、PoC、Price quote、Renewal delay等のAccount-level signal。

### opportunities

Sales Play、Competitor、Stage、Amount、Quote、Discount、Forecast category。

### gtm_monthly

時間軸を持つGTMドライバーパネル（`Company` ロールアップ + Segment別、42ヶ月）。
new / expansion / contraction / churn ARR、revenue、COGS、S&M / R&D / G&A、
customers、ファネル（MQL/SQL/opportunities/won/lost）、pipeline、quota を月次で保持。
`src/saas_insights/gtm.py` で決定論的に生成。

## Core analytical tables

### asset_reconciliation

主な列：

- `reconciliation_status`
- `asset_data_confidence_pct`
- `issue_count`
- `issue_summary`
- 各Issue flag

### account_features

Account単位の特徴量：

- Subscription inventory / primary vendor share
- Lifecycle transition / support gap / data throughput
- Portfolio domain count / deployment model count
- Physical or hybrid mix / software subscription mix
- Renewal value / fragmentation / adoption
- Incident pressure
- Competitor pressure
- Pipeline and quote variance
- Data confidence

### gtm_monthly_metrics / gtm_company_monthly

GTM経済性Mart（`compute_gtm_metrics` がドライバーから再構成）：

- ARR / net new ARR / YoY growth
- NRR / GRR（TTM）
- gross margin / operating margin / Rule of 40
- Magic Number / CAC / CAC payback / LTV / LTV·CAC / burn multiple
- pipeline coverage / win rate / quota attainment

`gtm_company_monthly` は Company ロールアップ、`gtm_segment_latest` は最新月のSegment別。

### account_positioning

営業意思決定用Mart：

- 各Sales Play score
- `recommended_play`
- `primary_competitor`
- `priority_score` / `priority_band`
- `estimated_tcv_jpy_mn`
- `expected_commercial_value_jpy_mn`
- `score_drivers_json`
- `positioning_angle`
- `next_best_action`
- `governance_status`
