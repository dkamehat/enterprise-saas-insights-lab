from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import duckdb
import pandas as pd

from .config import Paths, get_paths

RAW_TABLES = [
    "accounts",
    "contracts",
    "assets",
    "entitlements",
    "support_cases",
    "competitor_signals",
    "opportunities",
    "product_events",
    "planted_quality_signals",
    "gtm_monthly",
    "dataset_meta",
]


def connect(database: Path | None = None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    path = database or get_paths().database
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only)


def _sql_literal(path: Path) -> str:
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def load_raw_tables(connection: duckdb.DuckDBPyConnection, paths: Paths | None = None) -> None:
    project_paths = paths or get_paths()
    missing = [name for name in RAW_TABLES if not (project_paths.raw / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw files: {', '.join(missing)}")

    for name in RAW_TABLES:
        csv_path = project_paths.raw / f"{name}.csv"
        connection.execute(
            f"CREATE OR REPLACE TABLE raw_{name} AS "
            f"SELECT * FROM read_csv_auto({_sql_literal(csv_path)}, header=true, sample_size=-1)"
        )


def execute_sql_files(
    connection: duckdb.DuckDBPyConnection,
    files: Iterable[Path],
) -> None:
    for path in files:
        sql = path.read_text(encoding="utf-8")
        connection.execute(sql)


def table_exists(connection: duckdb.DuckDBPyConnection, name: str) -> bool:
    result = connection.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [name]
    ).fetchone()
    return bool(result and result[0])


def query_df(
    sql: str,
    parameters: list[object] | tuple[object, ...] | None = None,
    database: Path | None = None,
) -> pd.DataFrame:
    with connect(database=database, read_only=True) as connection:
        return connection.execute(sql, parameters or []).fetchdf()
