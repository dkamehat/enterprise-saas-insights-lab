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
        e.license_quantity AS entitled_quantity,
        e.consumed_quantity,
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
        CASE
            WHEN e.entitlement_id IS NOT NULL
             AND COALESCE(e.consumed_quantity, 0) > COALESCE(e.license_quantity, 0)
            THEN 1 ELSE 0
        END AS true_forward_exposure_flag,
        GREATEST(
            0,
            COALESCE(e.consumed_quantity, 0) - COALESCE(e.license_quantity, 0)
        ) AS true_forward_overage_units,
        ROUND(
            GREATEST(
                0,
                COALESCE(e.consumed_quantity, 0) - COALESCE(e.license_quantity, 0)
            ) * 0.08,
            4
        ) AS true_forward_exposure_jpy_mn,
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
        CASE WHEN true_forward_exposure_flag = 1 THEN 'True Forward exposure' END,
        CASE WHEN stale_verification_flag = 1 THEN 'Stale verification' END
    ) AS issue_summary
FROM scored;

CREATE OR REPLACE TABLE asset_quality_detection_events AS
SELECT asset_id, account_id, 'missing_serial' AS defect_type,
       'missing_serial_flag' AS detected_flag_column, missing_serial_flag AS detected_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'duplicate_serial', 'duplicate_serial_flag', duplicate_serial_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'missing_contract', 'missing_contract_flag', missing_contract_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'orphan_contract', 'orphan_contract_flag', orphan_contract_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'contract_account_mismatch',
       'contract_account_mismatch_flag', contract_account_mismatch_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'missing_entitlement',
       'missing_entitlement_flag', missing_entitlement_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'orphan_entitlement',
       'orphan_entitlement_flag', orphan_entitlement_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'entitlement_account_mismatch',
       'entitlement_account_mismatch_flag', entitlement_account_mismatch_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'true_forward_overconsumption',
       'true_forward_exposure_flag', true_forward_exposure_flag
FROM asset_reconciliation
UNION ALL
SELECT asset_id, account_id, 'stale_verification',
       'stale_verification_flag', stale_verification_flag
FROM asset_reconciliation;

CREATE OR REPLACE TABLE quality_signal_evaluation AS
WITH planted AS (
    SELECT
        asset_id,
        account_id,
        defect_type,
        expected_flag_column,
        planted_level,
        COUNT(*) AS planted_count
    FROM stg_planted_quality_signals
    GROUP BY
        asset_id,
        account_id,
        defect_type,
        expected_flag_column,
        planted_level
)
SELECT
    d.asset_id,
    d.account_id,
    d.defect_type,
    d.detected_flag_column,
    COALESCE(p.expected_flag_column, d.detected_flag_column) AS expected_flag_column,
    COALESCE(p.planted_level, 'Not planted') AS planted_level,
    CASE WHEN COALESCE(p.planted_count, 0) > 0 THEN 1 ELSE 0 END AS planted_flag,
    d.detected_flag,
    CASE
        WHEN COALESCE(p.planted_count, 0) > 0 AND d.detected_flag = 1 THEN 1 ELSE 0
    END AS true_positive_flag,
    CASE
        WHEN COALESCE(p.planted_count, 0) > 0 AND d.detected_flag = 0 THEN 1 ELSE 0
    END AS false_negative_flag,
    CASE
        WHEN COALESCE(p.planted_count, 0) = 0 AND d.detected_flag = 1 THEN 1 ELSE 0
    END AS false_positive_flag,
    CASE
        WHEN COALESCE(p.planted_count, 0) = 0 AND d.detected_flag = 0 THEN 1 ELSE 0
    END AS true_negative_flag
FROM asset_quality_detection_events d
LEFT JOIN planted p
    ON p.asset_id = d.asset_id
   AND p.defect_type = d.defect_type;

CREATE OR REPLACE TABLE quality_signal_metrics AS
WITH planted_metrics AS (
    SELECT
        planted_level,
        defect_type,
        COUNT(*) AS planted_count,
        SUM(true_positive_flag) AS recovered_count,
        SUM(false_negative_flag) AS missed_count
    FROM quality_signal_evaluation
    WHERE planted_flag = 1
    GROUP BY planted_level, defect_type
), false_positive_metrics AS (
    SELECT
        defect_type,
        SUM(false_positive_flag) AS false_positive_count,
        SUM(CASE WHEN planted_flag = 0 THEN 1 ELSE 0 END) AS non_planted_count
    FROM quality_signal_evaluation
    GROUP BY defect_type
), by_level AS (
    SELECT
        p.planted_level,
        p.defect_type,
        p.planted_count,
        p.recovered_count,
        p.missed_count,
        COALESCE(f.false_positive_count, 0) AS false_positive_count,
        COALESCE(f.non_planted_count, 0) AS non_planted_count
    FROM planted_metrics p
    LEFT JOIN false_positive_metrics f USING (defect_type)
), overall AS (
    SELECT
        'ALL' AS planted_level,
        'ALL' AS defect_type,
        SUM(planted_flag) AS planted_count,
        SUM(true_positive_flag) AS recovered_count,
        SUM(false_negative_flag) AS missed_count,
        SUM(false_positive_flag) AS false_positive_count,
        SUM(CASE WHEN planted_flag = 0 THEN 1 ELSE 0 END) AS non_planted_count
    FROM quality_signal_evaluation
)
SELECT
    planted_level,
    defect_type,
    planted_count,
    recovered_count,
    missed_count,
    false_positive_count,
    non_planted_count,
    ROUND(100.0 * recovered_count / NULLIF(planted_count, 0), 3) AS recall_pct,
    ROUND(1.0 * false_positive_count / NULLIF(non_planted_count, 0), 5) AS fpr
FROM by_level
UNION ALL
SELECT
    planted_level,
    defect_type,
    planted_count,
    recovered_count,
    missed_count,
    false_positive_count,
    non_planted_count,
    ROUND(100.0 * recovered_count / NULLIF(planted_count, 0), 3) AS recall_pct,
    ROUND(1.0 * false_positive_count / NULLIF(non_planted_count, 0), 5) AS fpr
FROM overall;
