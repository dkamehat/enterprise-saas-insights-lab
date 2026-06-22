from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.config import load_scoring_config  # noqa: E402
from saas_insights.scoring import PLAY_CONFIG  # noqa: E402
from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Formula Appendix", layout="wide")
st.title("Formula Appendix")
st.caption(
    "Calculation details, business rationale, accepted practices, and lab hypotheses "
    "behind the demo scoring model."
)

if not database_ready():
    st.error("Build the demo warehouse first from the top page.")
    st.stop()

config = load_scoring_config()


def _weights_frame() -> pd.DataFrame:
    rows = []
    for play, spec in PLAY_CONFIG.items():
        weights = config["weights"][spec["config_key"]]
        for component, source_column in spec["feature_map"].items():
            rows.append(
                {
                    "sales_play": play,
                    "component": component,
                    "source_feature": source_column,
                    "weight": float(weights[component]),
                }
            )
    frame = pd.DataFrame(rows)
    frame["weight_pct"] = frame["weight"] * 100
    return frame


def _threshold_frame() -> pd.DataFrame:
    thresholds = config["thresholds"]
    return pd.DataFrame(
        [
            {
                "parameter": "high_priority",
                "value": thresholds["high_priority"],
                "meaning": "priority_score at or above this level becomes High.",
            },
            {
                "parameter": "medium_priority",
                "value": thresholds["medium_priority"],
                "meaning": "priority_score at or above this level becomes Medium.",
            },
            {
                "parameter": "minimum_data_confidence_for_forecast",
                "value": thresholds["minimum_data_confidence_for_forecast"],
                "meaning": "minimum confidence required for Forecast-ready status.",
            },
            {
                "parameter": "renewal_window_days",
                "value": thresholds["renewal_window_days"],
                "meaning": "near-term renewal window used by the demo narrative.",
            },
            {
                "parameter": "modernization_window_days",
                "value": thresholds["modernization_window_days"],
                "meaning": "asset lifecycle window approximating 18 months.",
            },
        ]
    )


FEATURE_FORMULAS = [
    {
        "feature": "primary_share_pct",
        "formula": "100 * primary_vendor_assets / total_assets",
        "rationale": "Installed-base share is a proxy for continuity and expansion surface.",
    },
    {
        "feature": "primary_platform_share_pct",
        "formula": "100 * primary Core/Data assets / all Core/Data assets",
        "rationale": "Platform footprint matters most for modernization plays.",
    },
    {
        "feature": "primary_data_share_pct",
        "formula": "100 * primary Data Platform assets / all Data Platform assets",
        "rationale": "AI/data plays need a data-platform-specific adoption signal.",
    },
    {
        "feature": "eol_18m_pct",
        "formula": (
            "100 * primary Core/Data assets ending support by 2027-12-21 "
            "/ primary Core/Data assets"
        ),
        "rationale": "Lifecycle pressure is treated as a modernization trigger.",
    },
    {
        "feature": "support_gap_pct",
        "formula": "100 * primary assets with missing/orphan/mismatched contract / primary assets",
        "rationale": "Commercial coverage gaps reduce forecast and renewal confidence.",
    },
    {
        "feature": "data_throughput_gap_pct",
        "formula": "100 * Data Platform assets with capacity_units < 400 / Data Platform assets",
        "rationale": "Capacity pressure is a proxy for AI/data expansion need.",
    },
    {
        "feature": "physical_or_hybrid_pct",
        "formula": "100 * hybrid/device-linked assets / all assets",
        "rationale": "Hybrid estates need more careful migration and sales coverage.",
    },
    {
        "feature": "software_subscription_pct",
        "formula": "100 * SaaS subscription assets / all assets",
        "rationale": "Subscription mix helps separate expansion from lifecycle refresh motions.",
    },
    {
        "feature": "platform_utilization_pressure_pct",
        "formula": "100 * avg(clip((utilization_pct - 65) / 35, 0, 1))",
        "rationale": "Utilization above 65% is modeled as rising capacity pressure.",
    },
    {
        "feature": "contract_fragmentation_pct",
        "formula": (
            "min(100, 55 * min(active_contracts/8, 1) "
            "+ 45 * min(renewal_months_24m/8, 1))"
        ),
        "rationale": "Many active contracts and renewal months increase account complexity.",
    },
    {
        "feature": "incident_pressure_pct",
        "formula": "min(100, 35 * severe_cases_18m + 10 * open_cases)",
        "rationale": "High-severity and open cases indicate operational urgency.",
    },
]

SCORING_FORMULAS = [
    {
        "output": "component_contribution",
        "formula": "clip(feature_value, 0, 100) * component_weight",
        "notes": "Every component is bounded before weighting so outliers cannot dominate.",
    },
    {
        "output": "sales_play_score",
        "formula": "clip(sum(component_contribution), 0, 100)",
        "notes": "Weighted-sum model for each sales play.",
    },
    {
        "output": "recommended_play",
        "formula": "argmax(platform, security, ai_data, renewal scores)",
        "notes": "The demo recommends the play with the strongest current evidence.",
    },
    {
        "output": "score_drivers_json",
        "formula": "top 4 component_contribution values for recommended_play",
        "notes": "Shown to keep the recommendation explainable.",
    },
    {
        "output": "modeled_win_probability_pct",
        "formula": (
            "clip(0.55*play_fit + 0.25*data_confidence "
            "+ 0.20*primary_fit, 5, 92)"
        ),
        "notes": "Bounds avoid false precision at 0% or 100%.",
    },
    {
        "output": "expected_commercial_value_jpy_mn",
        "formula": "estimated_tcv_jpy_mn * modeled_win_probability_pct / 100",
        "notes": "Expected value framing: size multiplied by modeled probability.",
    },
    {
        "output": "priority_score",
        "formula": (
            "clip(0.55*play_fit + 0.25*expected_value_percentile "
            "+ 0.20*data_confidence, 0, 100)"
        ),
        "notes": "Prioritization balances fit, commercial value, and evidence quality.",
    },
    {
        "output": "priority_band",
        "formula": "High >= 70; Medium >= 45; otherwise Low",
        "notes": "Thresholds are business-owned TOML parameters.",
    },
    {
        "output": "governance_status",
        "formula": "Forecast-ready when data_confidence_pct >= 85; otherwise Evidence required",
        "notes": "Low-confidence records stay out of commit-style forecast use.",
    },
]

TCV_FORMULAS = [
    {
        "sales_play": "Platform Modernization",
        "formula": "max(5, modernization_asset_count * modernization_unit_price * 1.18)",
        "hypothesis": (
            "Lifecycle refresh opportunity scales with affected assets "
            "plus software attach."
        ),
    },
    {
        "sales_play": "Security Platform",
        "formula": "max(5, primary_annual_contract_value * 0.60 + security_tool_count * 4)",
        "hypothesis": "Security value grows with installed base and tool-consolidation surface.",
    },
    {
        "sales_play": "AI Data Platform",
        "formula": "max(8, min(2500, employee_count / 90 * gpu_multiplier))",
        "hypothesis": "AI platform opportunity scales with employee base and GPU plan signal.",
    },
    {
        "sales_play": "Renewal / Enterprise Plan",
        "formula": "max(3, renewal_value_180d * 3 + primary_annual_contract_value * 0.25)",
        "hypothesis": "Renewal motion values near-term renewals and broader account base.",
    },
]

DATA_QUALITY_RULES = [
    {
        "issue": "Missing serial",
        "penalty": 35,
        "reason": "Serial is the strongest asset-level reconciliation key.",
    },
    {
        "issue": "Duplicate serial",
        "penalty": 30,
        "reason": "Duplicate serials create identity ambiguity.",
    },
    {
        "issue": "Missing contract",
        "penalty": 15,
        "reason": "Commercial coverage is unclear for primary-vendor assets.",
    },
    {
        "issue": "Orphan contract reference",
        "penalty": 25,
        "reason": "Referenced contract does not exist in the contract table.",
    },
    {
        "issue": "Contract-account mismatch",
        "penalty": 35,
        "reason": "Account mismatch is a high-risk revenue and support integrity issue.",
    },
    {
        "issue": "Missing entitlement",
        "penalty": 12,
        "reason": "Some product families require entitlement proof.",
    },
    {
        "issue": "Orphan entitlement reference",
        "penalty": 20,
        "reason": "Referenced entitlement does not exist in the entitlement table.",
    },
    {
        "issue": "Entitlement-account mismatch",
        "penalty": 30,
        "reason": "License ownership conflicts with the asset account.",
    },
    {
        "issue": "Stale verification",
        "penalty": 10,
        "reason": "Old verification lowers confidence but may be recoverable.",
    },
]

TCO_FORMULAS = [
    {
        "component": "hardware_baseline",
        "formula": "max(8, modernization_assets * modernization_unit, annual_contract * 0.75)",
    },
    {
        "component": "software_attach",
        "formula": "hardware_baseline * software_attach_rate",
    },
    {
        "component": "primary_product",
        "formula": "hardware_baseline + software_attach",
    },
    {
        "component": "competitor_product",
        "formula": "hardware_baseline * (1 - competitor_discount_pct/100) + software_attach",
    },
    {
        "component": "primary_migration",
        "formula": "primary_product * primary_migration_cost_rate",
    },
    {
        "component": "competitor_migration",
        "formula": (
            "competitor_product * competitor_migration_cost_rate "
            "* (0.5 + primary_share)"
        ),
    },
    {
        "component": "operations",
        "formula": "product_cost * annual_operations_rate * horizon_years",
    },
    {
        "component": "expected_risk",
        "formula": "product_cost * expected_risk_rate * (1 + incident_pressure_pct/100)",
    },
]

THEORY_AND_HYPOTHESES = [
    {
        "lens": "Weighted-sum scoring / MCDA",
        "accepted_practice": (
            "When choices have multiple observable factors, a bounded weighted "
            "score is a common decision-support pattern."
        ),
        "lab_hypothesis": (
            "Sales-play fit can be expressed as a weighted mix of lifecycle, "
            "adoption, pressure, and competitive signals."
        ),
        "audit_note": "Weights must be business-owned and reviewed; this is not a causal model.",
    },
    {
        "lens": "Expected value",
        "accepted_practice": (
            "Pipeline views often separate opportunity size from "
            "probability-weighted value."
        ),
        "lab_hypothesis": "TCV times modeled win probability is a useful prioritization proxy.",
        "audit_note": "Do not treat expected value as a booking forecast without human review.",
    },
    {
        "lens": "Data quality dimensions",
        "accepted_practice": (
            "Completeness, uniqueness, validity, consistency, and timeliness "
            "are standard quality lenses."
        ),
        "lab_hypothesis": (
            "Asset forecast confidence can be penalized through serial, "
            "contract, entitlement, and freshness checks."
        ),
        "audit_note": (
            "Penalty weights are illustrative and should be calibrated "
            "with real error-cost data."
        ),
    },
    {
        "lens": "Total cost of ownership",
        "accepted_practice": (
            "TCO comparisons include product cost plus migration, training, "
            "operations, and risk."
        ),
        "lab_hypothesis": (
            "A cheaper competitor can still be less attractive when switching "
            "cost and disruption risk are included."
        ),
        "audit_note": "TCO is scenario analysis, not a price quote.",
    },
    {
        "lens": "Human-in-the-loop governance",
        "accepted_practice": (
            "Decision support should separate evidence, model recommendation, "
            "and accountable human decision."
        ),
        "lab_hypothesis": (
            "Low-confidence accounts should be routed to evidence collection "
            "before forecast use."
        ),
        "audit_note": (
            "The model can suggest actions; it should not override pricing, "
            "legal, or commit decisions."
        ),
    },
]

st.subheader("Model Scope")
st.markdown(
    """
This appendix documents the calculations behind the demo. The model is intentionally
rule-based and explainable: it is a BI decision-support layer, not an automated pricing,
forecasting, or entitlement system of record.

Key convention:

`clip(x, 0, 100) = min(100, max(0, x))`
"""
)

summary = read_df(
    """
    SELECT
        COUNT(*) AS accounts,
        AVG(priority_score) AS avg_priority,
        AVG(data_confidence_pct) AS avg_data_confidence,
        SUM(expected_commercial_value_jpy_mn) AS expected_value_jpy_mn
    FROM account_positioning
    """
).iloc[0]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Accounts scored", f"{int(summary['accounts']):,}")
m2.metric("Avg priority", f"{summary['avg_priority']:.1f}")
m3.metric("Avg data confidence", f"{summary['avg_data_confidence']:.1f}%")
m4.metric("Expected value", f"JPY {summary['expected_value_jpy_mn']:,.1f}M")

st.subheader("Theory, Practice, And Lab Hypotheses")
st.markdown(
    """
- **Weighted-sum scoring / MCDA**: bounded weighted factors make trade-offs inspectable.
- **Expected value**: opportunity size is separated from modeled probability.
- **Data quality dimensions**: completeness, uniqueness, validity, consistency, and timeliness
  drive confidence.
- **TCO**: product cost is compared with migration, training, operations, and risk.
- **Human-in-the-loop governance**: evidence and model recommendation stay separate from
  accountable business decisions.
"""
)
st.dataframe(
    pd.DataFrame(THEORY_AND_HYPOTHESES),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Business-Owned Thresholds")
st.dataframe(_threshold_frame(), use_container_width=True, hide_index=True)

st.subheader("Sales Play Weights")
weights_frame = _weights_frame()
st.dataframe(
    weights_frame,
    use_container_width=True,
    hide_index=True,
    column_config={
        "weight": st.column_config.NumberColumn("weight", format="%.2f"),
        "weight_pct": st.column_config.NumberColumn("weight_pct", format="%.0f%%"),
    },
)

st.subheader("Feature Engineering Formulas")
st.dataframe(pd.DataFrame(FEATURE_FORMULAS), use_container_width=True, hide_index=True)

st.subheader("Scoring Formulas")
st.dataframe(pd.DataFrame(SCORING_FORMULAS), use_container_width=True, hide_index=True)

st.subheader("Estimated TCV Formulas")
tco_cfg = config["tco"]
st.caption(
    "The modernization unit price is "
    f"JPY {float(tco_cfg['primary_modernization_unit_jpy_mn']):.2f}M in this demo."
)
st.dataframe(pd.DataFrame(TCV_FORMULAS), use_container_width=True, hide_index=True)

st.subheader("Asset Data Confidence")
st.markdown(
    """
`asset_data_confidence_pct = max(0, 100 - sum(issue_penalty))`

`reconciliation_status`:

- `Verified`: no issues.
- `Reconcilable`: no missing/duplicate serial, no account mismatch, and two or fewer issues.
- `Unknown`: higher-risk records requiring evidence before forecast use.
"""
)
st.dataframe(pd.DataFrame(DATA_QUALITY_RULES), use_container_width=True, hide_index=True)

st.subheader("TCO Scenario Formulas")
st.caption(
    "The Account 360 TCO scenario compares the primary path with a discounted "
    "competitor path over the configured horizon."
)
st.dataframe(pd.DataFrame(TCO_FORMULAS), use_container_width=True, hide_index=True)

with st.expander("Current TCO parameters"):
    st.json(config["tco"])

st.subheader("Interpretation Guardrails")
st.markdown(
    """
- Scores rank accounts for attention; they are not causal lift estimates.
- Win probability is modeled for prioritization and is capped at 92%.
- Forecast-ready only means the evidence is sufficient for scenario forecasting.
- Low-confidence data should trigger reconciliation work, not automatic exclusion from sales review.
- Real production use would calibrate weights against historical outcomes
  and add approval workflows.
"""
)
