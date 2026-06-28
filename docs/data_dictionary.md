# Data Dictionary

## Raw entities

### accounts

Account attributes and sales context: industry, business model, sales theater,
sales group, AE, partner, segment, AI-investment horizon, security-tool count, etc.

### assets

The finest grain of the installed base. Asset ID, serial, account, site, vendor,
product family, portfolio domain, deployment model, commercial model, lifecycle,
and contract / entitlement references.

### contracts

Vendor, product family, contract type, start/end, annual value, adoption, and
Enterprise Plan eligibility.

### entitlements

Usage rights tied to an asset: support level, consumption, end date.

### support_cases

Incident severity, open/closed status, resolution hours.

### competitor_signals

Account-level signals such as AE notes, RFPs, PoCs, price quotes, and renewal delays.

### opportunities

Sales play, competitor, stage, amount, quote, discount, forecast category.

### gtm_monthly

Time-aware GTM driver panel (a `Company` roll-up plus per-segment rows, 42 months).
Holds monthly new / expansion / contraction / churn ARR, revenue, COGS, S&M / R&D /
G&A, customers, the funnel (MQL/SQL/opportunities/won/lost), pipeline, and quota.
Generated deterministically in `src/saas_insights/gtm.py`.

## Core analytical tables

### asset_reconciliation

Key columns:

- `reconciliation_status`
- `asset_data_confidence_pct`
- `issue_count`
- `issue_summary`
- individual issue flags

### account_features

Account-level features:

- installed base / primary vendor share
- lifecycle transition / support gap / data throughput
- portfolio domain count / deployment model count
- physical or hybrid mix / software subscription mix
- renewal value / fragmentation / adoption
- incident pressure
- competitor pressure
- pipeline and quote variance
- data confidence

### gtm_monthly_metrics / gtm_company_monthly

GTM economics mart (reconstructed from drivers by `compute_gtm_metrics`):

- ARR / net new ARR / YoY growth
- NRR / GRR (TTM)
- gross margin / operating margin / Rule of 40
- Magic Number / CAC / CAC payback / LTV / LTV·CAC / burn multiple
- pipeline coverage / win rate / quota attainment

`gtm_company_monthly` is the Company roll-up; `gtm_segment_latest` is the latest
month by segment.

### account_positioning

Sales decision-support mart:

- per-sales-play score
- `recommended_play`
- `primary_competitor`
- `priority_score` / `priority_band`
- `estimated_tcv_jpy_mn`
- `expected_commercial_value_jpy_mn`
- `score_drivers_json`
- `positioning_angle`
- `next_best_action`
- `governance_status`
