from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.briefing import build_grounded_account_brief, validate_grounding  # noqa: E402
from saas_insights.config import load_scoring_config  # noqa: E402
from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Model Governance", page_icon="MG", layout="wide")
st.title("Model Governance")
st.caption(
    "Trace score weights, calibration, grounded briefing, and human decision boundaries."
)

if not database_ready():
    st.error("Build the demo warehouse from the top page first.")
    st.stop()

config = load_scoring_config()
weights_rows = []
for model, weights in config["weights"].items():
    for feature, weight in weights.items():
        weights_rows.append({"model": model, "feature": feature, "weight": weight})
weights_df = pd.DataFrame(weights_rows)

calibration = read_df("SELECT * FROM forecast_calibration")
calibration_summary = read_df("SELECT * FROM forecast_calibration_summary").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Closed opps", f"{int(calibration_summary['closed_opportunities']):,}")
c2.metric("Avg Brier", f"{float(calibration_summary['avg_brier_score']):.3f}")
c3.metric("Avg calibration gap", f"{float(calibration_summary['avg_calibration_gap_pct']):.1f}%")
c4.metric("Max calibration gap", f"{float(calibration_summary['max_calibration_gap_pct']):.1f}%")

weights_tab, calibration_tab, brief_tab, lens_tab = st.tabs(
    ["Weights & Controls", "Calibration", "Grounded Brief", "Interview Lens"]
)

with weights_tab:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Business-Owned Score Weights")
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Decision Boundaries")
        st.json(config["thresholds"])

    st.subheader("Control Design")
    st.dataframe(
        {
            "Layer": ["Deterministic logic", "Grounded brief", "Human approval", "Audit"],
            "Allowed": [
                "Asset reconciliation, bounded scores, TCV formulas, and priority ranking",
                "Evidence-cited stakeholder draft using governed account and asset rows",
                "Pricing, discounting, entitlement action, and forecast commit decisions",
                "Input records, manifest truth, rule versions, score drivers, and citations",
            ],
            "Constrained": [
                "No ungrounded forecast or pricing recommendation",
                "No external model call in the public demo and no unsupported claims",
                "No commit forecast when evidence threshold is not met",
                "No manual override without traceable evidence",
            ],
        },
        use_container_width=True,
        hide_index=True,
    )

with calibration_tab:
    st.subheader("Probability Calibration")
    st.caption("Closed Won/Lost outcomes are compared with modeled win probability buckets.")
    st.plotly_chart(
        px.line(
            calibration,
            x="probability_bucket",
            y=["avg_predicted_probability_pct", "actual_win_rate_pct"],
            markers=True,
            labels={
                "probability_bucket": "Predicted probability bucket",
                "value": "Percent",
                "variable": "Series",
            },
        ),
        use_container_width=True,
    )
    st.dataframe(calibration, use_container_width=True, hide_index=True)

with brief_tab:
    st.subheader("Grounded Account Brief")
    accounts = read_df(
        """
        SELECT *
        FROM account_positioning
        ORDER BY priority_score DESC
        LIMIT 50
        """
    )
    selected_account = st.selectbox(
        "Account",
        accounts["account_id"].tolist(),
        format_func=lambda account_id: accounts.set_index("account_id").loc[
            account_id, "account_name"
        ],
    )
    account_row = accounts[accounts["account_id"] == selected_account].iloc[0].to_dict()
    evidence = read_df(
        """
        SELECT asset_id, account_id, asset_data_confidence_pct, issue_summary
        FROM asset_reconciliation
        WHERE account_id = ?
          AND issue_summary IS NOT NULL
          AND issue_summary <> ''
        ORDER BY asset_data_confidence_pct ASC
        LIMIT 5
        """,
        [selected_account],
    )
    evidence_rows = evidence.to_dict("records")
    brief = build_grounded_account_brief(account_row, evidence_rows)
    allowed = {f"account_positioning:{selected_account}"} | {
        f"asset_reconciliation:{row['asset_id']}" for row in evidence_rows
    }

    st.success(f"Grounding check: {validate_grounding(brief, allowed)}")
    st.json(brief)
    st.dataframe(evidence, use_container_width=True, hide_index=True)

with lens_tab:
    st.subheader("Vendor-Neutral Interview Lens")
    st.caption(
        "The data remains generic. This table translates the demo vocabulary into "
        "enterprise SaaS / networking portfolio-management language."
    )
    st.dataframe(
        {
            "Demo term": [
                "Primary SaaS Vendor",
                "Enterprise Plan",
                "Renewal / Enterprise Plan",
                "True Forward exposure",
                "Asset reconciliation",
                "Forecast-ready",
                "Grounded brief",
            ],
            "Interview lens": [
                "Incumbent strategic vendor footprint",
                "Enterprise agreement or portfolio-wide subscription construct",
                "ARR/NRR motion with churn, contraction, and expansion review",
                "Consumption above entitlement requiring commercial review",
                "Install base, entitlement, contract, and account alignment",
                "Evidence quality is sufficient for scenario forecast review",
                "Agentic summary constrained to cited CRM and asset evidence",
            ],
            "Guardrail": [
                "No real vendor or customer data is included",
                "No production pricing or contract terms are encoded",
                "Forecast remains human-approved",
                "Exposure is scenario analytics, not an invoice",
                "Manifest recall/FPR measures logic quality",
                "Low confidence routes to evidence work",
                "Unsupported claims fail the grounding check",
            ],
        },
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Score Audit Sample")
audit = read_df(
    """
    SELECT account_id, account_name, priority_score, priority_band,
           recommended_play, primary_competitor, score_drivers_json,
           data_confidence_pct, governance_status, forecast_recommendation
    FROM account_positioning
    ORDER BY priority_score DESC
    LIMIT 100
    """
)
st.dataframe(audit, use_container_width=True, hide_index=True)

with st.expander("Top record driver breakdown"):
    if not audit.empty:
        top = audit.iloc[0]
        st.write(top["account_name"])
        st.json(json.loads(top["score_drivers_json"]))
