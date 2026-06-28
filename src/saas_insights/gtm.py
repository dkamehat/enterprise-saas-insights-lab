"""Time-aware GTM economics panel for Strategy & Operations analysis.

This module produces a deterministic monthly go-to-market (GTM) panel and the
SaaS efficiency metrics that a Strategy & Operations / BizOps team reports to an
executive staff: ARR growth, NRR / GRR, Rule of 40, Magic Number, CAC payback,
LTV / CAC, burn multiple, pipeline coverage, and win rate.

All numbers are synthetic and generated from a fixed seed. The point of the
module is not the values themselves but the *modeling discipline*: every headline
KPI is reconstructed from first-principle monthly drivers (new / expansion /
contraction / churn ARR, spend, customers, and funnel counts) so each metric is
auditable and reproducible rather than hard-coded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data_generator import AS_OF_DATE

# Segment-level operating assumptions. These are deliberately explicit so the
# generated story (improving efficiency over time) is transparent and tunable.
SEGMENT_PROFILES: dict[str, dict[str, float]] = {
    # starting ARR (JPY mn) ~42 months ago, monthly rates as fraction of base ARR,
    # average new-logo and installed-base deal sizes (JPY mn ARR), and margins.
    "Enterprise": {
        "start_arr": 2200.0,
        "new_rate": 0.020,
        "expansion_rate": 0.017,
        "contraction_rate": 0.0040,
        "churn_rate": 0.0050,
        "new_deal_arr": 42.0,
        "base_deal_arr": 95.0,
        "win_rate": 0.27,
    },
    "Commercial": {
        "start_arr": 1100.0,
        "new_rate": 0.026,
        "expansion_rate": 0.016,
        "contraction_rate": 0.0050,
        "churn_rate": 0.0080,
        "new_deal_arr": 8.0,
        "base_deal_arr": 14.0,
        "win_rate": 0.23,
    },
    "Public Sector": {
        "start_arr": 520.0,
        "new_rate": 0.012,
        "expansion_rate": 0.009,
        "contraction_rate": 0.0030,
        "churn_rate": 0.0030,
        "new_deal_arr": 16.0,
        "base_deal_arr": 28.0,
        "win_rate": 0.31,
    },
}

# Operating-expense ratios as a fraction of recognized revenue, ramped linearly
# from inefficient-early to efficient-late across the panel to model a company
# scaling toward profitability.
_RATIO_RAMP = {
    "gross_margin": (0.76, 0.81),
    "sm_ratio": (0.50, 0.33),
    "rd_ratio": (0.32, 0.21),
    "ga_ratio": (0.18, 0.11),
}

PANEL_MONTHS = 42


def _ramp(start: float, end: float, n: int) -> np.ndarray:
    return np.linspace(start, end, n)


def _month_index(months: int, as_of: pd.Timestamp) -> pd.DatetimeIndex:
    end = as_of.to_period("M").to_timestamp()
    return pd.date_range(end=end, periods=months, freq="MS")


def _segment_panel(
    segment: str,
    profile: dict[str, float],
    months: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n = len(months)
    gm = _ramp(*_RATIO_RAMP["gross_margin"], n)
    sm_ratio = _ramp(*_RATIO_RAMP["sm_ratio"], n)
    rd_ratio = _ramp(*_RATIO_RAMP["rd_ratio"], n)
    ga_ratio = _ramp(*_RATIO_RAMP["ga_ratio"], n)

    # Retention improves and churn decays over time to model a maturing motion.
    expansion_rate = profile["expansion_rate"] * _ramp(0.85, 1.20, n)
    churn_rate = profile["churn_rate"] * _ramp(1.20, 0.80, n)
    contraction_rate = profile["contraction_rate"] * _ramp(1.15, 0.85, n)
    new_rate = profile["new_rate"] * _ramp(0.90, 1.10, n)

    noise = rng.normal(1.0, 0.06, size=n).clip(0.80, 1.20)

    rows: list[dict[str, float]] = []
    arr = profile["start_arr"]
    customers = profile["start_arr"] / profile["base_deal_arr"]
    for i, month in enumerate(months):
        starting_arr = arr
        new_arr = starting_arr * new_rate[i] * noise[i]
        expansion_arr = starting_arr * expansion_rate[i] * noise[i]
        contraction_arr = starting_arr * contraction_rate[i]
        churned_arr = starting_arr * churn_rate[i]
        ending_arr = starting_arr + new_arr + expansion_arr - contraction_arr - churned_arr

        revenue = starting_arr / 12.0
        cogs = revenue * (1.0 - gm[i])
        sm_spend = revenue * sm_ratio[i]
        rd_spend = revenue * rd_ratio[i]
        ga_spend = revenue * ga_ratio[i]
        operating_income = revenue - cogs - sm_spend - rd_spend - ga_spend

        new_customers = max(1.0, new_arr / profile["new_deal_arr"])
        churned_customers = churned_arr / profile["base_deal_arr"]
        customers_end = customers + new_customers - churned_customers

        opps_won = new_customers
        win_rate = float(np.clip(profile["win_rate"] * noise[i], 0.10, 0.60))
        opps_closed = opps_won / win_rate
        opps_lost = opps_closed - opps_won
        opps_created = opps_closed * 1.35
        sql_count = opps_created * 1.6
        mql_count = sql_count * 3.1
        pipeline_created_arr = opps_created * profile["new_deal_arr"]
        # Quota and open pipeline snapshot, sized to a healthy ~3.4x coverage.
        quarter_target_arr = (new_arr + expansion_arr) * 3.0 / float(np.clip(noise[i], 0.85, 1.1))
        open_pipeline_arr = quarter_target_arr * 3.4 * noise[i]
        cash_burn = max(0.0, -operating_income)

        rows.append(
            {
                "month": month.date().isoformat(),
                "segment": segment,
                "starting_arr_jpy_mn": round(starting_arr, 2),
                "new_arr_jpy_mn": round(new_arr, 2),
                "expansion_arr_jpy_mn": round(expansion_arr, 2),
                "contraction_arr_jpy_mn": round(contraction_arr, 2),
                "churned_arr_jpy_mn": round(churned_arr, 2),
                "ending_arr_jpy_mn": round(ending_arr, 2),
                "revenue_jpy_mn": round(revenue, 2),
                "cogs_jpy_mn": round(cogs, 2),
                "sales_marketing_spend_jpy_mn": round(sm_spend, 2),
                "rd_spend_jpy_mn": round(rd_spend, 2),
                "ga_spend_jpy_mn": round(ga_spend, 2),
                "operating_income_jpy_mn": round(operating_income, 2),
                "cash_burn_jpy_mn": round(cash_burn, 2),
                "customers_start": round(customers, 1),
                "new_customers": round(new_customers, 1),
                "churned_customers": round(churned_customers, 1),
                "customers_end": round(customers_end, 1),
                "mql": round(mql_count, 0),
                "sql": round(sql_count, 0),
                "opportunities_created": round(opps_created, 0),
                "opportunities_won": round(opps_won, 1),
                "opportunities_lost": round(opps_lost, 1),
                "pipeline_created_arr_jpy_mn": round(pipeline_created_arr, 2),
                "open_pipeline_arr_jpy_mn": round(open_pipeline_arr, 2),
                "quarter_target_arr_jpy_mn": round(quarter_target_arr, 2),
            }
        )
        arr = ending_arr
        customers = customers_end
    return pd.DataFrame(rows)


# Columns summed when rolling segment rows up to a company total.
_ADDITIVE_COLUMNS = [
    "starting_arr_jpy_mn",
    "new_arr_jpy_mn",
    "expansion_arr_jpy_mn",
    "contraction_arr_jpy_mn",
    "churned_arr_jpy_mn",
    "ending_arr_jpy_mn",
    "revenue_jpy_mn",
    "cogs_jpy_mn",
    "sales_marketing_spend_jpy_mn",
    "rd_spend_jpy_mn",
    "ga_spend_jpy_mn",
    "operating_income_jpy_mn",
    "cash_burn_jpy_mn",
    "customers_start",
    "new_customers",
    "churned_customers",
    "customers_end",
    "mql",
    "sql",
    "opportunities_created",
    "opportunities_won",
    "opportunities_lost",
    "pipeline_created_arr_jpy_mn",
    "open_pipeline_arr_jpy_mn",
    "quarter_target_arr_jpy_mn",
]


def generate_gtm_monthly(
    months: int = PANEL_MONTHS,
    seed: int = 42,
    as_of: pd.Timestamp = AS_OF_DATE,
) -> pd.DataFrame:
    """Return the raw monthly GTM driver panel (segment rows + a ``Company`` roll-up)."""
    rng = np.random.default_rng(seed + 7)
    index = _month_index(months, as_of)
    segment_frames = [
        _segment_panel(segment, profile, index, rng)
        for segment, profile in SEGMENT_PROFILES.items()
    ]
    panel = pd.concat(segment_frames, ignore_index=True)

    company = panel.groupby("month", as_index=False)[_ADDITIVE_COLUMNS].sum()
    company.insert(1, "segment", "Company")
    return pd.concat([company, panel], ignore_index=True)


def _trailing_sum(series: pd.Series, window: int = 12) -> pd.Series:
    return series.rolling(window, min_periods=window).sum()


def _metrics_for_group(group: pd.DataFrame) -> pd.DataFrame:
    g = group.sort_values("month").reset_index(drop=True)
    arr = g["ending_arr_jpy_mn"]
    base_12m = g["ending_arr_jpy_mn"].shift(12)

    net_new_arr = (
        g["new_arr_jpy_mn"]
        + g["expansion_arr_jpy_mn"]
        - g["contraction_arr_jpy_mn"]
        - g["churned_arr_jpy_mn"]
    )
    g["net_new_arr_jpy_mn"] = net_new_arr.round(2)
    g["arr_growth_yoy_pct"] = ((arr / base_12m - 1.0) * 100.0).round(1)

    expansion_ttm = _trailing_sum(g["expansion_arr_jpy_mn"])
    contraction_ttm = _trailing_sum(g["contraction_arr_jpy_mn"])
    churn_ttm = _trailing_sum(g["churned_arr_jpy_mn"])
    g["nrr_ttm_pct"] = (
        (base_12m + expansion_ttm - contraction_ttm - churn_ttm) / base_12m * 100.0
    ).round(1)
    g["grr_ttm_pct"] = (
        (base_12m - contraction_ttm - churn_ttm) / base_12m * 100.0
    ).round(1)

    revenue_ttm = _trailing_sum(g["revenue_jpy_mn"])
    g["gross_margin_pct"] = (
        (g["revenue_jpy_mn"] - g["cogs_jpy_mn"]) / g["revenue_jpy_mn"] * 100.0
    ).round(1)
    g["operating_margin_ttm_pct"] = (
        _trailing_sum(g["operating_income_jpy_mn"]) / revenue_ttm * 100.0
    ).round(1)
    g["rule_of_40_pct"] = (g["arr_growth_yoy_pct"] + g["operating_margin_ttm_pct"]).round(1)

    # Magic number: net new ARR added this quarter / S&M spent the prior quarter.
    net_new_q = arr - arr.shift(3)
    sm_prev_q = (
        g["sales_marketing_spend_jpy_mn"].shift(3)
        + g["sales_marketing_spend_jpy_mn"].shift(4)
        + g["sales_marketing_spend_jpy_mn"].shift(5)
    )
    g["magic_number"] = (net_new_q / sm_prev_q).round(2)

    # CAC and payback on a trailing-3-month basis for stability.
    sm_ttq = _trailing_sum(g["sales_marketing_spend_jpy_mn"], 3)
    new_cust_ttq = _trailing_sum(g["new_customers"], 3)
    new_arr_ttq = _trailing_sum(g["new_arr_jpy_mn"], 3)
    cac = sm_ttq / new_cust_ttq
    new_arr_per_customer = new_arr_ttq / new_cust_ttq
    gm_frac = g["gross_margin_pct"] / 100.0
    g["cac_jpy_mn"] = cac.round(2)
    g["cac_payback_months"] = (
        cac / (new_arr_per_customer * gm_frac) * 12.0
    ).round(1)

    # LTV uses installed-base ARR per customer, gross margin, and the TTM gross
    # revenue churn rate (contraction + churn against the base 12 months ago),
    # i.e. (1 - GRR). This is more conservative than a logo-churn LTV and keeps
    # LTV / CAC in a defensible range.
    gross_rev_churn_rate = (
        (contraction_ttm + churn_ttm) / base_12m
    ).clip(lower=0.02)
    g["ltv_jpy_mn"] = (new_arr_per_customer * gm_frac / gross_rev_churn_rate).round(1)
    g["ltv_to_cac"] = (g["ltv_jpy_mn"] / g["cac_jpy_mn"]).round(2)

    # Burn multiple: net cash burned / net new ARR (trailing twelve months).
    burn_ttm = _trailing_sum(g["cash_burn_jpy_mn"])
    net_new_ttm = _trailing_sum(g["net_new_arr_jpy_mn"])
    g["burn_multiple"] = (burn_ttm / net_new_ttm).round(2)

    g["pipeline_coverage_x"] = (
        g["open_pipeline_arr_jpy_mn"] / g["quarter_target_arr_jpy_mn"]
    ).round(2)
    g["win_rate_pct"] = (
        g["opportunities_won"]
        / (g["opportunities_won"] + g["opportunities_lost"])
        * 100.0
    ).round(1)
    g["quota_attainment_pct"] = (
        net_new_arr / g["quarter_target_arr_jpy_mn"] * 3.0 * 100.0
    ).round(1)
    return g


def compute_gtm_metrics(monthly: pd.DataFrame) -> pd.DataFrame:
    """Augment the raw panel with derived SaaS efficiency metrics, per segment group."""
    frames = [
        _metrics_for_group(group) for _, group in monthly.groupby("segment", sort=False)
    ]
    return pd.concat(frames, ignore_index=True)


def gtm_summary(metrics: pd.DataFrame) -> dict[str, float]:
    """Return the latest-month company headline KPIs as a flat dict."""
    company = metrics[metrics["segment"] == "Company"].sort_values("month")
    latest = company.iloc[-1]
    keys = [
        "ending_arr_jpy_mn",
        "arr_growth_yoy_pct",
        "nrr_ttm_pct",
        "grr_ttm_pct",
        "gross_margin_pct",
        "rule_of_40_pct",
        "magic_number",
        "cac_payback_months",
        "ltv_to_cac",
        "burn_multiple",
        "pipeline_coverage_x",
        "win_rate_pct",
    ]
    return {key: float(latest[key]) for key in keys}
