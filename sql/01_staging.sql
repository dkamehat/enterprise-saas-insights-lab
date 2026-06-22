CREATE OR REPLACE TABLE stg_accounts AS
SELECT
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(account_name AS VARCHAR) AS account_name,
    CAST(industry AS VARCHAR) AS industry,
    CAST(segment AS VARCHAR) AS segment,
    CAST(region AS VARCHAR) AS region,
    CAST(ae_name AS VARCHAR) AS ae_name,
    CAST(partner_name AS VARCHAR) AS partner_name,
    CAST(strategic_tier AS VARCHAR) AS strategic_tier,
    CAST(annual_revenue_jpy_mn AS DOUBLE) AS annual_revenue_jpy_mn,
    CAST(employee_count AS BIGINT) AS employee_count,
    CAST(primary_relationship_years AS BIGINT) AS primary_relationship_years,
    CAST(security_tool_count AS BIGINT) AS security_tool_count,
    CAST(log_analytics_installed AS BOOLEAN) AS log_analytics_installed,
    CAST(ai_investment_horizon_months AS BIGINT) AS ai_investment_horizon_months,
    CAST(gpu_cluster_planned AS BOOLEAN) AS gpu_cluster_planned,
    CAST(budget_readiness_pct AS DOUBLE) AS budget_readiness_pct,
    CAST(managed_service_interest AS DOUBLE) AS managed_service_interest,
    CAST(budget_cycle_month AS BIGINT) AS budget_cycle_month
FROM raw_accounts;

CREATE OR REPLACE TABLE stg_contracts AS
SELECT
    CAST(contract_id AS VARCHAR) AS contract_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(vendor AS VARCHAR) AS vendor,
    CAST(product_family AS VARCHAR) AS product_family,
    CAST(contract_type AS VARCHAR) AS contract_type,
    TRY_CAST(start_date AS DATE) AS start_date,
    TRY_CAST(end_date AS DATE) AS end_date,
    CAST(annual_value_jpy_mn AS DOUBLE) AS annual_value_jpy_mn,
    CAST(currency AS VARCHAR) AS currency,
    CAST(status AS VARCHAR) AS status,
    CAST(renewal_probability_pct AS DOUBLE) AS renewal_probability_pct,
    CAST(adoption_pct AS DOUBLE) AS adoption_pct,
    CAST(discount_pct AS DOUBLE) AS discount_pct,
    CAST(enterprise_plan_eligible AS BOOLEAN) AS enterprise_plan_eligible,
    CAST(source_system AS VARCHAR) AS source_system
FROM raw_contracts;

CREATE OR REPLACE TABLE stg_assets AS
SELECT
    CAST(asset_id AS VARCHAR) AS asset_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(site_id AS VARCHAR) AS site_id,
    NULLIF(UPPER(TRIM(CAST(serial_number AS VARCHAR))), '') AS serial_number,
    CAST(vendor AS VARCHAR) AS vendor,
    CAST(product_family AS VARCHAR) AS product_family,
    CAST(product_line AS VARCHAR) AS product_line,
    CAST(model AS VARCHAR) AS model,
    TRY_CAST(install_date AS DATE) AS install_date,
    TRY_CAST(eol_date AS DATE) AS eol_date,
    TRY_CAST(end_of_support_date AS DATE) AS end_of_support_date,
    CAST(criticality AS VARCHAR) AS criticality,
    CAST(utilization_pct AS DOUBLE) AS utilization_pct,
    CAST(capacity_units AS BIGINT) AS capacity_units,
    NULLIF(TRIM(CAST(contract_id AS VARCHAR)), '') AS contract_id,
    NULLIF(TRIM(CAST(entitlement_id AS VARCHAR)), '') AS entitlement_id,
    CAST(source_system AS VARCHAR) AS source_system,
    TRY_CAST(last_verified_date AS DATE) AS last_verified_date
FROM raw_assets;

CREATE OR REPLACE TABLE stg_entitlements AS
SELECT
    CAST(entitlement_id AS VARCHAR) AS entitlement_id,
    CAST(asset_id AS VARCHAR) AS asset_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(vendor AS VARCHAR) AS vendor,
    CAST(product_family AS VARCHAR) AS product_family,
    CAST(license_quantity AS DOUBLE) AS license_quantity,
    CAST(consumed_quantity AS DOUBLE) AS consumed_quantity,
    CAST(support_level AS VARCHAR) AS support_level,
    TRY_CAST(start_date AS DATE) AS start_date,
    TRY_CAST(end_date AS DATE) AS end_date
FROM raw_entitlements;

CREATE OR REPLACE TABLE stg_support_cases AS
SELECT
    CAST(case_id AS VARCHAR) AS case_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(asset_id AS VARCHAR) AS asset_id,
    CAST(severity AS VARCHAR) AS severity,
    TRY_CAST(opened_date AS DATE) AS opened_date,
    TRY_CAST(closed_date AS DATE) AS closed_date,
    CAST(resolution_hours AS DOUBLE) AS resolution_hours,
    CAST(status AS VARCHAR) AS status
FROM raw_support_cases;

CREATE OR REPLACE TABLE stg_competitor_signals AS
SELECT
    CAST(signal_id AS VARCHAR) AS signal_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(sales_play AS VARCHAR) AS sales_play,
    CAST(competitor AS VARCHAR) AS competitor,
    CAST(signal_type AS VARCHAR) AS signal_type,
    CAST(signal_strength_pct AS DOUBLE) AS signal_strength_pct,
    TRY_CAST(observed_date AS DATE) AS observed_date,
    CAST(source AS VARCHAR) AS source
FROM raw_competitor_signals;

CREATE OR REPLACE TABLE stg_opportunities AS
SELECT
    CAST(opportunity_id AS VARCHAR) AS opportunity_id,
    CAST(account_id AS VARCHAR) AS account_id,
    CAST(sales_play AS VARCHAR) AS sales_play,
    CAST(competitor AS VARCHAR) AS competitor,
    CAST(stage AS VARCHAR) AS stage,
    TRY_CAST(close_date AS DATE) AS close_date,
    CAST(amount_jpy_mn AS DOUBLE) AS amount_jpy_mn,
    CAST(quote_amount_jpy_mn AS DOUBLE) AS quote_amount_jpy_mn,
    CAST(discount_pct AS DOUBLE) AS discount_pct,
    CAST(win_probability_pct AS DOUBLE) AS win_probability_pct,
    CAST(forecast_category AS VARCHAR) AS forecast_category,
    CAST(source_system AS VARCHAR) AS source_system
FROM raw_opportunities;

CREATE OR REPLACE TABLE stg_product_events AS
SELECT
    CAST(event_id AS VARCHAR) AS event_id,
    CAST(product_family AS VARCHAR) AS product_family,
    CAST(event_type AS VARCHAR) AS event_type,
    TRY_CAST(effective_date AS DATE) AS effective_date,
    CAST(description AS VARCHAR) AS description,
    CAST(recommended_action AS VARCHAR) AS recommended_action
FROM raw_product_events;
