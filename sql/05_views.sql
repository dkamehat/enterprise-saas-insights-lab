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

CREATE OR REPLACE VIEW portfolio_summary AS
SELECT
    COUNT(*) AS account_count,
    SUM(estimated_tcv_jpy_mn) AS estimated_tcv_jpy_mn,
    SUM(expected_commercial_value_jpy_mn) AS expected_commercial_value_jpy_mn,
    COUNT(*) FILTER (WHERE priority_band = 'High') AS high_priority_accounts,
    COUNT(*) FILTER (WHERE governance_status = 'Forecast-ready') AS forecast_ready_accounts,
    AVG(data_confidence_pct) AS avg_data_confidence_pct
FROM account_positioning;
