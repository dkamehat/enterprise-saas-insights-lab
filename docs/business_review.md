# Monthly Business Review — GTM (synthetic)

*Audience: executive staff. One page. Numbers are synthetic and reproduce from the
seeded warehouse (`gtm_company_monthly`, `account_positioning`). This memo is a
writing sample: how a Strategy & Operations partner frames the same data the
dashboards show.*

---

**Bottom line.** We are compounding ARR at **47% YoY to ¥12.1B** with a **Rule of
40 of 58** — growth is efficient, not bought. The constraint on next-quarter
growth is **sales capacity in Enterprise**, not demand or efficiency. I recommend
shifting incremental S&M into Enterprise expansion and fixing Commercial
onboarding; combined modeled effect is **+¥0.4–0.6B net-new ARR over the next four
quarters** at flat blended CAC payback.

## Where we are

| Metric | Now | Read |
|---|---|---|
| ARR / growth | ¥12.1B · **+47% YoY** | top-quartile growth |
| NRR / GRR (TTM) | **114%** / 88% | base expands faster than it leaks; **GRR below the 90% bar** |
| Rule of 40 | **58** | growth + improving operating margin (now ~+11%) |
| Magic Number | **1.30** | each ¥1 of prior-quarter S&M returns ¥1.30 of net-new ARR |
| CAC payback / LTV·CAC | **18 mo** / **5.4x** | healthy; payback well inside one renewal cycle |
| Pipeline coverage | **3.4x** | adequate, not excessive |

## What's working

- **Retention is the engine.** NRR of 114% means most growth comes from the
  installed base. Enterprise leads at **NRR 117.5%** — expansion motion is real.
- **Efficiency is improving as we scale.** Operating margin has moved from
  negative to ~+11% TTM while growth held, lifting Rule of 40 quarter over
  quarter. We are no longer buying growth.

## What's at risk

- **Commercial trades retention for speed.** Fastest grower (+51%) but
  **GRR 83.7%** — gross churn is leaking ~16% of the base annually. This is the
  single biggest drag on blended GRR.
- **Enterprise is capacity-bound.** Win rate (27%) and pipeline coverage are
  healthy; the limiter is rep capacity against an expanding book, not lead flow.
- **Governance queue.** A slice of high-value accounts sits in *Evidence required*
  and is correctly held out of Commit until the data baseline is reconciled —
  real upside, but not forecastable yet.

## Recommendations

1. **Fund Enterprise expansion capacity** (reallocate, don't add net S&M). Magic
   Number 1.3 says marginal S&M is productive; Enterprise NRR 117.5% says the
   return is highest here. *Modeled: +¥0.3–0.4B net-new ARR / 4 quarters.*
2. **Fix Commercial onboarding to lift GRR ≥ 88%.** Target the first-90-day churn
   cohort. Closing the gap to Enterprise GRR is worth *~+¥0.1–0.2B retained ARR*.
3. **Clear the evidence queue.** Reconcile the *Evidence required* accounts to move
   qualified value from Upside into Commit — converts known upside into forecast.

## Asks of the staff

- Approve the S&M reallocation toward Enterprise expansion for next quarter.
- Sponsor a Commercial onboarding/retention sprint with CS.
- Endorse keeping unreconciled accounts out of Commit (governance over optics).

*Method: every figure is reconstructed from monthly drivers in
`src/saas_insights/gtm.py`; see `docs/reference_architecture.md` for the data
design and `pages/9_GTM_Economics.py` for the interactive view.*
