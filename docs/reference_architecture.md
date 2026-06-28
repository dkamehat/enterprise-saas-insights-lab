# Reference Architecture — a unified, time-aware GTM analytics backbone

This document describes how the lab would run in a real Strategy & Operations
org, and why it is built the way it is. The repository is the **local, zero-cost
emulation** of that architecture: DuckDB stands in for BigQuery and runs the
identical SQL models, so the design is demonstrable without any cloud spend.

## Principle: model once, deliver everywhere, agree always

```
SOURCES                  BACKBONE (BigQuery / DuckDB)            SURFACES
CRM (opportunities) ─┐   raw_*  ──►  staging  ──►  marts ──┬──► Looker      (execs/analysts)
Contracts / billing ─┤              (clean,        (account ├──► Streamlit   (analysts)
Install base / usage ─┤              typed,         + GTM    ├──► Apps Script (operations)
Support / signals ───┘              conformed)     economics)└──► AppSheet    (field sales)
                                         │
                                         └── governance: planted-defect audit,
                                             score drivers, calibration, citations
```

Every metric (ARR, NRR/GRR, Rule of 40, Magic Number, CAC payback, LTV/CAC) is
defined **once** in the marts layer (`sql/` + `src/saas_insights/gtm.py`). Looker
LookML, the Streamlit pages, the Apps Script web app, and the AppSheet app all
*read* those definitions. No surface recomputes a KPI, so no two surfaces can
disagree.

## Layers

| Layer | In this repo | In production |
|---|---|---|
| Ingestion | `data_generator.py` (synthetic) | Fivetran / scheduled loads / streaming |
| Raw | `raw_*` tables | BigQuery raw dataset |
| Staging | `sql/01_staging.sql` | dbt staging models |
| Conformed marts | `sql/02–04`, `gtm.py` | dbt marts on BigQuery |
| Semantic layer | metric definitions in marts | Looker (`delivery/looker/`) |
| Delivery | `pages/`, `delivery/` | Looker / AppSheet / Apps Script |
| Orchestration | `cli.py`, `Makefile` | Cloud Composer / scheduled dbt |

## Time-aware by design

A single-snapshot warehouse can answer "what is true now" but not "what changed
and why" — the questions S&O actually gets asked. The model carries time on two
tracks:

1. **As-of point-in-time facts** (`AS_OF_DATE`): the account portfolio is
   reconciled to a stated date, so renewals, EOL windows, and pipeline are all
   measured from one consistent clock.
2. **Monthly panel** (`gtm_monthly` → `gtm_company_monthly`): 42 months of
   first-principle GTM drivers. Trailing-twelve-month and year-over-year metrics
   (NRR, GRR, growth, Magic Number, burn multiple) are reconstructed from the
   panel rather than stored as opaque snapshots, so every number is auditable and
   reproduces exactly from the seed.

In production this generalises to date-partitioned, snapshot/SCD-style marts in
BigQuery: facts partitioned by event date, dimensions tracked as slowly-changing,
and a `dbt snapshot` (or daily `metrics_daily` table) preserving history. The
local panel is the shape of that history at zero cost.

## Governance boundary (carried into every surface)

| Decision | Owner |
|---|---|
| Reconciliation, feature engineering, scoring, GTM metric math | Deterministic SQL / Python |
| Evidence-cited summaries | Grounded brief (draft only) |
| Price, discount, forecast commit, customer-facing recommendation | Human approval |
| Audit trail | Source IDs, planted manifest, score drivers, calibration, citations |

The same rule holds on the field-sales and ops surfaces: they *show* eligibility
(e.g. "Forecast-ready" vs "Evidence required") but never let a user override the
governed flag.

## Cost and privacy

- **Cost: zero.** DuckDB, Streamlit, Apps Script, and the static HTML surface are
  all free; BigQuery/Looker/AppSheet are the production swap-ins, not required to
  run or evaluate the project.
- **Privacy: synthetic only.** No employer, customer, pricing, credential, or PII
  data. Names, vendors, and values are generated; the disclaimer ships in
  `dataset_meta`.
