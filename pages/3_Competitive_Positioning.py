from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Competitive Positioning", page_icon="⚔️", layout="wide")
st.title("Competitive Positioning")
st.caption(
    "Separate accounts under high competitive pressure by win-fit strength and commercial value."
)

if not database_ready():
    st.error("Build the demo warehouse on the home page first.")
    st.stop()

frame = read_df("SELECT * FROM account_positioning")
st.info(
    "Accounts toward the top-right have high sales-play fit but also high competitive pressure. "
    "Line up the value hypothesis and evidence early so the deal isn't reduced "
    "to a price comparison."
)
f1, f2, f3, f4 = st.columns(4)
play = f1.selectbox("Sales Play", ["All"] + sorted(frame["recommended_play"].unique().tolist()))
competitor = f2.selectbox(
    "Competitor", ["All"] + sorted(frame["primary_competitor"].unique().tolist())
)
theater = f3.selectbox("Theater", ["All"] + sorted(frame["sales_theater"].unique().tolist()))
sales_group = f4.selectbox(
    "Sales group", ["All"] + sorted(frame["sales_group"].unique().tolist())
)

g1, g2 = st.columns(2)
industry = g1.selectbox("Industry", ["All"] + sorted(frame["industry"].unique().tolist()))
business_model = g2.selectbox(
    "Business model", ["All"] + sorted(frame["customer_business_model"].unique().tolist())
)

filtered = frame.copy()
if play != "All":
    filtered = filtered[filtered["recommended_play"] == play]
if competitor != "All":
    filtered = filtered[filtered["primary_competitor"] == competitor]
if theater != "All":
    filtered = filtered[filtered["sales_theater"] == theater]
if sales_group != "All":
    filtered = filtered[filtered["sales_group"] == sales_group]
if industry != "All":
    filtered = filtered[filtered["industry"] == industry]
if business_model != "All":
    filtered = filtered[filtered["customer_business_model"] == business_model]

st.subheader("Positioning matrix")
fig = px.scatter(
    filtered,
    x="play_fit_score",
    y="competitive_pressure_pct",
    size="expected_commercial_value_jpy_mn",
    color="recommended_play",
    hover_name="account_name",
    hover_data=[
        "industry",
        "sales_group",
        "primary_competitor",
        "priority_score",
        "data_confidence_pct",
        "governance_status",
    ],
    labels={
        "play_fit_score": "Primary vendor sales-play fit",
        "competitive_pressure_pct": "Competitive pressure",
        "expected_commercial_value_jpy_mn": "Expected value",
    },
    size_max=45,
)
fig.add_vline(x=70, line_dash="dash")
fig.add_hline(y=70, line_dash="dash")
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Top-right: high fit + high pressure = Defend/Accelerate. "
    "Bottom-right: proactive expansion. Top-left: qualify out or re-position."
)

st.subheader("Account-level positioning")
st.caption("Per account, review the competitive talking points and the next action.")
columns = [
    "account_name",
    "industry",
    "sales_theater",
    "sales_group",
    "recommended_play",
    "primary_competitor",
    "play_fit_score",
    "competitive_pressure_pct",
    "priority_score",
    "estimated_tcv_jpy_mn",
    "data_confidence_pct",
    "positioning_angle",
    "next_best_action",
]
st.dataframe(
    filtered.sort_values(["priority_score", "competitive_pressure_pct"], ascending=False)[
        columns
    ].head(100),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Competitor exposure")
st.caption("By sales play, see which competitor themes may be pulling expected value down.")
exposure = (
    filtered.groupby(["recommended_play", "primary_competitor"], as_index=False)
    .agg(
        accounts=("account_id", "count"), expected_value=("expected_commercial_value_jpy_mn", "sum")
    )
    .sort_values("expected_value", ascending=False)
)
st.dataframe(exposure, use_container_width=True, hide_index=True)
