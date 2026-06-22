from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.config import load_scoring_config  # noqa: E402
from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Model Governance", page_icon="🛡️", layout="wide")
st.title("Model Governance")
st.caption("Score → Driver → Evidence → Human decision を追跡できるようにします。")

if not database_ready():
    st.error("先にトップページでデモ環境を構築してください。")
    st.stop()

config = load_scoring_config()
st.info(
    "このデモのスコアは説明可能なルールベースです。AIは根拠の要約や下書きに限定し、"
    "価格、契約範囲、Forecast commitのSource of Truthにはしません。"
)
rows = []
for model, weights in config["weights"].items():
    for feature, weight in weights.items():
        rows.append({"model": model, "feature": feature, "weight": weight})
weights_df = pd.DataFrame(rows)

c1, c2 = st.columns([1.2, 1])
with c1:
    st.subheader("Business-owned score weights")
    st.caption("営業・Finance・RevOpsがレビューできる重みだけでスコアを作ります。")
    st.dataframe(weights_df, use_container_width=True, hide_index=True)
with c2:
    st.subheader("Decision boundaries")
    st.caption("High/Mediumの境界と、Forecastに使える最低Data confidenceです。")
    st.json(config["thresholds"])

st.subheader("Control design")
st.caption("どの判断をルール、AI、人が担当するかを明確に分けます。")
st.dataframe(
    {
        "Layer": ["Deterministic logic", "Optional AI", "Human approval", "Audit"],
        "Allowed": [
            "Asset照合、契約対象、価格式、ルールベースScore",
            "承認済みEvidenceの要約、コメント分類、Briefドラフト",
            "価格、Discount、Forecast category、顧客提示",
            "入力Record、Rule version、出力、Override理由",
        ],
        "Prohibited / constrained": [
            "根拠なしの上書き",
            "Entitlement・価格・ComplianceをSource of Truthとして決定",
            "Evidence不明のCommit",
            "追跡不能な手修正",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

st.subheader("Score audit sample")
st.caption("各Accountの推奨PlayとDriverを追跡し、後から説明できる状態にします。")
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

st.subheader("Export governed AE playbook")
export = read_df(
    """
    SELECT account_id, account_name, ae_name, recommended_play, primary_competitor,
           priority_score, priority_band, estimated_tcv_jpy_mn,
           expected_commercial_value_jpy_mn, data_confidence_pct,
           governance_status, positioning_angle, next_best_action, data_story
    FROM account_positioning
    ORDER BY priority_score DESC
    """
)
st.download_button(
    "CSVをダウンロード",
    data=export.to_csv(index=False).encode("utf-8-sig"),
    file_name="governed_ae_playbook.csv",
    mime="text/csv",
)

with st.expander("Top recordのDriverを展開"):
    if not audit.empty:
        top = audit.iloc[0]
        st.write(top["account_name"])
        st.json(json.loads(top["score_drivers_json"]))
