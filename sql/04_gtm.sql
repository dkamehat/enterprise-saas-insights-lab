-- Time-aware GTM economics marts.
-- gtm_monthly_metrics is materialised in Python (saas_insights.gtm.compute_gtm_metrics)
-- so that every SaaS efficiency metric is reconstructed from monthly drivers and
-- remains auditable. These views expose the company roll-up, the latest snapshot,
-- and the per-segment latest cut for the Strategy & Operations page.

CREATE OR REPLACE VIEW gtm_company_monthly AS
SELECT *
FROM gtm_monthly_metrics
WHERE segment = 'Company'
ORDER BY month;

CREATE OR REPLACE VIEW gtm_summary_latest AS
SELECT *
FROM gtm_company_monthly
WHERE month = (SELECT MAX(month) FROM gtm_company_monthly);

CREATE OR REPLACE VIEW gtm_segment_latest AS
SELECT *
FROM gtm_monthly_metrics
WHERE segment <> 'Company'
  AND month = (SELECT MAX(month) FROM gtm_monthly_metrics)
ORDER BY ending_arr_jpy_mn DESC;
