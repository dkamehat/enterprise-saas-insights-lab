from __future__ import annotations

from saas_insights.briefing import build_grounded_account_brief, validate_grounding


def test_grounded_brief_uses_only_supplied_citations() -> None:
    account = {
        "account_id": "A00001",
        "account_name": "Kanto Systems 001",
        "priority_band": "High",
        "recommended_play": "Renewal / Enterprise Plan",
        "priority_score": 88.2,
        "expected_commercial_value_jpy_mn": 42.5,
        "data_confidence_pct": 91.0,
        "next_best_action": "Review renewal consolidation scenario.",
    }
    evidence_rows = [
        {
            "asset_id": "AS000000001",
            "issue_summary": "Missing entitlement",
            "asset_data_confidence_pct": 78.0,
        }
    ]

    brief = build_grounded_account_brief(account, evidence_rows)

    assert "Kanto Systems 001" in brief["summary"]
    assert validate_grounding(
        brief,
        {"account_positioning:A00001", "asset_reconciliation:AS000000001"},
    )
    assert not validate_grounding(brief, {"account_positioning:A00001"})
