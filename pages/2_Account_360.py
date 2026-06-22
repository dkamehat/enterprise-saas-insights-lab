from __future__ import annotations

import json
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.config import load_scoring_config  # noqa: E402
from saas_insights.tco import calculate_tco  # noqa: E402
from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(page_title="Account 360", page_icon="🎯", layout="wide")
st.title("Account 360")
st.caption("契約、利用率、競合、更新、データ品質を一つのAccountストーリーへ変換します。")

if not database_ready():
    st.error("先にトップページでデモ環境を構築してください。")
    st.stop()

accounts = read_df(
    "SELECT account_id, account_name, priority_score "
    "FROM account_positioning ORDER BY priority_score DESC"
)
labels = {f"{r.account_name} [{r.account_id}]": r.account_id for r in accounts.itertuples()}
selected_label = st.selectbox("Account", list(labels))
account_id = labels[selected_label]

row = read_df("SELECT * FROM account_positioning WHERE account_id = ?", [account_id]).iloc[0]

st.info(
    "この画面はAE/CSMが顧客会話の準備に使う想定です。"
    "推奨Play、根拠となるDriver、未検証データ、競合ポジション、TCO仮説を一画面にまとめます。"
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Priority", f"{row['priority_score']:.1f}", row["priority_band"])
m2.metric("Recommended play", row["recommended_play"])
m3.metric("Primary competitor", row["primary_competitor"])
m4.metric("Expected value", format_jpy_mn(float(row["expected_commercial_value_jpy_mn"])))
m5.metric("Data confidence", f"{row['data_confidence_pct']:.1f}%")

st.subheader("AE向けData Story")
st.success(row["data_story"])

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Competitive positioning**")
    st.caption("競合比較で何を論点にすべきかを短く示します。")
    st.write(row["positioning_angle"])
with c2:
    st.markdown("**Next Best Action**")
    st.caption("次回顧客接点までに実行すべき確認・提案準備です。")
    st.write(row["next_best_action"])

with st.expander("スコア根拠・Forecast governance"):
    drivers = json.loads(row["score_drivers_json"])
    driver_frame = {"Driver": list(drivers), "Contribution": list(drivers.values())}
    st.dataframe(driver_frame, use_container_width=True, hide_index=True)
    st.write(f"**Governance:** {row['governance_status']}")
    st.write(row["forecast_recommendation"])

left, right = st.columns(2)
with left:
    st.subheader("Asset reconciliation")
    st.caption("Forecastの根拠に使えるSubscription inventoryかどうかを確認します。")
    reconciliation = read_df(
        """
        SELECT reconciliation_status, COUNT(*) AS assets,
               AVG(asset_data_confidence_pct) AS avg_confidence
        FROM asset_reconciliation
        WHERE account_id = ?
        GROUP BY reconciliation_status
        ORDER BY assets DESC
        """,
        [account_id],
    )
    st.plotly_chart(
        px.bar(reconciliation, x="reconciliation_status", y="assets"), use_container_width=True
    )
    st.dataframe(reconciliation, use_container_width=True, hide_index=True)
with right:
    st.subheader("Commercial profile")
    st.caption("契約・利用・更新の状態を、提案余地とリスクの両面から見ます。")
    profile = {
        "Metric": [
            "Industry",
            "Business model",
            "Sales theater",
            "Sales group",
            "Sales manager",
            "AE / member",
            "Route to market",
            "Global account",
            "Total assets",
            "Portfolio domains",
            "Deployment models",
            "Physical / hybrid mix",
            "Software subscription mix",
            "Primary SaaS Vendor Platform share",
            "Lifecycle / support transition within 18m",
            "Support gap",
            "180d renewal value",
            "Contract fragmentation",
            "Average adoption",
        ],
        "Value": [
            row["industry"],
            row["customer_business_model"],
            row["sales_theater"],
            row["sales_group"],
            row["sales_manager"],
            row["ae_name"],
            row["route_to_market"],
            "Yes" if bool(row["global_account_flag"]) else "No",
            f"{int(row['total_assets']):,}",
            f"{int(row['portfolio_domain_count'])}",
            f"{int(row['deployment_model_count'])}",
            f"{row['physical_or_hybrid_pct']:.1f}%",
            f"{row['software_subscription_pct']:.1f}%",
            f"{row['primary_platform_share_pct']:.1f}%",
            f"{row['eol_18m_pct']:.1f}%",
            f"{row['support_gap_pct']:.1f}%",
            format_jpy_mn(float(row["renewal_value_180d_jpy_mn"])),
            f"{row['contract_fragmentation_pct']:.1f}%",
            f"{row['avg_adoption_pct']:.1f}%",
        ],
    }
    st.dataframe(profile, use_container_width=True, hide_index=True)

st.subheader("3-year TCO scenario")
st.caption("競合が安く見える場合でも、移行、教育、二重運用、障害期待損失まで含めて比較します。")
t1, t2 = st.columns([1, 1])
competitor_discount = t1.slider(
    "Competitor product discount vs primary vendor baseline", 0, 40, 18, 1
)
years = t2.select_slider("Horizon", options=[1, 3, 5], value=3)
tco = calculate_tco(
    row, load_scoring_config(), competitor_discount_pct=competitor_discount, years=years
)
st.dataframe(tco, use_container_width=True, hide_index=True)
total_primary = float(tco["primary_jpy_mn"].sum())
total_competitor = float(tco["competitor_jpy_mn"].sum())
st.metric("Competitor minus primary-vendor TCO", format_jpy_mn(total_competitor - total_primary))
st.caption(
    "係数はデモ用の仮定です。実案件では見積、移行WBS、運用工数、障害期待損失で差し替えます。"
)

with st.expander("Contracts / competitor signals / opportunities"):
    contracts = read_df(
        "SELECT * FROM stg_contracts WHERE account_id = ? ORDER BY end_date", [account_id]
    )
    signals = read_df(
        "SELECT * FROM stg_competitor_signals WHERE account_id = ? "
        "ORDER BY signal_strength_pct DESC",
        [account_id],
    )
    opportunities = read_df(
        "SELECT * FROM stg_opportunities WHERE account_id = ? ORDER BY close_date", [account_id]
    )
    st.markdown("**Contracts**")
    st.dataframe(contracts, use_container_width=True, hide_index=True)
    st.markdown("**Competitor signals**")
    st.dataframe(signals, use_container_width=True, hide_index=True)
    st.markdown("**Opportunities**")
    st.dataframe(opportunities, use_container_width=True, hide_index=True)
