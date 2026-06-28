from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .recommendations import data_story, next_best_action, positioning_angle

PLAY_CONFIG = {
    "Platform Modernization": {
        "config_key": "platform_modernization",
        "competitor_column": "platform_competitor",
        "feature_map": {
            "eol_18m_pct": "eol_18m_pct",
            "support_gap_pct": "support_gap_pct",
            "primary_platform_share_pct": "primary_platform_share_pct",
            "platform_utilization_pressure": "platform_utilization_pressure_pct",
            "incident_pressure": "incident_pressure_pct",
            "contract_fragmentation": "contract_fragmentation_pct",
            "competitive_pressure": "platform_competitive_pressure_pct",
        },
    },
    "Security Platform": {
        "config_key": "security_platform",
        "competitor_column": "security_competitor",
        "feature_map": {
            "security_tool_sprawl": "security_tool_sprawl_pct",
            "primary_platform_share_pct": "primary_platform_share_pct",
            "log_analytics_presence": "log_analytics_presence_pct",
            "security_renewal_pressure": "security_renewal_pressure_pct",
            "security_incident_pressure": "incident_pressure_pct",
            "competitive_pressure": "security_competitive_pressure_pct",
            "contract_fragmentation": "contract_fragmentation_pct",
        },
    },
    "AI Data Platform": {
        "config_key": "ai_data_platform",
        "competitor_column": "ai_competitor",
        "feature_map": {
            "gpu_cluster_planned": "gpu_cluster_planned_pct",
            "ai_investment_urgency": "ai_investment_urgency_pct",
            "data_platform_modernization_pressure": "eol_18m_pct",
            "data_throughput_gap": "data_throughput_gap_pct",
            "primary_data_share_pct": "primary_data_share_pct",
            "budget_readiness": "budget_readiness_pct",
            "competitive_pressure": "ai_competitive_pressure_pct",
        },
    },
    "Renewal / Enterprise Plan": {
        "config_key": "renewal_enterprise_plan",
        "competitor_column": "renewal_competitor",
        "feature_map": {
            "renewal_value_pressure": "renewal_value_pressure_pct",
            "contract_fragmentation": "contract_fragmentation_pct",
            "enterprise_plan_eligibility": "enterprise_plan_eligibility_pct",
            "support_gap_pct": "support_gap_pct",
            "adoption_health": "avg_adoption_pct",
            "data_confidence": "data_confidence_pct",
            "competitive_pressure": "renewal_competitive_pressure_pct",
        },
    },
}


def _clip(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0).clip(0.0, 100.0)


def _prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["security_tool_sprawl_pct"] = ((df["security_tool_count"] - 1) / 8 * 100).clip(0, 100)
    df["log_analytics_presence_pct"] = (
        df["log_analytics_installed"].astype(bool).astype(float) * 100
    )
    annual = pd.to_numeric(df["primary_annual_contract_value_jpy_mn"], errors="coerce").fillna(0.0)
    security_renewal = pd.to_numeric(df["security_renewal_12m_jpy_mn"], errors="coerce").fillna(0.0)
    df["security_renewal_pressure_pct"] = (security_renewal / annual.clip(lower=1.0) * 100).clip(
        0, 100
    )
    horizon = pd.to_numeric(df["ai_investment_horizon_months"], errors="coerce").fillna(60.0)
    df["ai_investment_urgency_pct"] = ((60 - horizon) / 54 * 100).clip(0, 100)
    df["gpu_cluster_planned_pct"] = df["gpu_cluster_planned"].astype(bool).astype(float) * 100
    df["enterprise_plan_eligibility_pct"] = (
        pd.to_numeric(df["enterprise_plan_eligible_contracts"], errors="coerce").fillna(0) / 4 * 100
    ).clip(0, 100)
    renewal_value = pd.to_numeric(df["renewal_value_180d_jpy_mn"], errors="coerce").fillna(0.0)
    if renewal_value.nunique(dropna=False) <= 1:
        df["renewal_value_pressure_pct"] = 0.0
    else:
        df["renewal_value_pressure_pct"] = renewal_value.rank(method="average", pct=True) * 100
    return df


def _score_play(
    df: pd.DataFrame,
    play_name: str,
    config: Mapping[str, Any],
) -> tuple[pd.Series, list[dict[str, float]]]:
    spec = PLAY_CONFIG[play_name]
    weights = config["weights"][spec["config_key"]]
    contributions: dict[str, pd.Series] = {}
    total = pd.Series(0.0, index=df.index)
    for component, column in spec["feature_map"].items():
        weight = float(weights[component])
        contribution = _clip(df[column]) * weight
        contributions[component] = contribution
        total = total + contribution

    driver_rows: list[dict[str, float]] = []
    for idx in df.index:
        row = {name: round(float(series.loc[idx]), 2) for name, series in contributions.items()}
        driver_rows.append(row)
    return total.clip(0, 100), driver_rows


def _play_tcv(row: Mapping[str, Any], play: str, unit_modernization_jpy_mn: float) -> float:
    modernization_assets = float(row.get("modernization_asset_count", 0) or 0)
    annual_value = float(row.get("primary_annual_contract_value_jpy_mn", 0) or 0)
    renewal_value = float(row.get("renewal_value_180d_jpy_mn", 0) or 0)
    security_tools = float(row.get("security_tool_count", 0) or 0)
    employee_count = float(row.get("employee_count", 0) or 0)
    gpu = bool(row.get("gpu_cluster_planned", False))

    estimates = {
        "Platform Modernization": max(5.0, modernization_assets * unit_modernization_jpy_mn * 1.18),
        "Security Platform": max(5.0, annual_value * 0.60 + security_tools * 4.0),
        "AI Data Platform": max(8.0, min(2_500.0, employee_count / 90.0 * (1.35 if gpu else 0.55))),
        "Renewal / Enterprise Plan": max(3.0, renewal_value * 3.0 + annual_value * 0.25),
    }
    return round(float(estimates[play]), 2)


def score_accounts(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    df = _prepare_features(frame)
    play_driver_maps: dict[str, list[dict[str, float]]] = {}

    for play_name in PLAY_CONFIG:
        score, drivers = _score_play(df, play_name, config)
        column = play_name.lower().replace(" / ", "_").replace(" ", "_") + "_score"
        df[column] = score.round(2)
        play_driver_maps[play_name] = drivers

    score_columns = {
        "Platform Modernization": "platform_modernization_score",
        "Security Platform": "security_platform_score",
        "AI Data Platform": "ai_data_platform_score",
        "Renewal / Enterprise Plan": "renewal_enterprise_plan_score",
    }
    score_matrix = df[list(score_columns.values())].to_numpy(dtype=float)
    play_names = list(score_columns)
    best_indices = score_matrix.argmax(axis=1)
    df["recommended_play"] = [play_names[i] for i in best_indices]
    df["play_fit_score"] = score_matrix.max(axis=1).round(2)

    competitors: list[str] = []
    score_driver_json: list[str] = []
    positioning: list[str] = []
    actions: list[str] = []
    stories: list[str] = []
    tcvs: list[float] = []
    win_probabilities: list[float] = []

    tco_cfg = config["tco"]
    unit_modernization = float(tco_cfg["primary_modernization_unit_jpy_mn"])

    for position, (_, row) in enumerate(df.iterrows()):
        play = str(row["recommended_play"])
        competitor_column = PLAY_CONFIG[play]["competitor_column"]
        competitor = str(row.get(competitor_column) or "No Decision")
        competitors.append(competitor)

        drivers = play_driver_maps[play][position]
        top_drivers = sorted(drivers.items(), key=lambda item: item[1], reverse=True)[:4]
        score_driver_json.append(json.dumps(dict(top_drivers), ensure_ascii=False))
        positioning.append(positioning_angle(play, competitor, row))
        actions.append(next_best_action(play, competitor, row))
        stories.append(data_story(play, competitor, row))

        tcv = _play_tcv(row, play, unit_modernization)
        tcvs.append(tcv)
        primary_fit = float(row.get("primary_platform_share_pct", 0) or 0)
        if play == "AI Data Platform":
            primary_fit = float(row.get("primary_data_share_pct", 0) or 0)
        win_probability = (
            0.55 * float(row["play_fit_score"])
            + 0.25 * float(row.get("data_confidence_pct", 0) or 0)
            + 0.20 * primary_fit
        )
        win_probabilities.append(round(float(np.clip(win_probability, 5, 92)), 2))

    df["primary_competitor"] = competitors
    df["score_drivers_json"] = score_driver_json
    df["positioning_angle"] = positioning
    df["next_best_action"] = actions
    df["data_story"] = stories
    df["estimated_tcv_jpy_mn"] = tcvs
    df["modeled_win_probability_pct"] = win_probabilities
    df["expected_commercial_value_jpy_mn"] = (
        df["estimated_tcv_jpy_mn"] * df["modeled_win_probability_pct"] / 100.0
    ).round(2)

    value_percentile = df["expected_commercial_value_jpy_mn"].rank(method="average", pct=True) * 100
    df["priority_score"] = (
        (
            0.55 * df["play_fit_score"]
            + 0.25 * value_percentile
            + 0.20 * _clip(df["data_confidence_pct"])
        )
        .clip(0, 100)
        .round(2)
    )

    thresholds = config["thresholds"]
    high = float(thresholds["high_priority"])
    medium = float(thresholds["medium_priority"])
    df["priority_band"] = np.select(
        [df["priority_score"] >= high, df["priority_score"] >= medium],
        ["High", "Medium"],
        default="Low",
    )
    minimum_confidence = float(thresholds["minimum_data_confidence_for_forecast"])
    df["governance_status"] = np.where(
        df["data_confidence_pct"] >= minimum_confidence,
        "Forecast-ready",
        "Evidence required",
    )
    df["forecast_recommendation"] = np.where(
        df["governance_status"] == "Forecast-ready",
        "Eligible for scenario forecasting; AE still to confirm account situation.",
        "Exclude from Commit; manage as Upside/Risk and re-assess after reconciliation.",
    )
    return df
