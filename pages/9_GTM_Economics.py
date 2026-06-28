from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(page_title="GTM Economics", page_icon="💹", layout="wide")
st.title("GTM Economics — Strategy & Operations view")
st.caption(
    "Time-aware SaaS efficiency from monthly first-principle drivers: ARR growth, "
    "retention, Rule of 40, Magic Number, CAC payback, LTV/CAC, and pipeline coverage."
)

if not database_ready():
    st.error("Build the demo warehouse on the home page first.")
    st.stop()

company = read_df("SELECT * FROM gtm_company_monthly ORDER BY month")
latest = company.iloc[-1]
segments = read_df("SELECT * FROM gtm_segment_latest")

# --- Benchmark-aware headline KPIs --------------------------------------------
st.subheader("Headline KPIs (latest month, trailing-twelve-month basis)")


def kpi(col, label: str, value: str, benchmark: str, good: bool | None) -> None:
    delta_color = "off" if good is None else ("normal" if good else "inverse")
    col.metric(label, value, benchmark, delta_color=delta_color)


r1 = st.columns(4)
kpi(r1[0], "ARR", format_jpy_mn(float(latest["ending_arr_jpy_mn"])), "synthetic", None)
kpi(
    r1[1],
    "ARR growth (YoY)",
    f"{latest['arr_growth_yoy_pct']:.0f}%",
    "vs ~30% healthy",
    latest["arr_growth_yoy_pct"] >= 30,
)
kpi(
    r1[2],
    "Net revenue retention",
    f"{latest['nrr_ttm_pct']:.0f}%",
    "vs 110% best-in-class",
    latest["nrr_ttm_pct"] >= 110,
)
kpi(
    r1[3],
    "Gross revenue retention",
    f"{latest['grr_ttm_pct']:.0f}%",
    "vs 90% target",
    latest["grr_ttm_pct"] >= 90,
)

r2 = st.columns(4)
kpi(
    r2[0],
    "Rule of 40",
    f"{latest['rule_of_40_pct']:.0f}",
    "vs 40 threshold",
    latest["rule_of_40_pct"] >= 40,
)
kpi(
    r2[1],
    "Magic Number",
    f"{latest['magic_number']:.2f}",
    "vs 0.75 efficient",
    latest["magic_number"] >= 0.75,
)
kpi(
    r2[2],
    "CAC payback",
    f"{latest['cac_payback_months']:.0f} mo",
    "vs <18 mo target",
    latest["cac_payback_months"] <= 18,
)
kpi(
    r2[3],
    "LTV / CAC",
    f"{latest['ltv_to_cac']:.1f}x",
    "vs 3x+ healthy",
    latest["ltv_to_cac"] >= 3,
)

# --- Executive read -----------------------------------------------------------
ro40 = float(latest["rule_of_40_pct"])
nrr = float(latest["nrr_ttm_pct"])
payback = float(latest["cac_payback_months"])
st.info(
    f"**Executive read.** The business is compounding at "
    f"{latest['arr_growth_yoy_pct']:.0f}% YoY with a Rule of 40 of {ro40:.0f} — growth "
    f"is efficient, not bought. NRR of {nrr:.0f}% means the installed base expands "
    f"faster than it leaks, so retention (not net-new logos) is the primary ARR engine. "
    f"With CAC payback at {payback:.0f} months and LTV/CAC above 3x, sales capacity is "
    "the constraint worth funding next. Public Sector carries the strongest GRR; "
    "Commercial trades retention for speed — the place to tighten onboarding."
)

# --- ARR bridge (trailing twelve months) --------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("ARR bridge — trailing 12 months")
    st.caption("Where net-new ARR comes from: new logos, expansion, contraction, churn.")
    last12 = company.tail(12)
    opening = float(company.iloc[-13]["ending_arr_jpy_mn"]) if len(company) >= 13 else float(
        company.iloc[0]["starting_arr_jpy_mn"]
    )
    bridge = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Opening ARR", "New", "Expansion", "Contraction", "Churn", "Ending ARR"],
            y=[
                opening,
                float(last12["new_arr_jpy_mn"].sum()),
                float(last12["expansion_arr_jpy_mn"].sum()),
                -float(last12["contraction_arr_jpy_mn"].sum()),
                -float(last12["churned_arr_jpy_mn"].sum()),
                float(latest["ending_arr_jpy_mn"]),
            ],
            connector={"line": {"color": "rgb(150,150,150)"}},
        )
    )
    bridge.update_layout(showlegend=False, yaxis_title="ARR (JPY mn)", height=380)
    st.plotly_chart(bridge, use_container_width=True)

with right:
    st.subheader("ARR & growth trajectory")
    st.caption("ARR scale alongside the YoY growth rate.")
    trend = go.Figure()
    trend.add_bar(x=company["month"], y=company["ending_arr_jpy_mn"], name="ARR (JPY mn)")
    trend.add_trace(
        go.Scatter(
            x=company["month"],
            y=company["arr_growth_yoy_pct"],
            name="YoY growth %",
            yaxis="y2",
            mode="lines",
        )
    )
    trend.update_layout(
        height=380,
        yaxis_title="ARR (JPY mn)",
        yaxis2={"title": "YoY %", "overlaying": "y", "side": "right"},
        legend={"orientation": "h", "y": 1.1},
    )
    st.plotly_chart(trend, use_container_width=True)

# --- Rule of 40 and retention -------------------------------------------------
left2, right2 = st.columns(2)
with left2:
    st.subheader("Rule of 40 decomposition")
    st.caption("Growth + operating margin. The 40 line separates efficient from not.")
    roll = company.dropna(subset=["rule_of_40_pct"])
    fig = go.Figure()
    fig.add_bar(x=roll["month"], y=roll["arr_growth_yoy_pct"], name="Growth %")
    fig.add_bar(x=roll["month"], y=roll["operating_margin_ttm_pct"], name="Op margin %")
    fig.add_trace(
        go.Scatter(x=roll["month"], y=roll["rule_of_40_pct"], name="Rule of 40", mode="lines")
    )
    fig.add_hline(y=40, line_dash="dash", line_color="gray")
    fig.update_layout(barmode="relative", height=360, legend={"orientation": "h", "y": 1.12})
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader("Retention & sales efficiency")
    st.caption("NRR/GRR with the Magic Number trend.")
    eff = company.dropna(subset=["nrr_ttm_pct"])
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=eff["month"], y=eff["nrr_ttm_pct"], name="NRR %", mode="lines"))
    fig2.add_trace(go.Scatter(x=eff["month"], y=eff["grr_ttm_pct"], name="GRR %", mode="lines"))
    fig2.add_trace(
        go.Scatter(
            x=eff["month"],
            y=eff["magic_number"],
            name="Magic Number",
            yaxis="y2",
            mode="lines",
        )
    )
    fig2.add_hline(y=100, line_dash="dot", line_color="gray")
    fig2.update_layout(
        height=360,
        yaxis_title="Retention %",
        yaxis2={"title": "Magic Number", "overlaying": "y", "side": "right"},
        legend={"orientation": "h", "y": 1.12},
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Segment economics --------------------------------------------------------
st.subheader("Segment economics (latest month)")
st.caption("Where the ARR sits and which motion is most efficient to scale.")
seg_cols = [
    "segment",
    "ending_arr_jpy_mn",
    "arr_growth_yoy_pct",
    "nrr_ttm_pct",
    "grr_ttm_pct",
    "magic_number",
    "cac_payback_months",
    "ltv_to_cac",
    "win_rate_pct",
    "pipeline_coverage_x",
]
st.dataframe(
    segments[seg_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ending_arr_jpy_mn": st.column_config.NumberColumn("ARR (JPY mn)", format="%.0f"),
        "arr_growth_yoy_pct": st.column_config.NumberColumn("Growth %", format="%.0f"),
        "nrr_ttm_pct": st.column_config.NumberColumn("NRR %", format="%.0f"),
        "grr_ttm_pct": st.column_config.NumberColumn("GRR %", format="%.0f"),
        "magic_number": st.column_config.NumberColumn("Magic #", format="%.2f"),
        "cac_payback_months": st.column_config.NumberColumn("CAC payback (mo)", format="%.0f"),
        "ltv_to_cac": st.column_config.NumberColumn("LTV/CAC", format="%.1fx"),
        "win_rate_pct": st.column_config.NumberColumn("Win rate %", format="%.0f"),
        "pipeline_coverage_x": st.column_config.NumberColumn("Pipeline cov.", format="%.1fx"),
    },
)

st.caption(
    "All figures are synthetic and reconstructed from monthly drivers in "
    "`saas_insights.gtm`. Benchmarks shown are common SaaS rules of thumb, not targets."
)
