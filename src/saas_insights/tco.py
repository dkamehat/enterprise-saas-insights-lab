from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd


def _f(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, default)
        return default if value is None else float(value)
    except (TypeError, ValueError):
        return default


def calculate_tco(
    row: Mapping[str, Any],
    config: Mapping[str, Any],
    competitor_discount_pct: float = 18.0,
    years: int | None = None,
) -> pd.DataFrame:
    cfg = config["tco"]
    horizon = int(years or cfg["default_years"])
    modernization_assets = max(_f(row, "modernization_asset_count"), 1.0)
    annual_contract = _f(row, "primary_annual_contract_value_jpy_mn")
    primary_share = _f(row, "primary_platform_share_pct") / 100.0
    incident_factor = 1.0 + _f(row, "incident_pressure_pct") / 100.0

    hardware_baseline = max(
        8.0,
        modernization_assets * float(cfg["primary_modernization_unit_jpy_mn"]),
        annual_contract * 0.75,
    )
    software_attach = hardware_baseline * float(cfg["software_attach_rate"])
    primary_product = hardware_baseline + software_attach
    competitor_product = hardware_baseline * (1 - competitor_discount_pct / 100.0) + software_attach

    primary_migration = primary_product * float(cfg["primary_migration_cost_rate"])
    competitor_migration = (
        competitor_product * float(cfg["competitor_migration_cost_rate"]) * (0.5 + primary_share)
    )
    primary_training = primary_product * float(cfg["primary_training_cost_rate"])
    competitor_training = (
        competitor_product * float(cfg["competitor_training_cost_rate"]) * (0.5 + primary_share)
    )
    primary_operations = primary_product * float(cfg["primary_annual_operations_rate"]) * horizon
    competitor_operations = (
        competitor_product * float(cfg["competitor_annual_operations_rate"]) * horizon
    )
    primary_risk = primary_product * float(cfg["primary_expected_risk_rate"]) * incident_factor
    competitor_risk = (
        competitor_product
        * float(cfg["competitor_expected_risk_rate"])
        * incident_factor
        * (0.7 + primary_share)
    )

    rows = [
        ("Product / software", primary_product, competitor_product),
        ("Migration / coexistence", primary_migration, competitor_migration),
        ("Training / operating change", primary_training, competitor_training),
        (f"Operations ({horizon} years)", primary_operations, competitor_operations),
        ("Expected disruption risk", primary_risk, competitor_risk),
    ]
    frame = pd.DataFrame(rows, columns=["cost_component", "primary_jpy_mn", "competitor_jpy_mn"])
    frame["delta_jpy_mn"] = frame["competitor_jpy_mn"] - frame["primary_jpy_mn"]
    return frame.round(2)
