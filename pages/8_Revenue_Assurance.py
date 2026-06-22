from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(page_title="Revenue Assurance", page_icon="RA", layout="wide")
st.title("Revenue Assurance")
st.caption(
    "NRR decomposition and True Forward exposure for renewal and expansion reviews."
)

if not database_ready():
    st.error("Build the demo warehouse from the top page first.")
    st.stop()

nrr = read_df("SELECT * FROM nrr_decomposition")
true_forward = read_df("SELECT * FROM true_forward_exposure")

total_opening = float(nrr["opening_arr_jpy_mn"].sum())
total_churn = float(nrr["churn_risk_jpy_mn"].sum())
total_contraction = float(nrr["contraction_risk_jpy_mn"].sum())
total_expansion = float(nrr["expansion_potential_jpy_mn"].sum())
ending = max(0.0, total_opening - total_churn - total_contraction + total_expansion)
modeled_nrr = 100.0 * ending / total_opening if total_opening else 0.0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Opening ARR", format_jpy_mn(total_opening))
m2.metric("Churn risk", format_jpy_mn(total_churn))
m3.metric("Contraction risk", format_jpy_mn(total_contraction))
m4.metric("Expansion potential", format_jpy_mn(total_expansion))
m5.metric("Modeled NRR", f"{modeled_nrr:.1f}%")

st.subheader("NRR Bridge")
bridge = [
    {"component": "Opening ARR", "jpy_mn": total_opening},
    {"component": "Churn risk", "jpy_mn": -total_churn},
    {"component": "Contraction risk", "jpy_mn": -total_contraction},
    {"component": "Expansion potential", "jpy_mn": total_expansion},
    {"component": "Modeled ending ARR", "jpy_mn": ending},
]
st.plotly_chart(
    px.bar(
        bridge,
        x="component",
        y="jpy_mn",
        labels={"jpy_mn": "JPY mn", "component": "NRR component"},
    ),
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    st.subheader("NRR By Sales Group")
    by_group = (
        nrr.groupby("sales_group", as_index=False)
        .agg(
            opening_arr=("opening_arr_jpy_mn", "sum"),
            churn=("churn_risk_jpy_mn", "sum"),
            contraction=("contraction_risk_jpy_mn", "sum"),
            expansion=("expansion_potential_jpy_mn", "sum"),
        )
        .sort_values("opening_arr", ascending=False)
    )
    by_group["modeled_nrr_pct"] = (
        100.0
        * (by_group["opening_arr"] - by_group["churn"] - by_group["contraction"]
           + by_group["expansion"])
        / by_group["opening_arr"].clip(lower=1.0)
    )
    st.dataframe(by_group, use_container_width=True, hide_index=True)
with right:
    st.subheader("True Forward Exposure")
    tf_summary = {
        "exposed_accounts": int(true_forward["account_id"].nunique())
        if not true_forward.empty
        else 0,
        "exposed_assets": int(true_forward["exposed_assets"].sum())
        if not true_forward.empty
        else 0,
        "overage_units": float(true_forward["overage_units"].sum())
        if not true_forward.empty
        else 0.0,
        "exposure_jpy_mn": float(true_forward["exposure_jpy_mn"].sum())
        if not true_forward.empty
        else 0.0,
    }
    st.metric("Exposed accounts", f"{tf_summary['exposed_accounts']:,}")
    st.metric("Exposed assets", f"{tf_summary['exposed_assets']:,}")
    st.metric("True Forward exposure", format_jpy_mn(tf_summary["exposure_jpy_mn"]))

st.subheader("Account-Level Renewal And Expansion Queue")
columns = [
    "account_name",
    "segment",
    "sales_group",
    "ae_name",
    "priority_score",
    "recommended_play",
    "opening_arr_jpy_mn",
    "churn_risk_jpy_mn",
    "contraction_risk_jpy_mn",
    "expansion_potential_jpy_mn",
    "modeled_nrr_pct",
    "modeled_grr_pct",
    "governance_status",
]
st.dataframe(
    nrr.sort_values(["expansion_potential_jpy_mn", "opening_arr_jpy_mn"], ascending=False)[
        columns
    ].head(100),
    use_container_width=True,
    hide_index=True,
)

st.subheader("True Forward Account Queue")
st.caption("Consumed quantity is measured separately from entitled quantity.")
st.dataframe(
    true_forward.sort_values("exposure_jpy_mn", ascending=False).head(100),
    use_container_width=True,
    hide_index=True,
)
