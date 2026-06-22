# Enterprise SaaS Insights Lab

An explainable BI lab for a synthetic enterprise SaaS portfolio. It models account
prioritization, installed-base reconciliation, entitlement usage, renewal economics,
competitive pressure, and governed sales-play recommendations without using employer,
customer, pricing, or production platform data.

## What It Demonstrates

- Large synthetic account, contract, asset, entitlement, support, opportunity, and signal data
- Planted-signal manifest for known data-quality defects
- Recall and false-positive-rate measurement for asset reconciliation logic
- Sales plays:
  - Platform Modernization
  - Security Platform
  - AI Data Platform
  - Renewal / Enterprise Plan
- NRR decomposition across churn risk, contraction risk, and expansion potential
- True Forward style exposure using separate entitled and consumed quantities
- Forecast calibration with Brier score and probability-bucket comparison
- Grounded account briefing with source-row citations and a grounding test
- Vendor-neutral interview lens for enterprise SaaS / networking portfolio roles

All generated data is synthetic. The project intentionally avoids real vendor names,
customer names, production pricing, credentials, internal KPI labels, and live adapters.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42
python -m saas_insights.cli export
streamlit run app.py
```

Open `http://localhost:8501`.

## Demo Pages

1. **Executive Portfolio**: prioritize accounts by expected commercial value,
   sales play, segment, sales team, and forecast readiness.
2. **Account 360**: inspect a single account's recommended play, score drivers,
   data story, TCO scenario, and asset evidence.
3. **Competitive Positioning**: compare sales-play fit with competitive pressure.
4. **Data Quality**: audit planted-signal recall, FPR, reconciliation status,
   source-system quality, and evidence queues.
5. **Model Governance**: review weights, decision boundaries, calibration,
   grounded brief drafts, and human approval controls.
6. **Dataset Blueprint**: inspect ER-style relationships, table grain, row counts,
   and physical schema.
7. **Formula Appendix**: document formulas, assumptions, and guardrails.
8. **Revenue Assurance**: decompose NRR and inspect True Forward exposure.

## CLI

```bash
saas-insights bootstrap --accounts 250 --assets 25000 --seed 42
saas-insights build
saas-insights validate
saas-insights export
pytest
ruff check .
```

## Public Safety

- Synthetic names and values only
- No consumer rows, employee PII, credentials, or live endpoints
- No production pricing, discount policy, entitlement authority, or forecast authority
- Generated CSV and DuckDB outputs are ignored by git
- Grounded brief is deterministic in the public demo and cites source row IDs

## Main Artifacts

- `data/warehouse/sales_insights.duckdb`
- `outputs/account_playbook.csv`
- `outputs/data_quality_summary.csv`
- `outputs/renewal_pipeline.csv`

## Repository Layout

```text
config/             Business-owned weights and thresholds
sql/                Staging, reconciliation, feature models, and views
src/saas_insights/  Generator, pipeline, scoring, briefing, recommendations, TCO
pages/              Streamlit decision-support pages
tests/              Unit and integration tests
docs/               Architecture, data dictionary, demo guide
```
