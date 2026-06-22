from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from cisco_insights.pipeline import bootstrap, export_outputs, validate_warehouse  # noqa: E402
from cisco_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(
    page_title="Cisco Sales Insights Lab",
    page_icon="📊",
    layout="wide",
)

st.title("Cisco Sales Insights Lab")
st.caption("Synthetic commercial analytics environment — Cisco社内データ・実価格ではありません")

if not database_ready():
    st.warning("データベースが未構築です。")
    st.code("python -m pip install -e .\npython -m cisco_insights.cli bootstrap")
    if st.button("合成データでデモ環境を構築", type="primary"):
        with st.spinner("合成データとWarehouseを構築中..."):
            bootstrap()
            export_outputs()
        st.success("構築しました。ページを再読み込みしてください。")
        st.rerun()
    st.stop()

summary = read_df("SELECT * FROM portfolio_summary").iloc[0]
validation = validate_warehouse()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Accounts", f"{int(summary['account_count']):,}")
col2.metric("Assets", f"{int(validation['assets']):,}")
col3.metric(
    "Expected commercial value", format_jpy_mn(float(summary["expected_commercial_value_jpy_mn"]))
)
col4.metric("Forecast-ready", f"{int(summary['forecast_ready_accounts']):,}")

st.subheader("分析フロー")
st.markdown(
    """
```text
Installed Base / Contract / Entitlement / Usage / Support / CRM / Competitor signals
                                  ↓
                         Asset reconciliation
                                  ↓
             Account features + explainable play scoring
                                  ↓
       Competitive positioning / TCO / Next Best Action / Governance
```
"""
)

st.subheader("実装済みSales Play")
st.dataframe(
    {
        "Sales Play": ["Campus Refresh", "Security Platform", "AI Data Center", "Renewal / EA"],
        "主な判断材料": [
            "EOL、保守Gap、既存Cisco比率、障害、競合PoC",
            "ツール乱立、Splunk、更新集中、インシデント、競合",
            "GPU計画、Port speed、DC刷新、予算、競合",
            "180日更新額、契約分散、EA適格性、Adoption、データ信頼度",
        ],
        "営業出力": [
            "Refresh優先順位・TCO・段階移行",
            "Platform統合仮説・SOC工数比較",
            "AI-ready Discovery・PoC候補",
            "Base/Downside/Upside・契約集約シナリオ",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

st.info(
    "左メニューからPortfolio、Account 360、Competitive Positioning、"
    "Data Quality、Model Governanceを確認できます。"
)
