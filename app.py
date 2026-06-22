from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.pipeline import (  # noqa: E402
    bootstrap,
    export_outputs,
    validate_warehouse,
)
from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(
    page_title="Enterprise SaaS Insights Lab",
    page_icon="SaaS",
    layout="wide",
)

st.title("Enterprise SaaS Insights Lab")
st.caption(
    "Synthetic BI workspace for enterprise SaaS renewals, installed-base governance, "
    "portfolio expansion, and forecast evidence."
)

st.markdown(
    """
This lab models a global enterprise SaaS portfolio using synthetic data only. It connects
accounts, assets, contracts, entitlements, usage, support, opportunities, and competitive
signals into explainable account-level recommendations.

The current version emphasizes measurable governance:

- Planted-signal manifest with recall and false-positive-rate tracking
- NRR decomposition across churn, contraction, and expansion
- True Forward style exposure from entitled vs consumed quantity
- Forecast calibration with Brier score
- Grounded account brief drafts with source-row citations
- Vendor-neutral interview lens for enterprise SaaS portfolio roles
"""
)

if not database_ready():
    st.warning("The demo warehouse has not been built yet.")
    st.code(
        "python -m pip install -e .\n"
        "python -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42"
    )
    if st.button("Build synthetic demo warehouse", type="primary"):
        with st.spinner("Generating synthetic data and DuckDB warehouse..."):
            bootstrap()
            export_outputs()
        st.success("Warehouse built. Reloading the app.")
        st.rerun()
    st.stop()

summary = read_df("SELECT * FROM portfolio_summary").iloc[0]
validation = validate_warehouse()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Accounts", f"{int(summary['account_count']):,}")
col2.metric("Assets", f"{int(validation['assets']):,}")
col3.metric(
    "Expected value",
    format_jpy_mn(float(summary["expected_commercial_value_jpy_mn"])),
)
col4.metric("Forecast-ready", f"{int(summary['forecast_ready_accounts']):,}")
col5.metric("Known defects", f"{int(validation['known_quality_signals']):,}")

st.subheader("Decision Flow")
st.markdown(
    """
```text
Subscription inventory / Contract / Entitlement / Usage / Support / CRM / Signals
                                  -> Asset reconciliation + planted-signal audit
                                  -> Account features + explainable play scoring
                                  -> NRR / True Forward / calibration / grounded brief
                                  -> Human-approved sales and forecast review
```
"""
)

st.subheader("Sales Plays")
st.dataframe(
    {
        "Sales Play": [
            "Platform Modernization",
            "Security Platform",
            "AI Data Platform",
            "Renewal / Enterprise Plan",
        ],
        "Primary evidence": [
            "Lifecycle pressure, support gaps, utilization, incidents, competition",
            "Security tool sprawl, log analytics, renewals, incidents, competition",
            "AI horizon, GPU plan, data capacity, data-platform share, budget",
            "Renewal value, contract fragmentation, enterprise-plan eligibility, adoption",
        ],
        "Decision output": [
            "Modernization priority and TCO scenario",
            "Consolidation story and security-platform action",
            "AI-ready discovery and data-platform expansion",
            "ARR/NRR review, evidence status, and expansion path",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

st.info(
    "Use the sidebar to move from portfolio prioritization to account diagnosis, "
    "competitive positioning, data-quality measurement, governance, formulas, and "
    "revenue assurance."
)
