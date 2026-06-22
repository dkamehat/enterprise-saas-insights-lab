from __future__ import annotations

from cisco_insights.config import load_scoring_config
from cisco_insights.tco import calculate_tco


def test_tco_has_traceable_components() -> None:
    row = {
        "refresh_asset_count": 500,
        "cisco_annual_contract_value_jpy_mn": 200,
        "cisco_network_share_pct": 85,
        "incident_pressure_pct": 60,
    }
    result = calculate_tco(row, load_scoring_config(), competitor_discount_pct=18, years=3)
    assert list(result.columns) == [
        "cost_component",
        "cisco_jpy_mn",
        "competitor_jpy_mn",
        "delta_jpy_mn",
    ]
    assert len(result) == 5
    assert result["cisco_jpy_mn"].sum() > 0
    assert result["competitor_jpy_mn"].sum() > 0
