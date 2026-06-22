from __future__ import annotations

import json

import pandas as pd

from cisco_insights.config import load_scoring_config
from cisco_insights.scoring import score_accounts


def _row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "account_id": "A00001",
        "account_name": "Synthetic Account",
        "industry": "Manufacturing",
        "segment": "Enterprise",
        "region": "Japan East",
        "ae_name": "AE-01",
        "partner_name": "Partner Alpha",
        "strategic_tier": "Tier 1",
        "annual_revenue_jpy_mn": 10000.0,
        "employee_count": 5000,
        "cisco_relationship_years": 8,
        "security_tool_count": 7,
        "splunk_installed": True,
        "ai_investment_horizon_months": 12,
        "gpu_cluster_planned": True,
        "budget_readiness_pct": 80.0,
        "managed_service_interest": 60.0,
        "budget_cycle_month": 4,
        "total_assets": 1000,
        "cisco_assets": 800,
        "refresh_asset_count": 450,
        "cisco_share_pct": 80.0,
        "cisco_network_share_pct": 85.0,
        "cisco_dc_share_pct": 75.0,
        "eol_18m_pct": 65.0,
        "support_gap_pct": 25.0,
        "high_speed_port_gap_pct": 70.0,
        "network_utilization_pressure_pct": 68.0,
        "data_confidence_pct": 88.0,
        "verified_assets_pct": 75.0,
        "reconcilable_assets_pct": 15.0,
        "unknown_assets_pct": 10.0,
        "active_cisco_contracts": 9,
        "renewal_month_count_24m": 8,
        "cisco_annual_contract_value_jpy_mn": 200.0,
        "renewal_value_180d_jpy_mn": 120.0,
        "security_renewal_12m_jpy_mn": 60.0,
        "avg_adoption_pct": 76.0,
        "ea_eligible_contracts": 4,
        "active_ea_contracts": 0,
        "support_case_count_18m": 20,
        "severe_case_count_18m": 3,
        "open_case_count": 4,
        "avg_resolution_hours": 30.0,
        "competitive_pressure_pct": 82.0,
        "top_competitor": "HPE Networking",
        "competitor_signal_count": 3,
        "campus_competitive_pressure_pct": 90.0,
        "campus_competitor": "HPE Networking",
        "security_competitive_pressure_pct": 55.0,
        "security_competitor": "Palo Alto Networks",
        "ai_competitive_pressure_pct": 65.0,
        "ai_competitor": "Arista",
        "renewal_competitive_pressure_pct": 30.0,
        "renewal_competitor": "No Decision",
        "open_pipeline_jpy_mn": 400.0,
        "weighted_pipeline_jpy_mn": 210.0,
        "open_opportunity_count": 4,
        "avg_quote_variance_pct": 4.0,
        "commit_count": 1,
        "contract_fragmentation_pct": 90.0,
        "incident_pressure_pct": 100.0,
    }
    base.update(overrides)
    return base


def test_scores_are_bounded_and_explainable() -> None:
    frame = pd.DataFrame([_row(), _row(account_id="A00002", account_name="Second")])
    result = score_accounts(frame, load_scoring_config())

    for column in [
        "campus_refresh_score",
        "security_platform_score",
        "ai_data_center_score",
        "renewal_ea_score",
        "priority_score",
    ]:
        assert result[column].between(0, 100).all()

    drivers = json.loads(result.iloc[0]["score_drivers_json"])
    assert 1 <= len(drivers) <= 4
    assert result.iloc[0]["next_best_action"]
    assert result.iloc[0]["positioning_angle"]


def test_low_confidence_is_not_forecast_ready() -> None:
    frame = pd.DataFrame([_row(data_confidence_pct=40.0, unknown_assets_pct=35.0)])
    result = score_accounts(frame, load_scoring_config()).iloc[0]
    assert result["governance_status"] == "Evidence required"
    assert "Commit" in result["forecast_recommendation"]
    assert "照合" in result["next_best_action"]
