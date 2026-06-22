# Architecture

## Design Principle

This lab is not a black-box prediction model. It is an auditable BI transformation from
evidence to sales and renewal decision support.

```text
Synthetic source tables
  accounts / contracts / assets / entitlements / opportunities
  support cases / competitor signals / planted quality manifest
                         |
                         v
DuckDB raw + staging tables
                         |
                         v
Asset reconciliation
  identity / contract / entitlement / freshness / True Forward exposure
                         |
                         v
Planted-signal evaluation
  known defects / recovered defects / recall / FPR
                         |
                         v
Account feature mart
  installed base / lifecycle / renewal / adoption / incident / competition
                         |
                         v
Explainable sales-play scoring
  Modernization / Security / AI Data / Renewal Enterprise Plan
                         |
                         v
Decision support
  priority / NRR / True Forward / calibration / grounded brief / exports
```

## Why DuckDB

DuckDB keeps the demo local, reproducible, and easy to inspect. In production, the same
modeling layers could be implemented in Snowflake, BigQuery, Databricks, Sigma, or a
Salesforce-connected BI stack.

## Data Confidence

Asset reconciliation checks:

- Missing or duplicate serial
- Missing, orphaned, or mismatched contract
- Missing, orphaned, or mismatched entitlement
- True Forward overconsumption where consumed quantity exceeds entitled quantity
- Stale verification

The planted-quality manifest records the expected defect type and expected detection flag.
`quality_signal_metrics` then measures recall and false-positive rate, so the demo can say
how many known defects were recovered rather than only showing `Verified / Unknown` status.

## Revenue Assurance

NRR is decomposed into:

- Opening ARR
- Churn risk
- Contraction risk
- Expansion potential
- Modeled ending ARR

True Forward exposure is calculated from separate `license_quantity` and
`consumed_quantity` fields.

## Model Governance

The scoring layer remains deterministic and explainable:

- Business-owned weights live in `config/scoring.toml`
- Account scoring is generated in `src/saas_insights/scoring.py`
- Forecast calibration compares modeled win probability with Closed Won/Lost outcomes
- Brier score and calibration gap are shown in the governance page

## Grounded Briefing

The public demo implements a deterministic grounded brief draft. It is designed to show
agentic workflow discipline without calling an external model:

- The brief uses account and asset rows already present in the warehouse
- Source row IDs are attached as citations
- `validate_grounding` rejects briefs with unsupported citations
- Pricing, discounting, entitlement actions, and forecast commits remain human-approved

## Governance Boundary

| Layer | Responsibility |
|---|---|
| Deterministic SQL / rules | Reconciliation, feature engineering, scoring, NRR, True Forward exposure |
| Grounded brief | Evidence-cited summary draft only |
| Human approval | Price, discount, forecast commit, customer-facing recommendation |
| Audit | Source record IDs, planted manifest, rule version, score drivers, citations |
