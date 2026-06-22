from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Data Quality", page_icon="DQ", layout="wide")
st.title("Data Quality & Planted-Signal Audit")
st.caption(
    "Move from asset-status reporting to measured defect recovery: planted truth, "
    "recall, false positives, and evidence queues."
)

if not database_ready():
    st.error("Build the demo warehouse from the top page first.")
    st.stop()

overall = read_df(
    """
    SELECT *
    FROM quality_signal_metrics
    WHERE planted_level = 'ALL' AND defect_type = 'ALL'
    """
).iloc[0]
by_type = read_df(
    """
    SELECT *
    FROM quality_signal_metrics
    WHERE defect_type <> 'ALL'
    ORDER BY planted_level, recall_pct ASC, fpr DESC, planted_count DESC
    """
)
manifest_summary = read_df(
    """
    SELECT planted_level, defect_type, COUNT(*) AS planted_signals
    FROM stg_planted_quality_signals
    GROUP BY planted_level, defect_type
    ORDER BY planted_level, planted_signals DESC
    """
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Known defects", f"{int(overall['planted_count']):,}")
m2.metric("Recovered", f"{int(overall['recovered_count']):,}")
m3.metric("Missed", f"{int(overall['missed_count']):,}")
m4.metric("Recall", f"{float(overall['recall_pct']):.2f}%")
m5.metric("FPR", f"{float(overall['fpr']):.4f}")

st.subheader("Planted Signal Recovery")
st.dataframe(
    by_type,
    use_container_width=True,
    hide_index=True,
    column_config={
        "recall_pct": st.column_config.ProgressColumn("Recall", min_value=0, max_value=100),
        "fpr": st.column_config.NumberColumn("FPR", format="%.5f"),
    },
)

left, right = st.columns(2)
with left:
    st.subheader("Truth Manifest")
    st.caption("Each row is a known defect the generator planted or labeled as ground truth.")
    st.plotly_chart(
        px.bar(
            manifest_summary,
            x="defect_type",
            y="planted_signals",
            color="planted_level",
            labels={"defect_type": "Defect type", "planted_signals": "Signals"},
        ),
        use_container_width=True,
    )
with right:
    st.subheader("Reconciliation Waterfall")
    waterfall = read_df("SELECT * FROM reconciliation_waterfall ORDER BY step_order")
    st.plotly_chart(px.funnel(waterfall, x="asset_count", y="step"), use_container_width=True)

status = read_df(
    """
    SELECT reconciliation_status, COUNT(*) AS assets,
           AVG(asset_data_confidence_pct) AS avg_confidence
    FROM asset_reconciliation
    GROUP BY reconciliation_status
    ORDER BY assets DESC
    """
)
st.subheader("Verified / Reconcilable / Unknown")
st.dataframe(status, use_container_width=True, hide_index=True)

issue_query = """
SELECT issue, SUM(issue_count) AS assets
FROM (
    SELECT 'Missing serial' AS issue, missing_serial_flag AS issue_count
    FROM asset_reconciliation
    UNION ALL SELECT 'Duplicate serial', duplicate_serial_flag FROM asset_reconciliation
    UNION ALL SELECT 'Missing contract', missing_contract_flag FROM asset_reconciliation
    UNION ALL SELECT 'Orphan contract', orphan_contract_flag FROM asset_reconciliation
    UNION ALL
    SELECT 'Contract-account mismatch', contract_account_mismatch_flag
    FROM asset_reconciliation
    UNION ALL SELECT 'Missing entitlement', missing_entitlement_flag
    FROM asset_reconciliation
    UNION ALL SELECT 'Orphan entitlement', orphan_entitlement_flag
    FROM asset_reconciliation
    UNION ALL
    SELECT 'Entitlement-account mismatch', entitlement_account_mismatch_flag
    FROM asset_reconciliation
    UNION ALL
    SELECT 'True Forward exposure', true_forward_exposure_flag
    FROM asset_reconciliation
    UNION ALL SELECT 'Stale verification', stale_verification_flag FROM asset_reconciliation
)
GROUP BY issue
ORDER BY assets DESC
"""
issues = read_df(issue_query)
st.subheader("Issue Backlog")
st.caption("Operational backlog by concrete rule, not just status labels.")
st.dataframe(issues, use_container_width=True, hide_index=True)

q1, q2 = st.columns(2)
with q1:
    st.subheader("Quality By Source System")
    source_quality = read_df(
        """
        SELECT source_system, reconciliation_status, COUNT(*) AS assets,
               AVG(asset_data_confidence_pct) AS avg_confidence
        FROM asset_reconciliation
        GROUP BY source_system, reconciliation_status
        ORDER BY source_system, assets DESC
        """
    )
    st.plotly_chart(
        px.bar(
            source_quality,
            x="source_system",
            y="assets",
            color="reconciliation_status",
            barmode="stack",
        ),
        use_container_width=True,
    )
with q2:
    st.subheader("Quality By Portfolio")
    portfolio_quality = read_df(
        """
        SELECT portfolio_domain, deployment_model, COUNT(*) AS assets,
               AVG(asset_data_confidence_pct) AS avg_confidence
        FROM asset_reconciliation
        GROUP BY portfolio_domain, deployment_model
        ORDER BY avg_confidence, assets DESC
        """
    )
    st.dataframe(portfolio_quality, use_container_width=True, hide_index=True)

st.subheader("Accounts Requiring Evidence Before Forecast")
accounts = read_df(
    """
    SELECT account_name, ae_name, priority_score, recommended_play,
           data_confidence_pct, unknown_assets_pct, renewal_value_180d_jpy_mn,
           governance_status, next_best_action
    FROM account_positioning
    WHERE governance_status = 'Evidence required'
    ORDER BY priority_score DESC, renewal_value_180d_jpy_mn DESC
    """
)
st.dataframe(accounts, use_container_width=True, hide_index=True)

with st.expander("False positive / missed signal samples"):
    samples = read_df(
        """
        SELECT e.asset_id, e.account_id, e.defect_type, e.planted_level,
               e.detected_flag, e.false_positive_flag, e.false_negative_flag,
               r.vendor, r.product_family, r.model, r.issue_summary
        FROM quality_signal_evaluation e
        LEFT JOIN asset_reconciliation r USING (asset_id)
        WHERE e.false_positive_flag = 1 OR e.false_negative_flag = 1
        ORDER BY e.false_negative_flag DESC, e.false_positive_flag DESC, e.defect_type
        LIMIT 500
        """
    )
    st.dataframe(samples, use_container_width=True, hide_index=True)
