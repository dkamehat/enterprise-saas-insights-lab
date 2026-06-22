from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(page_title="Executive Portfolio", page_icon="📈", layout="wide")
st.title("Executive Portfolio")
st.caption("更新・拡張・競合防衛の候補Accountを、価値、勝ち筋、データ信頼度で並べ替えます。")

if not database_ready():
    st.error("先にトップページでデモ環境を構築してください。")
    st.stop()

portfolio = read_df("SELECT * FROM account_positioning")

st.info(
    "ここでは全Accountを同じ優先度で扱わず、Expected value、Sales Play fit、"
    "Forecastに使えるデータ品質を組み合わせて営業・CSの集中先を決めます。"
)

f1, f2, f3, f4 = st.columns(4)
industry = f1.multiselect("Industry", sorted(portfolio["industry"].unique()), default=[])
business_model = f2.multiselect(
    "Business model", sorted(portfolio["customer_business_model"].unique()), default=[]
)
theater = f3.multiselect("Theater", sorted(portfolio["sales_theater"].unique()), default=[])
sales_group = f4.multiselect("Sales group", sorted(portfolio["sales_group"].unique()), default=[])

g1, g2, g3, g4 = st.columns(4)
segment = g1.multiselect("Segment", sorted(portfolio["segment"].unique()), default=[])
region = g2.multiselect("Region", sorted(portfolio["region"].unique()), default=[])
ae = g3.multiselect("AE / member", sorted(portfolio["ae_name"].unique()), default=[])
priority = g4.multiselect("Priority", ["High", "Medium", "Low"], default=["High", "Medium"])

filtered = portfolio.copy()
if industry:
    filtered = filtered[filtered["industry"].isin(industry)]
if business_model:
    filtered = filtered[filtered["customer_business_model"].isin(business_model)]
if theater:
    filtered = filtered[filtered["sales_theater"].isin(theater)]
if sales_group:
    filtered = filtered[filtered["sales_group"].isin(sales_group)]
if segment:
    filtered = filtered[filtered["segment"].isin(segment)]
if region:
    filtered = filtered[filtered["region"].isin(region)]
if ae:
    filtered = filtered[filtered["ae_name"].isin(ae)]
if priority:
    filtered = filtered[filtered["priority_band"].isin(priority)]

m1, m2, m3, m4 = st.columns(4)
m1.metric("対象Accounts", f"{len(filtered):,}")
m2.metric("High priority", f"{(filtered['priority_band'] == 'High').sum():,}")
m3.metric(
    "Expected value", format_jpy_mn(float(filtered["expected_commercial_value_jpy_mn"].sum()))
)
m4.metric(
    "平均Data confidence",
    f"{filtered['data_confidence_pct'].mean():.1f}%" if len(filtered) else "-",
)

left, right = st.columns(2)
with left:
    st.subheader("Sales Play別Expected Value")
    st.caption("どの提案テーマが商業価値を作っているかを確認します。")
    by_play = (
        filtered.groupby("recommended_play", as_index=False)["expected_commercial_value_jpy_mn"]
        .sum()
        .sort_values("expected_commercial_value_jpy_mn", ascending=False)
    )
    st.plotly_chart(
        px.bar(
            by_play,
            x="recommended_play",
            y="expected_commercial_value_jpy_mn",
            labels={
                "recommended_play": "Sales Play",
                "expected_commercial_value_jpy_mn": "Expected value (JPY mn)",
            },
        ),
        use_container_width=True,
    )
with right:
    st.subheader("Priority × Governance")
    st.caption("High priorityでもEvidence requiredなら、Commit前に照合タスクへ回します。")
    matrix = filtered.groupby(["priority_band", "governance_status"], as_index=False).size()
    st.plotly_chart(
        px.bar(
            matrix,
            x="priority_band",
            y="size",
            color="governance_status",
            barmode="group",
            labels={"size": "Accounts", "priority_band": "Priority"},
        ),
        use_container_width=True,
    )

st.subheader("Global Portfolio And Sales Coverage")
st.markdown(
    "Use this view to compare industry, business model, sales theater, sales group, "
    "and owner coverage while keeping physical/hybrid portfolio mix and software "
    "subscription mix visible for renewal and expansion planning."
)
st.caption(
    "グローバル地域、営業グループ、業種・業態で見たときに、どこへ支援と監査を寄せるべきかを見ます。"
)
coverage_left, coverage_right = st.columns(2)
with coverage_left:
    by_group = (
        filtered.groupby(["sales_theater", "sales_group", "governance_status"], as_index=False)
        .agg(
            accounts=("account_id", "count"),
            expected_value=("expected_commercial_value_jpy_mn", "sum"),
        )
        .sort_values("expected_value", ascending=False)
    )
    st.plotly_chart(
        px.bar(
            by_group,
            x="sales_group",
            y="expected_value",
            color="governance_status",
            facet_col="sales_theater",
            labels={"expected_value": "Expected value (JPY mn)", "sales_group": "Sales group"},
        ),
        use_container_width=True,
    )
with coverage_right:
    industry_model = (
        filtered.groupby(["industry", "customer_business_model"], as_index=False)
        .agg(
            accounts=("account_id", "count"),
            avg_priority=("priority_score", "mean"),
            expected_value=("expected_commercial_value_jpy_mn", "sum"),
        )
        .sort_values("expected_value", ascending=False)
    )
    st.dataframe(
        industry_model.head(30),
        use_container_width=True,
        hide_index=True,
        column_config={
            "avg_priority": st.column_config.NumberColumn("Avg priority", format="%.1f"),
            "expected_value": st.column_config.NumberColumn(
                "Expected value (JPY mn)", format="%.1f"
            ),
        },
    )

st.subheader("Top Account Playbook")
st.caption("AEが次に見るべきAccountと、会話の入口になるNext Best Actionです。")
columns = [
    "account_name",
    "industry",
    "customer_business_model",
    "segment",
    "sales_theater",
    "sales_group",
    "ae_name",
    "strategic_tier",
    "priority_score",
    "recommended_play",
    "primary_competitor",
    "portfolio_domain_count",
    "physical_or_hybrid_pct",
    "software_subscription_pct",
    "expected_commercial_value_jpy_mn",
    "data_confidence_pct",
    "governance_status",
    "next_best_action",
]
st.dataframe(
    filtered.sort_values("priority_score", ascending=False)[columns].head(50),
    use_container_width=True,
    hide_index=True,
    column_config={
        "expected_commercial_value_jpy_mn": st.column_config.NumberColumn(
            "Expected value (JPY mn)", format="%.1f"
        ),
        "priority_score": st.column_config.ProgressColumn(
            "Priority", min_value=0, max_value=100, format="%.1f"
        ),
        "data_confidence_pct": st.column_config.ProgressColumn(
            "Data confidence", min_value=0, max_value=100, format="%.1f%%"
        ),
    },
)
