from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Paths:
    root: Path
    raw: Path
    warehouse: Path
    outputs: Path
    sql: Path
    scoring_config: Path
    database: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_paths(root: Path | None = None) -> Paths:
    base = (root or project_root()).resolve()
    return Paths(
        root=base,
        raw=base / "data" / "raw",
        warehouse=base / "data" / "warehouse",
        outputs=base / "outputs",
        sql=base / "sql",
        scoring_config=base / "config" / "scoring.toml",
        database=base / "data" / "warehouse" / "sales_insights.duckdb",
    )


def load_scoring_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or get_paths().scoring_config
    with config_path.open("rb") as handle:
        return tomllib.load(handle)
