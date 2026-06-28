from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import Paths, get_paths, load_scoring_config
from .data_generator import generate_dataset
from .db import connect, execute_sql_files, load_raw_tables, table_exists
from .gtm import compute_gtm_metrics
from .scoring import score_accounts


def build_warehouse(paths: Paths | None = None) -> Path:
    project_paths = paths or get_paths()
    project_paths.warehouse.mkdir(parents=True, exist_ok=True)
    config = load_scoring_config(project_paths.scoring_config)

    with connect(project_paths.database) as connection:
        load_raw_tables(connection, project_paths)
        execute_sql_files(
            connection,
            [
                project_paths.sql / "01_staging.sql",
                project_paths.sql / "02_asset_reconciliation.sql",
                project_paths.sql / "03_account_features.sql",
            ],
        )
        features = connection.execute(
            "SELECT * FROM account_features ORDER BY account_id"
        ).fetchdf()
        scored = score_accounts(features, config)
        connection.register("scored_accounts_df", scored)
        connection.execute(
            "CREATE OR REPLACE TABLE account_positioning AS SELECT * FROM scored_accounts_df"
        )
        connection.unregister("scored_accounts_df")

        gtm_raw = connection.execute("SELECT * FROM raw_gtm_monthly").fetchdf()
        gtm_metrics = compute_gtm_metrics(gtm_raw)
        connection.register("gtm_metrics_df", gtm_metrics)
        connection.execute(
            "CREATE OR REPLACE TABLE gtm_monthly_metrics AS SELECT * FROM gtm_metrics_df"
        )
        connection.unregister("gtm_metrics_df")

        execute_sql_files(
            connection,
            [project_paths.sql / "04_gtm.sql", project_paths.sql / "05_views.sql"],
        )

        if not table_exists(connection, "account_positioning"):
            raise RuntimeError("account_positioning was not created")
    return project_paths.database


def bootstrap(
    account_count: int = 250,
    asset_count: int = 25_000,
    seed: int = 42,
    paths: Paths | None = None,
) -> Path:
    project_paths = paths or get_paths()
    generate_dataset(
        project_paths.raw,
        account_count=account_count,
        asset_count=asset_count,
        seed=seed,
    )
    return build_warehouse(project_paths)


def export_outputs(paths: Paths | None = None) -> list[Path]:
    project_paths = paths or get_paths()
    project_paths.outputs.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    queries = {
        "account_playbook.csv": """
            SELECT account_id, account_name, industry, customer_business_model,
                   segment, sales_theater, region, sales_group, sales_manager,
                   ae_name, route_to_market, strategic_tier, global_account_flag,
                   priority_score, priority_band, recommended_play, primary_competitor,
                   portfolio_domain_count, deployment_model_count,
                   physical_or_hybrid_pct, software_subscription_pct,
                   estimated_tcv_jpy_mn, expected_commercial_value_jpy_mn,
                   data_confidence_pct, governance_status, positioning_angle,
                   next_best_action, data_story
            FROM account_positioning
            ORDER BY priority_score DESC
        """,
        "data_quality_summary.csv": """
            SELECT *
            FROM quality_signal_metrics
            ORDER BY planted_level, defect_type
        """,
        "renewal_pipeline.csv": """
            SELECT * FROM renewal_pipeline
            ORDER BY days_to_renewal, annual_value_jpy_mn DESC
        """,
        "gtm_company_monthly.csv": """
            SELECT * FROM gtm_company_monthly
            ORDER BY month
        """,
    }
    with connect(project_paths.database, read_only=True) as connection:
        for filename, query in queries.items():
            frame: pd.DataFrame = connection.execute(query).fetchdf()
            path = project_paths.outputs / filename
            frame.to_csv(path, index=False)
            outputs.append(path)
    return outputs


def validate_warehouse(paths: Paths | None = None) -> dict[str, int | float]:
    project_paths = paths or get_paths()
    with connect(project_paths.database, read_only=True) as connection:
        metrics = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM stg_accounts) AS accounts,
                (SELECT COUNT(*) FROM stg_assets) AS assets,
                (SELECT COUNT(*) FROM account_positioning) AS scored_accounts,
                (
                    SELECT COUNT(*) FROM asset_reconciliation
                    WHERE reconciliation_status = 'Verified'
                ) AS verified_assets,
                (
                    SELECT COUNT(*) FROM account_positioning
                    WHERE governance_status = 'Forecast-ready'
                ) AS forecast_ready_accounts,
                (
                    SELECT planted_count FROM quality_signal_metrics
                    WHERE planted_level = 'ALL' AND defect_type = 'ALL'
                ) AS known_quality_signals,
                (
                    SELECT recall_pct FROM quality_signal_metrics
                    WHERE planted_level = 'ALL' AND defect_type = 'ALL'
                ) AS quality_signal_recall_pct,
                (
                    SELECT fpr FROM quality_signal_metrics
                    WHERE planted_level = 'ALL' AND defect_type = 'ALL'
                ) AS quality_signal_fpr
            """
        ).fetchone()
    assert metrics is not None
    keys = [
        "accounts",
        "assets",
        "scored_accounts",
        "verified_assets",
        "forecast_ready_accounts",
        "known_quality_signals",
        "quality_signal_recall_pct",
        "quality_signal_fpr",
    ]
    result = dict(zip(keys, metrics, strict=True))
    if result["accounts"] != result["scored_accounts"]:
        raise AssertionError("Every account must have exactly one scored record")
    if result["assets"] <= 0:
        raise AssertionError("Asset table is empty")
    return result
