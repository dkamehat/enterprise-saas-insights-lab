from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import get_paths
from .db import connect


def database_ready() -> bool:
    return get_paths().database.exists()


def read_df(sql: str, parameters: list[Any] | None = None) -> pd.DataFrame:
    paths = get_paths()
    with connect(paths.database, read_only=True) as connection:
        return connection.execute(sql, parameters or []).fetchdf()


def format_jpy_mn(value: float) -> str:
    return f"¥{value:,.1f}M"


def root_path() -> Path:
    return get_paths().root
