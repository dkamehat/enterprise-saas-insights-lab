CREATE OR REPLACE TABLE asset_reconciliation AS
WITH serial_counts AS (
    SELECT serial_number, COUNT(*) AS serial_count
    FROM stg_assets
    WHERE serial_number IS NOT NULL
    GROUP BY serial_number
), joined AS (
    SELECT
        a.*,
        COALESCE(sc.serial_count, 0) AS serial_count,
        c.account_id AS contract_account_id,
        c.status AS contract_status,
        c.end_date AS contract_end_date,
        e.account_id AS entitlement_account_id,
        e.end_date AS entitlement_end_date,
        CASE WHEN a.serial_number IS NULL THEN 1 ELSE 0 END AS missing_serial_flag,
        CASE WHEN COALESCE(sc.serial_count, 0) > 1 THEN 1 ELSE 0 END AS duplicate_serial_flag,
        CASE WHEN a.vendor = 'Primary SaaS Vendor' AND a.contract_id IS NULL THEN 1 ELSE 0 END AS missing_contract_flag,
        CASE WHEN a.contract_id IS NOT NULL AND c.contract_id IS NULL THEN 1 ELSE 0 END AS orphan_contract_flag,
        CASE WHEN c.contract_id IS NOT NULL AND c.account_id <> a.account_id THEN 1 ELSE 0 END AS contract_account_mismatch_flag,
        CASE
            WHEN a.vendor = 'Primary SaaS Vendor'
             AND a.product_family IN ('Security Suite', 'Observability', 'Collaboration')
             AND a.entitlement_id IS NULL THEN 1 ELSE 0
        END AS missing_entitlement_flag,
        CASE WHEN a.entitlement_id IS NOT NULL AND e.entitlement_id IS NULL THEN 1 ELSE 0 END AS orphan_entitlement_flag,
        CASE WHEN e.entitlement_id IS NOT NULL AND e.account_id <> a.account_id THEN 1 ELSE 0 END AS entitlement_account_mismatch_flag,
        CASE WHEN a.last_verified_date IS NULL OR a.last_verified_date < DATE '2025-06-21' THEN 1 ELSE 0 END AS stale_verification_flag
    FROM stg_assets a
    LEFT JOIN serial_counts sc USING (serial_number)
    LEFT JOIN stg_contracts c ON a.contract_id = c.contract_id
    LEFT JOIN stg_entitlements e ON a.entitlement_id = e.entitlement_id
), scored AS (
    SELECT
        *,
        missing_serial_flag
        + duplicate_serial_flag
        + missing_contract_flag
        + orphan_contract_flag
        + contract_account_mismatch_flag
        + missing_entitlement_flag
        + orphan_entitlement_flag
        + entitlement_account_mismatch_flag
        + stale_verification_flag AS issue_count,
        GREATEST(
            0,
            100
            - 35 * missing_serial_flag
            - 30 * duplicate_serial_flag
            - 15 * missing_contract_flag
            - 25 * orphan_contract_flag
            - 35 * contract_account_mismatch_flag
            - 12 * missing_entitlement_flag
            - 20 * orphan_entitlement_flag
            - 30 * entitlement_account_mismatch_flag
            - 10 * stale_verification_flag
        ) AS asset_data_confidence_pct
    FROM joined
)
SELECT
    *,
    CASE
        WHEN issue_count = 0 THEN 'Verified'
        WHEN missing_serial_flag = 0
         AND duplicate_serial_flag = 0
         AND contract_account_mismatch_flag = 0
         AND entitlement_account_mismatch_flag = 0
         AND issue_count <= 2 THEN 'Reconcilable'
        ELSE 'Unknown'
    END AS reconciliation_status,
    CONCAT_WS(
        '; ',
        CASE WHEN missing_serial_flag = 1 THEN 'Missing serial' END,
        CASE WHEN duplicate_serial_flag = 1 THEN 'Duplicate serial' END,
        CASE WHEN missing_contract_flag = 1 THEN 'Missing contract' END,
        CASE WHEN orphan_contract_flag = 1 THEN 'Orphan contract reference' END,
        CASE WHEN contract_account_mismatch_flag = 1 THEN 'Contract-account mismatch' END,
        CASE WHEN missing_entitlement_flag = 1 THEN 'Missing entitlement' END,
        CASE WHEN orphan_entitlement_flag = 1 THEN 'Orphan entitlement reference' END,
        CASE WHEN entitlement_account_mismatch_flag = 1 THEN 'Entitlement-account mismatch' END,
        CASE WHEN stale_verification_flag = 1 THEN 'Stale verification' END
    ) AS issue_summary
FROM scored;
