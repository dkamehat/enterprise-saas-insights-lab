CREATE OR REPLACE TABLE account_features AS
WITH asset_agg AS (
    SELECT
        account_id,
        COUNT(*) AS total_assets,
        COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor') AS primary_assets,
        COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND product_family IN ('Core Platform', 'Data Platform')
              AND end_of_support_date <= DATE '2027-12-21'
        ) AS modernization_asset_count,
        100.0 * COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor') / NULLIF(COUNT(*), 0) AS primary_share_pct,
        100.0 * COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor' AND product_family IN ('Core Platform', 'Data Platform')
        ) / NULLIF(COUNT(*) FILTER (WHERE product_family IN ('Core Platform', 'Data Platform')), 0) AS primary_platform_share_pct,
        100.0 * COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor' AND product_family = 'Data Platform'
        ) / NULLIF(COUNT(*) FILTER (WHERE product_family = 'Data Platform'), 0) AS primary_data_share_pct,
        100.0 * COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND product_family IN ('Core Platform', 'Data Platform')
              AND end_of_support_date <= DATE '2027-12-21'
        ) / NULLIF(COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor' AND product_family IN ('Core Platform', 'Data Platform')
        ), 0) AS eol_18m_pct,
        100.0 * COUNT(*) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND (missing_contract_flag = 1 OR orphan_contract_flag = 1 OR contract_account_mismatch_flag = 1)
        ) / NULLIF(COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor'), 0) AS support_gap_pct,
        100.0 * COUNT(*) FILTER (
            WHERE product_family = 'Data Platform' AND capacity_units < 400
        ) / NULLIF(COUNT(*) FILTER (WHERE product_family = 'Data Platform'), 0) AS data_throughput_gap_pct,
        100.0 * AVG(
            CASE
                WHEN product_family IN ('Core Platform', 'Data Platform')
                THEN GREATEST(0, LEAST(1, (utilization_pct - 65.0) / 35.0))
            END
        ) AS platform_utilization_pressure_pct,
        AVG(asset_data_confidence_pct) AS data_confidence_pct,
        100.0 * COUNT(*) FILTER (WHERE reconciliation_status = 'Verified') / NULLIF(COUNT(*), 0) AS verified_assets_pct,
        100.0 * COUNT(*) FILTER (WHERE reconciliation_status = 'Reconcilable') / NULLIF(COUNT(*), 0) AS reconcilable_assets_pct,
        100.0 * COUNT(*) FILTER (WHERE reconciliation_status = 'Unknown') / NULLIF(COUNT(*), 0) AS unknown_assets_pct
    FROM asset_reconciliation
    GROUP BY account_id
), contract_agg AS (
    SELECT
        account_id,
        COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor' AND status IN ('Active', 'Pending')) AS active_primary_contracts,
        COUNT(DISTINCT DATE_TRUNC('month', end_date)) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND end_date BETWEEN DATE '2026-06-21' AND DATE '2028-06-21'
        ) AS renewal_month_count_24m,
        SUM(annual_value_jpy_mn) FILTER (WHERE vendor = 'Primary SaaS Vendor' AND status IN ('Active', 'Pending')) AS primary_annual_contract_value_jpy_mn,
        SUM(annual_value_jpy_mn) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND end_date BETWEEN DATE '2026-06-21' AND DATE '2026-12-18'
        ) AS renewal_value_180d_jpy_mn,
        SUM(annual_value_jpy_mn) FILTER (
            WHERE vendor = 'Primary SaaS Vendor'
              AND product_family = 'Security Suite'
              AND end_date BETWEEN DATE '2026-06-21' AND DATE '2027-06-21'
        ) AS security_renewal_12m_jpy_mn,
        AVG(adoption_pct) FILTER (WHERE vendor = 'Primary SaaS Vendor' AND status IN ('Active', 'Pending')) AS avg_adoption_pct,
        COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor' AND enterprise_plan_eligible) AS enterprise_plan_eligible_contracts,
        COUNT(*) FILTER (WHERE vendor = 'Primary SaaS Vendor' AND contract_type = 'Enterprise Agreement' AND status IN ('Active', 'Pending')) AS active_enterprise_plan_contracts
    FROM stg_contracts
    GROUP BY account_id
), support_agg AS (
    SELECT
        account_id,
        COUNT(*) AS support_case_count_18m,
        COUNT(*) FILTER (WHERE severity IN ('S1', 'S2')) AS severe_case_count_18m,
        COUNT(*) FILTER (WHERE status = 'Open') AS open_case_count,
        AVG(resolution_hours) AS avg_resolution_hours
    FROM stg_support_cases
    GROUP BY account_id
), competitor_agg AS (
    SELECT
        account_id,
        MAX(signal_strength_pct) AS competitive_pressure_pct,
        ARG_MAX(competitor, signal_strength_pct) AS top_competitor,
        COUNT(*) AS competitor_signal_count,
        MAX(signal_strength_pct) FILTER (WHERE sales_play = 'Platform Modernization') AS platform_competitive_pressure_pct,
        ARG_MAX(competitor, signal_strength_pct) FILTER (WHERE sales_play = 'Platform Modernization') AS platform_competitor,
        MAX(signal_strength_pct) FILTER (WHERE sales_play = 'Security Platform') AS security_competitive_pressure_pct,
        ARG_MAX(competitor, signal_strength_pct) FILTER (WHERE sales_play = 'Security Platform') AS security_competitor,
        MAX(signal_strength_pct) FILTER (WHERE sales_play = 'AI Data Platform') AS ai_competitive_pressure_pct,
        ARG_MAX(competitor, signal_strength_pct) FILTER (WHERE sales_play = 'AI Data Platform') AS ai_competitor,
        MAX(signal_strength_pct) FILTER (WHERE sales_play = 'Renewal / Enterprise Plan') AS renewal_competitive_pressure_pct,
        ARG_MAX(competitor, signal_strength_pct) FILTER (WHERE sales_play = 'Renewal / Enterprise Plan') AS renewal_competitor
    FROM stg_competitor_signals
    GROUP BY account_id
), opportunity_agg AS (
    SELECT
        account_id,
        SUM(amount_jpy_mn) FILTER (WHERE stage NOT IN ('Closed Won', 'Closed Lost')) AS open_pipeline_jpy_mn,
        SUM(amount_jpy_mn * win_probability_pct / 100.0) FILTER (WHERE stage NOT IN ('Closed Won', 'Closed Lost')) AS weighted_pipeline_jpy_mn,
        COUNT(*) FILTER (WHERE stage NOT IN ('Closed Won', 'Closed Lost')) AS open_opportunity_count,
        AVG(ABS(amount_jpy_mn - quote_amount_jpy_mn) / NULLIF(amount_jpy_mn, 0) * 100.0) AS avg_quote_variance_pct,
        COUNT(*) FILTER (WHERE forecast_category = 'Commit' AND stage NOT IN ('Closed Won', 'Closed Lost')) AS commit_count
    FROM stg_opportunities
    GROUP BY account_id
)
SELECT
    a.*,
    COALESCE(x.total_assets, 0) AS total_assets,
    COALESCE(x.primary_assets, 0) AS primary_assets,
    COALESCE(x.modernization_asset_count, 0) AS modernization_asset_count,
    COALESCE(x.primary_share_pct, 0) AS primary_share_pct,
    COALESCE(x.primary_platform_share_pct, 0) AS primary_platform_share_pct,
    COALESCE(x.primary_data_share_pct, 0) AS primary_data_share_pct,
    COALESCE(x.eol_18m_pct, 0) AS eol_18m_pct,
    COALESCE(x.support_gap_pct, 0) AS support_gap_pct,
    COALESCE(x.data_throughput_gap_pct, 0) AS data_throughput_gap_pct,
    COALESCE(x.platform_utilization_pressure_pct, 0) AS platform_utilization_pressure_pct,
    COALESCE(x.data_confidence_pct, 0) AS data_confidence_pct,
    COALESCE(x.verified_assets_pct, 0) AS verified_assets_pct,
    COALESCE(x.reconcilable_assets_pct, 0) AS reconcilable_assets_pct,
    COALESCE(x.unknown_assets_pct, 0) AS unknown_assets_pct,
    COALESCE(c.active_primary_contracts, 0) AS active_primary_contracts,
    COALESCE(c.renewal_month_count_24m, 0) AS renewal_month_count_24m,
    COALESCE(c.primary_annual_contract_value_jpy_mn, 0) AS primary_annual_contract_value_jpy_mn,
    COALESCE(c.renewal_value_180d_jpy_mn, 0) AS renewal_value_180d_jpy_mn,
    COALESCE(c.security_renewal_12m_jpy_mn, 0) AS security_renewal_12m_jpy_mn,
    COALESCE(c.avg_adoption_pct, 0) AS avg_adoption_pct,
    COALESCE(c.enterprise_plan_eligible_contracts, 0) AS enterprise_plan_eligible_contracts,
    COALESCE(c.active_enterprise_plan_contracts, 0) AS active_enterprise_plan_contracts,
    COALESCE(s.support_case_count_18m, 0) AS support_case_count_18m,
    COALESCE(s.severe_case_count_18m, 0) AS severe_case_count_18m,
    COALESCE(s.open_case_count, 0) AS open_case_count,
    COALESCE(s.avg_resolution_hours, 0) AS avg_resolution_hours,
    COALESCE(g.competitive_pressure_pct, 0) AS competitive_pressure_pct,
    COALESCE(g.top_competitor, 'No Decision') AS top_competitor,
    COALESCE(g.competitor_signal_count, 0) AS competitor_signal_count,
    COALESCE(g.platform_competitive_pressure_pct, 0) AS platform_competitive_pressure_pct,
    COALESCE(g.platform_competitor, 'No Decision') AS platform_competitor,
    COALESCE(g.security_competitive_pressure_pct, 0) AS security_competitive_pressure_pct,
    COALESCE(g.security_competitor, 'No Decision') AS security_competitor,
    COALESCE(g.ai_competitive_pressure_pct, 0) AS ai_competitive_pressure_pct,
    COALESCE(g.ai_competitor, 'No Decision') AS ai_competitor,
    COALESCE(g.renewal_competitive_pressure_pct, 0) AS renewal_competitive_pressure_pct,
    COALESCE(g.renewal_competitor, 'No Decision') AS renewal_competitor,
    COALESCE(o.open_pipeline_jpy_mn, 0) AS open_pipeline_jpy_mn,
    COALESCE(o.weighted_pipeline_jpy_mn, 0) AS weighted_pipeline_jpy_mn,
    COALESCE(o.open_opportunity_count, 0) AS open_opportunity_count,
    COALESCE(o.avg_quote_variance_pct, 0) AS avg_quote_variance_pct,
    COALESCE(o.commit_count, 0) AS commit_count,
    LEAST(100.0, GREATEST(0.0,
        55.0 * LEAST(1.0, COALESCE(c.active_primary_contracts, 0) / 8.0)
        + 45.0 * LEAST(1.0, COALESCE(c.renewal_month_count_24m, 0) / 8.0)
    )) AS contract_fragmentation_pct,
    LEAST(100.0, 35.0 * COALESCE(s.severe_case_count_18m, 0) + 10.0 * COALESCE(s.open_case_count, 0)) AS incident_pressure_pct
FROM stg_accounts a
LEFT JOIN asset_agg x USING (account_id)
LEFT JOIN contract_agg c USING (account_id)
LEFT JOIN support_agg s USING (account_id)
LEFT JOIN competitor_agg g USING (account_id)
LEFT JOIN opportunity_agg o USING (account_id);
