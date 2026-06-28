from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _n(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def positioning_angle(play: str, competitor: str, row: Mapping[str, Any]) -> str:
    competitor = competitor or "No Decision"
    primary_share = _n(row.get("primary_platform_share_pct"))

    if play == "Platform Modernization":
        if competitor == "WorkSuite Cloud":
            return (
                "Compete beyond unit price: weigh continuity with existing workflows, a "
                "3-year TCO that includes migration, training and dual-running, and the "
                "operating load after Security/Observability consolidation."
            )
        if competitor == "ServiceOps Cloud":
            return (
                "Don't compete on a feature grid: compare the operating model — "
                "standardization from Core to Data Platform, existing contracts, "
                "entitlements and utilization, plus visibility and governance."
            )
        if competitor == "Regional Suite":
            return (
                "Beyond price, quantify support continuity, security control, and the "
                "cost and risk of contract migration and operations."
            )
        return (
            "Make the cost of deferring renewal visible: compare lifecycle migration, "
            "expected incident loss, end-of-support, and future big-bang refresh cost "
            "against the status-quo scenario."
        )

    if play == "Security Platform":
        if competitor == "SecureEdge Cloud":
            return (
                "Not feature count, but telemetry consolidation across Platform, Identity, "
                "Security and Log Analytics — fewer operating consoles, lower SOC effort, "
                "and contract-consolidation savings."
            )
        if competitor == "ShieldOps Cloud":
            return (
                "Beyond entry price, compare enterprise governance, integration with the "
                "existing platform, lifecycle operations, access management, and 3-year TCO."
            )
        if competitor == "ZeroTrust Cloud":
            return (
                "Not an SSE-only comparison: clarify visibility across the hybrid estate "
                "(Core and Data Platform), identity integration, and the split of "
                "operational responsibility."
            )
        if competitor == "Endpoint Cloud":
            return (
                "Not endpoint alone, but detection-to-recovery operating time across "
                "Platform, Identity, Detection/Response, and Log Analytics."
            )
        return (
            "Frame tool sprawl, unused licenses, SOC effort, and detect-to-recover time "
            "as the cost of the status quo."
        )

    if play == "AI Data Platform":
        if competitor == "DataOps Cloud":
            return (
                "Not just AI-platform performance, but the whole job-to-operations: "
                "connectivity with existing Core/Data Platform, security, observability, "
                "operating skills, and a phased migration."
            )
        if competitor == "GPU Cloud Partner":
            return (
                "Acknowledge the GPU-integration strength, then design role split across "
                "the full architecture — heterogeneous environments, existing data "
                "integration, security, and standardized operations."
            )
        if competitor == "Open Platform":
            return (
                "Not usage fees alone, but total cost of ownership including in-house "
                "operations, incident response, lifecycle, support, and staffing."
            )
        return (
            "Compare the bottleneck of deferring AI investment against a phased expansion "
            "of the existing Data Platform."
        )

    if play == "Renewal / Enterprise Plan":
        if competitor == "No Decision":
            return (
                "Treat renewal as more than paperwork: compare the effort of lapses, "
                "end-of-support, fragmented renewals, and ad-hoc procurement before vs "
                "after consolidation."
            )
        return (
            f"Not just the switching price to {competitor}, but a commercial baseline "
            "that includes asset reconciliation, contract migration, unused entitlements, "
            "and support continuity."
        )

    return (
        f"Given an installed base with {primary_share:.0f}% primary-SaaS-vendor platform "
        "share, compare on customer outcomes and total cost of ownership."
    )


def next_best_action(play: str, competitor: str, row: Mapping[str, Any]) -> str:
    confidence = _n(row.get("data_confidence_pct"))
    unknown = _n(row.get("unknown_assets_pct"))
    renewal_value = _n(row.get("renewal_value_180d_jpy_mn"))
    eol = _n(row.get("eol_18m_pct"))
    pressure = _n(row.get("competitive_pressure_pct"))

    actions: list[str] = []
    if confidence < 65 or unknown >= 15:
        actions.append(
            "Reconcile Unknown assets with AE / Partner / contract owner; "
            "split forecastable from on-hold"
        )
    if renewal_value > 0:
        actions.append(
            "Build Base/Downside/Upside for renewals within 180 days; set owner and date"
        )
    if play == "Platform Modernization":
        actions.append(
            "Prioritize lifecycle-migration targets by business criticality; present "
            "3-year TCO and a phased rollout"
        )
    elif play == "Security Platform":
        actions.append(
            "Inventory security products, renewal dates and utilization; compare SOC "
            "effort before vs after consolidation"
        )
    elif play == "AI Data Platform":
        actions.append(
            "Discovery on AI workload, data throughput and GPU timing; select a PoC target"
        )
    elif play == "Renewal / Enterprise Plan":
        actions.append(
            "Consolidate contracts and renewal months; compare current contracts vs an "
            "Enterprise Plan / multi-year scenario"
        )
    if pressure >= 70 and competitor != "No Decision":
        actions.append(
            f"Validate {competitor}'s proposal terms on the evidence; set a competitive workshop"
        )
    if eol >= 40 and play != "Platform Modernization":
        actions.append("Evaluate Platform Modernization as a parallel sales play")
    return " / ".join(actions[:4])


def data_story(play: str, competitor: str, row: Mapping[str, Any]) -> str:
    return (
        f"Recommended play: \"{play}\". Refresh candidates within 18 months are "
        f"{_n(row.get('eol_18m_pct')):.1f}%, primary-SaaS-vendor platform share is "
        f"{_n(row.get('primary_platform_share_pct')):.1f}%, renewal value within 180 days "
        f"is JPY {_n(row.get('renewal_value_180d_jpy_mn')):.1f}M, and data confidence is "
        f"{_n(row.get('data_confidence_pct')):.1f}%. The primary competitor is {competitor}; "
        f"{positioning_angle(play, competitor, row)}"
    )
