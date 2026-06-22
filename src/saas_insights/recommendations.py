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
                "単価比較に閉じず、既存業務フローとの連続性、移行・教育・二重運用を含む3年TCO、"
                "Security/Observability統合後の運用負荷まで並べて評価する。"
            )
        if competitor == "ServiceOps Cloud":
            return (
                "機能表だけで競わず、Core PlatformからData Platformまでの運用標準化、"
                "既存契約・権利・利用率、可視性とガバナンスを含む運用モデルで比較する。"
            )
        if competitor == "Regional Suite":
            return (
                "価格以外に、サポート継続性、セキュリティ統制、"
                "契約移管・運用リスクを定量化する。"
            )
        return (
            "更新延期のコストを可視化する。ライフサイクル移行、障害期待損失、保守切れ、"
            "将来の一括刷新コストを現状維持シナリオと比較する。"
        )

    if play == "Security Platform":
        if competitor == "SecureEdge Cloud":
            return (
                "機能数ではなく、Platform・Identity・Security・Log AnalyticsのTelemetry統合、"
                "運用コンソール削減、SOC工数と契約集約効果で比較する。"
            )
        if competitor == "ShieldOps Cloud":
            return (
                "初期価格だけでなく、Enterprise Governance、既存Platformとの統合、"
                "ライフサイクル運用、権限管理、3年TCOで比較する。"
            )
        if competitor == "ZeroTrust Cloud":
            return (
                "SSE単体の比較ではなく、Core Platform・Data Platformを含むHybrid環境の可視性、"
                "Identity連携、運用責任範囲を明確にする。"
            )
        if competitor == "Endpoint Cloud":
            return (
                "Endpoint単体ではなく、Platform、Identity、Detection/Response、"
                "Log Analyticsを横断した"
                "検知から復旧までの運用時間で比較する。"
            )
        return "ツール乱立、未使用ライセンス、SOC工数、検知・復旧時間を現状維持コストとして示す。"

    if play == "AI Data Platform":
        if competitor == "DataOps Cloud":
            return (
                "AI基盤の性能だけでなく、既存Core Platform/Data Platformとの接続、Security、"
                "Observability、運用スキル、段階移行を含むJob-to-operations全体で比較する。"
            )
        if competitor == "GPU Cloud Partner":
            return (
                "GPU統合の強みを認めた上で、異種環境、既存データ連携、セキュリティ、"
                "運用標準化を含む全体アーキテクチャで役割分担を設計する。"
            )
        if competitor == "Open Platform":
            return (
                "利用料だけではなく、自社運用開発、障害対応、ライフサイクル、サポート、"
                "人材確保を含む総保有コストで比較する。"
            )
        return "AI投資延期によるボトルネックと、既存Data Platformの段階的拡張案を比較する。"

    if play == "Renewal / Enterprise Plan":
        if competitor == "No Decision":
            return (
                "契約更新を事務処理として扱わず、失効・保守切れ・分散更新・追加調達の工数を"
                "一本化前後で比較する。"
            )
        return (
            f"{competitor}への切替価格だけでなく、資産照合、契約移行、未使用権利、"
            f"サポート継続性を含む商業ベースラインで比較する。"
        )

    return (
        f"主力SaaSベンダー比率{primary_share:.0f}%の既存環境を前提に、"
        "顧客成果と総保有コストで比較する。"
    )


def next_best_action(play: str, competitor: str, row: Mapping[str, Any]) -> str:
    confidence = _n(row.get("data_confidence_pct"))
    unknown = _n(row.get("unknown_assets_pct"))
    renewal_value = _n(row.get("renewal_value_180d_jpy_mn"))
    eol = _n(row.get("eol_18m_pct"))
    pressure = _n(row.get("competitive_pressure_pct"))

    actions: list[str] = []
    if confidence < 65 or unknown >= 15:
        actions.append("Unknown資産をAE・Partner・契約担当で照合し、Forecast対象と保留を分離")
    if renewal_value > 0:
        actions.append("180日以内更新のBase/Downside/Upsideを作成し、Ownerと期限を設定")
    if play == "Platform Modernization":
        actions.append("ライフサイクル移行対象を業務重要度で優先付けし、3年TCOと段階導入案を提示")
    elif play == "Security Platform":
        actions.append("Security製品・更新日・利用率を棚卸しし、統合前後のSOC工数を比較")
    elif play == "AI Data Platform":
        actions.append("AI workload、データ処理容量、GPU導入時期をDiscoveryし、PoC対象を選定")
    elif play == "Renewal / Enterprise Plan":
        actions.append("契約・更新月を集約し、現行契約対Enterprise Plan/複数年契約のシナリオを比較")
    if pressure >= 70 and competitor != "No Decision":
        actions.append(f"{competitor}の提案条件を証拠ベースで確認し、競合Workshopを設定")
    if eol >= 40 and play != "Platform Modernization":
        actions.append("Platform Modernizationを並行Sales Playとして追加評価")
    return " / ".join(actions[:4])


def data_story(play: str, competitor: str, row: Mapping[str, Any]) -> str:
    return (
        f"推奨は「{play}」。18か月以内の刷新対象は{_n(row.get('eol_18m_pct')):.1f}%、"
        f"主力SaaSベンダーのPlatform比率は{_n(row.get('primary_platform_share_pct')):.1f}%、"
        f"180日以内更新額は{_n(row.get('renewal_value_180d_jpy_mn')):.1f}百万円、"
        f"データ信頼度は{_n(row.get('data_confidence_pct')):.1f}%です。"
        f"主要競合は{competitor}であり、{positioning_angle(play, competitor, row)}"
    )
