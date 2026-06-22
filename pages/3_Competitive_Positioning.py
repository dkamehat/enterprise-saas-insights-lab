from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from cisco_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Competitive Positioning", page_icon="⚔️", layout="wide")
st.title("Competitive Positioning")
st.caption("Ciscoが勝てる条件と、営業工数を投下すべきAccountを分離")

if not database_ready():
    st.error("先にトップページでデモ環境を構築してください。")
    st.stop()

frame = read_df("SELECT * FROM account_positioning")
play = st.selectbox("Sales Play", ["All"] + sorted(frame["recommended_play"].unique().tolist()))
competitor = st.selectbox(
    "Competitor", ["All"] + sorted(frame["primary_competitor"].unique().tolist())
)

filtered = frame.copy()
if play != "All":
    filtered = filtered[filtered["recommended_play"] == play]
if competitor != "All":
    filtered = filtered[filtered["primary_competitor"] == competitor]

st.subheader("Positioning matrix")
fig = px.scatter(
    filtered,
    x="play_fit_score",
    y="competitive_pressure_pct",
    size="expected_commercial_value_jpy_mn",
    color="recommended_play",
    hover_name="account_name",
    hover_data=["primary_competitor", "priority_score", "data_confidence_pct", "governance_status"],
    labels={
        "play_fit_score": "Cisco sales-play fit",
        "competitive_pressure_pct": "Competitive pressure",
        "expected_commercial_value_jpy_mn": "Expected value",
    },
    size_max=45,
)
fig.add_vline(x=70, line_dash="dash")
fig.add_hline(y=70, line_dash="dash")
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "右上：高Fit・高競争圧力＝Defend/Accelerate。"
    "右下：Proactive expansion。左上：選別または別ポジショニング。"
)

st.subheader("Account-level positioning")
columns = [
    "account_name",
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
exposure = (
    filtered.groupby(["recommended_play", "primary_competitor"], as_index=False)
    .agg(
        accounts=("account_id", "count"), expected_value=("expected_commercial_value_jpy_mn", "sum")
    )
    .sort_values("expected_value", ascending=False)
)
st.dataframe(exposure, use_container_width=True, hide_index=True)
