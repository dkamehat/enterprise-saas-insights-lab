CREATE OR REPLACE VIEW reconciliation_waterfall AS
SELECT 1 AS step_order, 'All assets' AS step, COUNT(*) AS asset_count FROM asset_reconciliation
UNION ALL
SELECT 2, 'Serial present', COUNT(*) FROM asset_reconciliation WHERE missing_serial_flag = 0
UNION ALL
SELECT 3, 'Unique serial', COUNT(*) FROM asset_reconciliation WHERE missing_serial_flag = 0 AND duplicate_serial_flag = 0
UNION ALL
SELECT 4, 'Contract aligned', COUNT(*) FROM asset_reconciliation
    WHERE missing_serial_flag = 0 AND duplicate_serial_flag = 0
      AND orphan_contract_flag = 0 AND contract_account_mismatch_flag = 0
UNION ALL
SELECT 5, 'Entitlement aligned', COUNT(*) FROM asset_reconciliation
    WHERE missing_serial_flag = 0 AND duplicate_serial_flag = 0
      AND orphan_contract_flag = 0 AND contract_account_mismatch_flag = 0
      AND orphan_entitlement_flag = 0 AND entitlement_account_mismatch_flag = 0
UNION ALL
SELECT 6, 'Verified', COUNT(*) FROM asset_reconciliation WHERE reconciliation_status = 'Verified';

CREATE OR REPLACE VIEW renewal_pipeline AS
SELECT
    c.*,
    p.industry,
    p.customer_business_model,
    p.sales_theater,
    p.sales_group,
    p.sales_manager,
    p.ae_name,
    p.route_to_market,
    p.priority_score,
    p.priority_band,
    p.recommended_play,
    p.data_confidence_pct,
    p.governance_status,
    DATE_DIFF('day', DATE '2026-06-21', c.end_date) AS days_to_renewal
FROM stg_contracts c
LEFT JOIN account_positioning p USING (account_id)
WHERE c.vendor = 'Primary SaaS Vendor'
  AND c.end_date >= DATE '2026-06-21';

CREATE OR REPLACE VIEW nrr_decomposition AS
WITH primary_contracts AS (
    SELECT
        c.account_id,
        SUM(c.annual_value_jpy_mn) FILTER (
            WHERE c.status IN ('Active', 'Pending')
        ) AS opening_arr_jpy_mn,
        SUM(
            c.annual_value_jpy_mn * (1.0 - c.renewal_probability_pct / 100.0)
        ) FILTER (
            WHERE c.end_date BETWEEN DATE '2026-06-21' AND DATE '2027-06-21'
        ) AS churn_risk_jpy_mn,
        SUM(
            c.annual_value_jpy_mn
            * GREATEST(0.0, 75.0 - c.adoption_pct) / 100.0
            * 0.40
        ) FILTER (
            WHERE c.status IN ('Active', 'Pending')
        ) AS contraction_risk_jpy_mn,
        SUM(
            c.annual_value_jpy_mn
            * CASE WHEN c.enterprise_plan_eligible THEN 0.32 ELSE 0.12 END
            * LEAST(1.0, c.adoption_pct / 100.0)
        ) FILTER (
            WHERE c.status IN ('Active', 'Pending')
        ) AS expansion_potential_jpy_mn
    FROM stg_contracts c
    WHERE c.vendor = 'Primary SaaS Vendor'
    GROUP BY c.account_id
)
SELECT
    p.account_id,
    a.account_name,
    a.segment,
    a.sales_theater,
    a.sales_group,
    a.ae_name,
    p.priority_score,
    p.recommended_play,
    p.governance_status,
    COALESCE(c.opening_arr_jpy_mn, 0) AS opening_arr_jpy_mn,
    COALESCE(c.churn_risk_jpy_mn, 0) AS churn_risk_jpy_mn,
    COALESCE(c.contraction_risk_jpy_mn, 0) AS contraction_risk_jpy_mn,
    COALESCE(c.expansion_potential_jpy_mn, 0) AS expansion_potential_jpy_mn,
    GREATEST(
        0,
        COALESCE(c.opening_arr_jpy_mn, 0)
        - COALESCE(c.churn_risk_jpy_mn, 0)
        - COALESCE(c.contraction_risk_jpy_mn, 0)
        + COALESCE(c.expansion_potential_jpy_mn, 0)
    ) AS modeled_ending_arr_jpy_mn,
    100.0 * GREATEST(
        0,
        COALESCE(c.opening_arr_jpy_mn, 0)
        - COALESCE(c.churn_risk_jpy_mn, 0)
        - COALESCE(c.contraction_risk_jpy_mn, 0)
        + COALESCE(c.expansion_potential_jpy_mn, 0)
    ) / NULLIF(COALESCE(c.opening_arr_jpy_mn, 0), 0) AS modeled_nrr_pct,
    100.0 * GREATEST(
        0,
        COALESCE(c.opening_arr_jpy_mn, 0)
        - COALESCE(c.churn_risk_jpy_mn, 0)
        - COALESCE(c.contraction_risk_jpy_mn, 0)
    ) / NULLIF(COALESCE(c.opening_arr_jpy_mn, 0), 0) AS modeled_grr_pct
FROM account_positioning p
LEFT JOIN stg_accounts a USING (account_id)
LEFT JOIN primary_contracts c USING (account_id);

CREATE OR REPLACE VIEW true_forward_exposure AS
SELECT
    r.account_id,
    a.account_name,
    a.segment,
    a.sales_group,
    a.ae_name,
    COUNT(*) AS exposed_assets,
    SUM(r.true_forward_overage_units) AS overage_units,
    SUM(r.true_forward_exposure_jpy_mn) AS exposure_jpy_mn,
    AVG(r.consumed_quantity / NULLIF(r.entitled_quantity, 0) * 100.0) AS avg_consumption_pct,
    MAX(r.true_forward_exposure_jpy_mn) AS max_asset_exposure_jpy_mn
FROM asset_reconciliation r
LEFT JOIN stg_accounts a USING (account_id)
WHERE r.true_forward_exposure_flag = 1
GROUP BY
    r.account_id,
    a.account_name,
    a.segment,
    a.sales_group,
    a.ae_name;

CREATE OR REPLACE VIEW forecast_calibration AS
WITH closed_outcomes AS (
    SELECT
        p.account_id,
        p.modeled_win_probability_pct,
        FLOOR(p.modeled_win_probability_pct / 10.0) * 10 AS probability_bucket,
        CASE WHEN o.stage = 'Closed Won' THEN 1.0 ELSE 0.0 END AS actual_win
    FROM account_positioning p
    JOIN stg_opportunities o USING (account_id)
    WHERE o.stage IN ('Closed Won', 'Closed Lost')
)
SELECT
    probability_bucket,
    COUNT(*) AS closed_opportunities,
    AVG(modeled_win_probability_pct) AS avg_predicted_probability_pct,
    100.0 * AVG(actual_win) AS actual_win_rate_pct,
    AVG(POWER(modeled_win_probability_pct / 100.0 - actual_win, 2)) AS brier_score,
    ABS(AVG(modeled_win_probability_pct) - 100.0 * AVG(actual_win)) AS calibration_gap_pct
FROM closed_outcomes
GROUP BY probability_bucket
ORDER BY probability_bucket;

CREATE OR REPLACE VIEW forecast_calibration_summary AS
SELECT
    SUM(closed_opportunities) AS closed_opportunities,
    AVG(brier_score) AS avg_brier_score,
    AVG(calibration_gap_pct) AS avg_calibration_gap_pct,
    MAX(calibration_gap_pct) AS max_calibration_gap_pct
FROM forecast_calibration;

CREATE OR REPLACE VIEW portfolio_summary AS
SELECT
    COUNT(*) AS account_count,
    SUM(estimated_tcv_jpy_mn) AS estimated_tcv_jpy_mn,
    SUM(expected_commercial_value_jpy_mn) AS expected_commercial_value_jpy_mn,
    COUNT(*) FILTER (WHERE priority_band = 'High') AS high_priority_accounts,
    COUNT(*) FILTER (WHERE governance_status = 'Forecast-ready') AS forecast_ready_accounts,
    AVG(data_confidence_pct) AS avg_data_confidence_pct
FROM account_positioning;
