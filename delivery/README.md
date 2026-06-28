# Delivery layer — one backbone, many surfaces

The hard part of analytics in a real GTM org is not the chart. It is getting
**one trusted number to every audience in the form each audience actually uses** —
without forking the logic three ways. This folder shows that discipline: every
surface below reads the *same* governed marts produced by the pipeline in this
repo.

```
                 ┌───────────────────────────────────────────┐
                 │   Unified backbone  (BigQuery in prod,      │
                 │   DuckDB locally — identical SQL models)    │
                 │   raw → staging → reconciliation →          │
                 │   account marts + time-aware GTM marts      │
                 └───────────────┬───────────────────────────┘
                                 │  one definition of ARR / NRR / Rule of 40 / …
        ┌────────────────────────┼─────────────────────────┬──────────────────┐
        ▼                        ▼                          ▼                  ▼
   Looker (LookML)         Streamlit app              Apps Script web app   AppSheet
   execs & analysts        analysts / interview       operations teams      field sales
   self-serve explores     deep, governed views       lightweight HTML      mobile, action
   delivery/looker/        app.py + pages/            delivery/gas_webapp/  delivery/appsheet/
```

## Why this matters
A common failure mode: Looker says one NRR, a board deck says another, and an
ops spreadsheet says a third. Here the metric is defined **once** in
`saas_insights.gtm` / the SQL marts, and every surface — including the Looker
semantic layer and the ops web app — references that single definition. The BI
tool cannot disagree with the warehouse because it does not recompute the metric.

## Surfaces
| Surface | Audience | Built from | Status |
|---|---|---|---|
| `looker/` | Execs, analysts (self-serve) | BigQuery marts via LookML | spec |
| `gas_webapp/` | Operations teams | BigQuery marts via Apps Script + native-canvas HTML | runnable demo (`dashboard.html`) |
| `appsheet/` | Field sales (mobile) | BigQuery marts via connected Sheet | spec |
| `../app.py` + `../pages/` | Analysts, interview demo | DuckDB warehouse | runnable |

## Run the ops surface locally (no cloud, no cost)
```bash
python -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42
python scripts/build_delivery_dashboard.py
# open delivery/gas_webapp/dashboard.html in any browser — fully self-contained
```

`dashboard.html` is the same UI the Apps Script `Code.gs` / `Index.html` serve;
locally the data is inlined from the warehouse, in production `getData()` queries
BigQuery. See `../docs/reference_architecture.md` for the time-aware data design.
