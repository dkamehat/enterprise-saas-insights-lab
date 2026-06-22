from __future__ import annotations

import shutil
from pathlib import Path

from saas_insights.config import get_paths, project_root
from saas_insights.pipeline import bootstrap, validate_warehouse


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    source_root = project_root()
    shutil.copytree(source_root / "sql", tmp_path / "sql")
    shutil.copytree(source_root / "config", tmp_path / "config")
    paths = get_paths(tmp_path)

    database = bootstrap(account_count=12, asset_count=300, seed=7, paths=paths)
    metrics = validate_warehouse(paths)

    assert database.exists()
    assert metrics["accounts"] == 12
    assert metrics["scored_accounts"] == 12
    assert metrics["assets"] == 300
