from __future__ import annotations

import shutil
from pathlib import Path

from saas_insights.config import get_paths, project_root
from saas_insights.db import connect
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

    with connect(database, read_only=True) as connection:
        quality = connection.execute(
            """
            SELECT planted_count, recovered_count, fpr
            FROM quality_signal_metrics
            WHERE planted_level = 'ALL' AND defect_type = 'ALL'
            """
        ).fetchone()
        nrr_accounts = connection.execute("SELECT COUNT(*) FROM nrr_decomposition").fetchone()
        calibration = connection.execute(
            "SELECT closed_opportunities FROM forecast_calibration_summary"
        ).fetchone()

    assert quality is not None
    assert quality[0] > 0
    assert quality[1] == quality[0]
    assert quality[2] <= 0.05
    assert nrr_accounts is not None
    assert nrr_accounts[0] == 12
    assert calibration is not None
    assert calibration[0] > 0
