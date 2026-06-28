# AppSheet — field sales surface (spec)

The third delivery surface in the "one backbone, many surfaces" model. AppSheet
gives **field sellers a mobile, action-oriented app** over the *same* governed
marts that feed Looker (execs) and the Apps Script web app (ops). No new data
pipeline — only a new surface.

## Why AppSheet for this audience
- Sellers live on mobile and need to *act*, not explore dashboards.
- No-code/low-code means the app evolves at the speed of the sales motion.
- Row-level security maps cleanly to AE / manager / theater ownership.

## Data source
- Primary: BigQuery marts (`account_positioning`, `renewal_pipeline`) via a
  scheduled export to a connected Google Sheet, or BigQuery directly on plans
  that support it. The export job is the same one that powers `outputs/*.csv`.
- The app is **read-mostly**: sellers update only `next_step_owner` and
  `next_step_due`, which sync back to a writeback table — pricing, discount, and
  forecast commit stay system-of-record controlled (see governance below).

## Core views
| View | Type | Purpose |
|---|---|---|
| My Accounts | deck | AE's accounts ranked by `priority_score`, filtered to `ae_name = USEREMAIL()` |
| Account detail | detail | recommended play, expected value, score drivers, next best action |
| Renewals (180d) | table | `renewal_pipeline` sorted by `days_to_renewal` |
| Needs evidence | gallery | `governance_status = 'Evidence required'` — work queue before Commit |

## Key column logic (AppSheet expressions)
```
Priority color   = IFS([priority_band]="High","Red",[priority_band]="Medium","Orange",TRUE,"Green")
My rows (RLS)    = [ae_name] = LOOKUP(USEREMAIL(), "users", "email", "ae_name")
Commit-eligible  = AND([governance_status]="Forecast-ready", [data_confidence_pct] >= 85)
```

## Governance (same boundary as every other surface)
- Sellers can record activity and ownership; they **cannot** change price,
  discount, entitlement, or forecast category from the app.
- `Commit-eligible` is a derived, read-only flag — the app surfaces the rule, it
  does not let a user override it.

This spec is intentionally buildable: every field referenced exists in the
warehouse marts in this repo.
