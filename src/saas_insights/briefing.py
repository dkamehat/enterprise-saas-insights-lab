from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _source_ref(prefix: str, row_id: object) -> str:
    return f"{prefix}:{row_id}"


def build_grounded_account_brief(
    account: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    account_id = str(account["account_id"])
    account_ref = _source_ref("account_positioning", account_id)
    evidence_refs = [
        _source_ref("asset_reconciliation", row["asset_id"])
        for row in evidence_rows
        if row.get("asset_id")
    ]
    citations = [account_ref, *evidence_refs[:5]]

    brief = {
        "title": f"Grounded account brief for {account['account_name']}",
        "allowed_use": (
            "Draft stakeholder briefing only. Pricing, discounting, entitlement actions, "
            "and forecast commits require human approval."
        ),
        "summary": (
            f"{account['account_name']} is prioritized as {account['priority_band']} "
            f"for {account['recommended_play']} with a priority score of "
            f"{float(account['priority_score']):.1f}."
        ),
        "why_now": (
            f"Expected commercial value is JPY "
            f"{float(account['expected_commercial_value_jpy_mn']):.1f}M, "
            f"with data confidence at {float(account['data_confidence_pct']):.1f}%."
        ),
        "recommended_next_step": str(account["next_best_action"]),
        "evidence_summary": [
            {
                "asset_id": row.get("asset_id"),
                "issue_summary": row.get("issue_summary", ""),
                "confidence": row.get("asset_data_confidence_pct"),
            }
            for row in evidence_rows[:5]
        ],
        "citations": citations,
    }
    return brief


def validate_grounding(brief: Mapping[str, Any], allowed_citations: set[str]) -> bool:
    citations = set(brief.get("citations", []))
    return bool(citations) and citations.issubset(allowed_citations)
