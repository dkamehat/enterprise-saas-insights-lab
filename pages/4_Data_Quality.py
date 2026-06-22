from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Data Quality", page_icon="🧹", layout="wide")
st.title("Data Quality & Asset Reconciliation")
st.caption("営業スピードを維持しつつ、未検証の契約・権利・利用データをForecastへ混入させません。")

if not database_ready():
    st.error("先にトップページでデモ環境を構築してください。")
    st.stop()

waterfall = read_df("SELECT * FROM reconciliation_waterfall ORDER BY step_order")
st.info(
    "Evidence requiredのAccountは営業対象から外すのではなく、Commit判断に必要な"
    "照合タスクとして扱います。"
    "この画面では、どのデータ欠損がForecastの根拠を弱くしているかを見ます。"
)
status = read_df(
    """
    SELECT reconciliation_status, COUNT(*) AS assets,
           AVG(asset_data_confidence_pct) AS avg_confidence
    FROM asset_reconciliation
    GROUP BY reconciliation_status
    ORDER BY assets DESC
    """
)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Reconciliation waterfall")
    st.caption("Subscription inventoryがForecast根拠として使える状態になるまでの落ちどころです。")
    st.plotly_chart(px.funnel(waterfall, x="asset_count", y="step"), use_container_width=True)
with c2:
    st.subheader("Verified / Reconcilable / Unknown")
    st.caption("UnknownはCommitに入れず、照合後に再評価します。")
    st.plotly_chart(px.bar(status, x="reconciliation_status", y="assets"), use_container_width=True)
    st.dataframe(status, use_container_width=True, hide_index=True)

issue_query = """
SELECT issue, SUM(issue_count) AS assets
FROM (
    SELECT 'Missing serial' AS issue, missing_serial_flag AS issue_count FROM asset_reconciliation
    UNION ALL SELECT 'Duplicate serial', duplicate_serial_flag FROM asset_reconciliation
    UNION ALL SELECT 'Missing contract', missing_contract_flag FROM asset_reconciliation
    UNION ALL SELECT 'Orphan contract', orphan_contract_flag FROM asset_reconciliation
    UNION ALL
    SELECT 'Contract-account mismatch', contract_account_mismatch_flag
    FROM asset_reconciliation
    UNION ALL SELECT 'Missing entitlement', missing_entitlement_flag FROM asset_reconciliation
    UNION ALL SELECT 'Orphan entitlement', orphan_entitlement_flag FROM asset_reconciliation
    UNION ALL
    SELECT 'Entitlement-account mismatch', entitlement_account_mismatch_flag
    FROM asset_reconciliation
    UNION ALL SELECT 'Stale verification', stale_verification_flag FROM asset_reconciliation
)
GROUP BY issue
ORDER BY assets DESC
"""
issues = read_df(issue_query)
st.subheader("Issue backlog")
st.caption("最初に潰すべきデータ品質課題を件数順に確認します。")
st.dataframe(issues, use_container_width=True, hide_index=True)

st.subheader("Accounts requiring evidence before forecast")
st.caption("商業価値があっても、証拠が足りないAccountはUpside/Riskとして分けます。")
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

with st.expander("Unknown asset sample"):
    unknown = read_df(
        """
        SELECT account_id, asset_id, serial_number, vendor, product_family, model,
               contract_id, entitlement_id, asset_data_confidence_pct, issue_summary
        FROM asset_reconciliation
        WHERE reconciliation_status = 'Unknown'
        ORDER BY asset_data_confidence_pct, account_id
        LIMIT 500
        """
    )
    st.dataframe(unknown, use_container_width=True, hide_index=True)
