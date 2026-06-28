from __future__ import annotations

import pandas as pd

from saas_insights.gtm import (
    PANEL_MONTHS,
    compute_gtm_metrics,
    generate_gtm_monthly,
    gtm_summary,
)


def test_panel_shape_and_company_rollup() -> None:
    panel = generate_gtm_monthly(seed=11)
    segments = set(panel["segment"].unique())
    assert {"Company", "Enterprise", "Commercial", "Public Sector"} == segments
    assert panel["month"].nunique() == PANEL_MONTHS

    # The Company row must equal the sum of the three segments for additive ARR flows.
    month = panel["month"].max()
    company = panel[(panel["segment"] == "Company") & (panel["month"] == month)].iloc[0]
    seg_sum = panel[(panel["segment"] != "Company") & (panel["month"] == month)][
        "ending_arr_jpy_mn"
    ].sum()
    assert abs(float(company["ending_arr_jpy_mn"]) - float(seg_sum)) <= 0.05


def test_metrics_are_sane_and_explainable() -> None:
    metrics = compute_gtm_metrics(generate_gtm_monthly(seed=11))
    company = metrics[metrics["segment"] == "Company"].sort_values("month")

    # ARR compounds over the panel.
    assert company["ending_arr_jpy_mn"].iloc[-1] > company["ending_arr_jpy_mn"].iloc[0]

    latest = company.iloc[-1]
    assert 95 <= latest["nrr_ttm_pct"] <= 140
    assert 70 <= latest["grr_ttm_pct"] <= 100
    assert latest["grr_ttm_pct"] <= latest["nrr_ttm_pct"]
    assert 0 <= latest["gross_margin_pct"] <= 100
    assert latest["cac_payback_months"] > 0
    assert latest["ltv_to_cac"] > 1
    assert 0 <= latest["win_rate_pct"] <= 100


def test_summary_keys_and_determinism() -> None:
    summary = gtm_summary(compute_gtm_metrics(generate_gtm_monthly(seed=11)))
    assert "rule_of_40_pct" in summary
    assert "magic_number" in summary

    first = generate_gtm_monthly(seed=11)
    second = generate_gtm_monthly(seed=11)
    pd.testing.assert_frame_equal(first, second)
