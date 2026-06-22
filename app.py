from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.pipeline import bootstrap, export_outputs, validate_warehouse  # noqa: E402
from saas_insights.ui import database_ready, format_jpy_mn, read_df  # noqa: E402

st.set_page_config(
    page_title="Enterprise SaaS Insights Lab",
    page_icon="📊",
    layout="wide",
)

st.title("Enterprise SaaS Insights Lab")
st.caption(
    "Synthetic BI workspace for managing enterprise SaaS renewals, adoption, and "
    "competitive risk."
)

st.markdown(
    """
このデモは、主力SaaSベンダーのポートフォリオを管理する営業・CS・RevOps向けBIツールです。
合成データだけを使い、契約更新、利用状況、競合シグナル、データ品質をAccount単位でつなげて、
「どこに営業工数を投下すべきか」「Forecastに入れてよい根拠があるか」を説明できる形にします。

実在企業の社内データ、実価格、実際の勝率、正式な製品推奨は含みません。
"""
)

if not database_ready():
    st.warning("データベースが未構築です。")
    st.code("python -m pip install -e .\npython -m saas_insights.cli bootstrap")
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
Subscription inventory / Contract / Entitlement / Usage / Support / CRM / Competitor signals
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
        "Sales Play": [
            "Platform Modernization",
            "Security Platform",
            "AI Data Platform",
            "Renewal / Enterprise Plan",
        ],
        "主な判断材料": [
            "ライフサイクル移行、契約Gap、主力ベンダー比率、障害、競合PoC",
            "セキュリティツール乱立、Log Analytics連携、更新集中、インシデント、競合",
            "AI投資時期、データ処理容量、Data Platform刷新、予算、競合",
            "180日更新額、契約分散、Enterprise Plan適格性、Adoption、データ信頼度",
        ],
        "営業出力": [
            "Modernization優先順位・TCO・段階導入",
            "Platform統合仮説・SOC工数比較",
            "AI-ready Discovery・PoC候補",
            "Base/Downside/Upside・契約集約シナリオ",
        ],
        "読み方": [
            "古い契約や低利用モジュールを残すコストを可視化します",
            "点在したセキュリティSaaSを統合する商業価値を見ます",
            "AI活用に必要なデータ基盤と運用準備度を見ます",
            "更新を事務処理ではなくForecast判断として管理します",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

st.info(
    "左メニューからPortfolio、Account 360、Competitive Positioning、"
    "Data Quality、Model Governanceを確認できます。各画面は、営業判断の根拠を"
    "スコア、ドライバー、データ品質、次アクションに分解して表示します。"
)
