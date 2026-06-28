# Interview Demo Script

A 4-minute walkthrough framed for a Strategy & Operations / BizOps conversation.
Lead with the business question, show efficient growth, then the decision and how
it reaches every team.

## 1. The business question (20s)

> "Not every account deserves the same attention, and not every growth number is
> equally healthy. I built one backbone that answers two questions from the same
> data: *is our growth efficient?* and *where should the field spend the next hour?*"

## 2. GTM Economics — is growth efficient? (70s)

Open **GTM Economics**.

1. Headline KPIs vs benchmarks: ARR growth ~47% with **Rule of 40 = 58** → growth
   is efficient, not bought.
2. **NRR 114% / GRR 88%** → the installed base is the engine; retention drives ARR.
3. **Magic Number 1.3, CAC payback ~18mo, LTV/CAC 5.4x** → marginal sales spend is
   productive, so capacity — not demand — is the constraint.
4. ARR bridge + Rule of 40 decomposition: show the path from negative to positive
   operating margin while growth held.

> "Every one of these is reconstructed from monthly drivers, not hard-coded — so
> it's auditable and reproduces from the seed."

## 3. From metric to account decision (60s)

Open **Executive Portfolio**, then **Account 360**.

1. Accounts ranked by expected value × win-fit × data trust — not alphabetically.
2. Drill into one account: recommended play, score drivers, asset reconciliation,
   competitive positioning, next best action, 3-year TCO.
3. **Governance:** a large opportunity with low data confidence stays *Evidence
   required* and out of Commit until reconciled — separate commercial
   attractiveness from forecast confidence.

## 4. One backbone, many surfaces (60s)

Open `delivery/gas_webapp/dashboard.html` (and reference `docs/reference_architecture.md`).

> "The same governed marts feed Looker for execs, this Streamlit app for analysts,
> a lightweight Apps Script/HTML app for operations teams a heavy BI tool never
> reaches, and AppSheet for field sales. The metric is defined once in the
> warehouse, so no two surfaces disagree. In production this is BigQuery; locally
> it's DuckDB running the identical SQL — zero cost to demonstrate."

## Wording to reuse

> I separate commercial attractiveness from forecast confidence. A large
> opportunity can still be high priority for evidence collection while remaining
> ineligible for Commit until the asset and contract baseline is reconciled.

> The output is not a dashboard. It's a decision: is growth efficient, what to
> sell, why we win, which evidence supports it, and what the AE does next —
> delivered to each audience in the form it actually uses.

## Trade-offs to be ready for

**Rule-based scoring** — explainable, fast, auditable, works before labeled
outcomes exist; but weights need governance and can miss non-linear patterns. The
recommended path is champion/challenger with an ML challenger, not an immediate
replacement of business rules.

**Synthetic data** — lets the whole pipeline be public and reproducible with zero
privacy risk; the modeling discipline (first-principle drivers, governance
boundary, calibration) is what transfers to production.
