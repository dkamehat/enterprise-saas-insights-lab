from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.ui import database_ready, read_df  # noqa: E402

st.set_page_config(page_title="Dataset Blueprint", layout="wide")
st.title("Dataset Blueprint")
st.caption(
    "This demo assumes a global enterprise SaaS portfolio with CRM, contracts, "
    "subscription inventory, entitlement, support, competitive, and product "
    "lifecycle data joined into explainable account-level marts."
)

if not database_ready():
    st.error("Build the demo warehouse first from the top page.")
    st.stop()

BLUEPRINT_TABLES = [
    {
        "layer": "Source landing",
        "table_name": "raw_accounts",
        "grain": "One customer account",
        "primary_key": "account_id",
        "business_use": "Industry, business model, theater, group, manager, AE coverage.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_assets",
        "grain": "One deployed asset or subscribed service instance",
        "primary_key": "asset_id",
        "business_use": "Physical, hybrid, and software portfolio footprint.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_contracts",
        "grain": "One commercial contract",
        "primary_key": "contract_id",
        "business_use": "Renewal timing, adoption, discount, and annual value.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_entitlements",
        "grain": "One license or support entitlement",
        "primary_key": "entitlement_id",
        "business_use": "License coverage, consumed quantity, and support level.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_support_cases",
        "grain": "One support case",
        "primary_key": "case_id",
        "business_use": "Incident pressure and customer health context.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_competitor_signals",
        "grain": "One account-level competitive signal",
        "primary_key": "signal_id",
        "business_use": "Competitive pressure by sales play and competitor.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_opportunities",
        "grain": "One sales opportunity",
        "primary_key": "opportunity_id",
        "business_use": "Open pipeline, commit count, quote variance, and forecast signal.",
    },
    {
        "layer": "Source landing",
        "table_name": "raw_product_events",
        "grain": "One product lifecycle event",
        "primary_key": "event_id",
        "business_use": "Reference data for lifecycle and portfolio planning narratives.",
    },
    {
        "layer": "Staging",
        "table_name": "stg_accounts",
        "grain": "Typed account dimension",
        "primary_key": "account_id",
        "business_use": "Canonical customer, sales coverage, and segmentation fields.",
    },
    {
        "layer": "Staging",
        "table_name": "stg_assets",
        "grain": "Typed asset dimension",
        "primary_key": "asset_id",
        "business_use": "Canonical inventory joined to contracts and entitlements.",
    },
    {
        "layer": "Governed mart",
        "table_name": "asset_reconciliation",
        "grain": "One asset with quality flags",
        "primary_key": "asset_id",
        "business_use": "Serial, contract, entitlement, and verification audit.",
    },
    {
        "layer": "Governed mart",
        "table_name": "account_features",
        "grain": "One account with engineered features",
        "primary_key": "account_id",
        "business_use": "Portfolio mix, renewal, incident, pipeline, and competition features.",
    },
    {
        "layer": "Decision mart",
        "table_name": "account_positioning",
        "grain": "One scored account",
        "primary_key": "account_id",
        "business_use": "Priority, sales play, data story, action, governance status.",
    },
    {
        "layer": "Decision view",
        "table_name": "renewal_pipeline",
        "grain": "One primary-vendor renewal contract",
        "primary_key": "contract_id",
        "business_use": "Renewal worklist with account priority and data confidence.",
    },
    {
        "layer": "Decision view",
        "table_name": "portfolio_summary",
        "grain": "Portfolio-level rollup",
        "primary_key": "single row",
        "business_use": "Executive KPI summary.",
    },
]

SOURCE_SYSTEMS = [
    {
        "source system": "CRM / account master",
        "lands as": "raw_accounts, raw_opportunities",
        "example owner": "Sales Ops",
    },
    {
        "source system": "Commerce and contract platform",
        "lands as": "raw_contracts",
        "example owner": "Deal Desk / Finance",
    },
    {
        "source system": "Subscription and asset inventory",
        "lands as": "raw_assets",
        "example owner": "Customer Success / Operations",
    },
    {
        "source system": "Licensing and entitlement service",
        "lands as": "raw_entitlements",
        "example owner": "Support Operations",
    },
    {
        "source system": "Support case system",
        "lands as": "raw_support_cases",
        "example owner": "Technical Support",
    },
    {
        "source system": "Competitive intelligence notes",
        "lands as": "raw_competitor_signals",
        "example owner": "Sales Strategy",
    },
    {
        "source system": "Product lifecycle catalog",
        "lands as": "raw_product_events",
        "example owner": "Product Operations",
    },
]

RELATIONSHIP_RULES = [
    {
        "relationship": "accounts -> assets / contracts / opportunities",
        "join key": "account_id",
        "cardinality": "1:N",
        "audit concern": "Every commercial signal must map to a known account.",
    },
    {
        "relationship": "assets -> contracts",
        "join key": "contract_id",
        "cardinality": "N:0..1",
        "audit concern": "Missing or orphan contracts create support-gap risk.",
    },
    {
        "relationship": "assets -> entitlements",
        "join key": "entitlement_id",
        "cardinality": "N:0..1",
        "audit concern": "Missing licenses limit forecast and renewal confidence.",
    },
    {
        "relationship": "assets -> account_features",
        "join key": "account_id",
        "cardinality": "N:1 aggregation",
        "audit concern": "Portfolio mix and data confidence are calculated at account grain.",
    },
    {
        "relationship": "account_features -> account_positioning",
        "join key": "account_id",
        "cardinality": "1:1",
        "audit concern": "One account should produce one governed recommendation.",
    },
]

ER_DOT = """
digraph dataset_blueprint {
  graph [
    rankdir=LR,
    bgcolor="transparent",
    pad="0.2",
    nodesep="0.45",
    ranksep="0.8"
  ];

  node [
    shape=record,
    style="rounded,filled",
    fillcolor="#f8fafc",
    color="#334155",
    fontname="Arial",
    fontsize=10
  ];

  edge [
    color="#64748b",
    fontname="Arial",
    fontsize=9,
    arrowsize=0.7
  ];

  stg_accounts [
    fillcolor="#dbeafe",
    label="{stg_accounts|PK account_id|industry / business model|theater / group / AE}"
  ];
  stg_assets [
    fillcolor="#dcfce7",
    label="{stg_assets|PK asset_id|FK account_id|FK contract_id|FK entitlement_id}"
  ];
  stg_contracts [
    fillcolor="#fef3c7",
    label="{stg_contracts|PK contract_id|FK account_id|renewal / adoption / value}"
  ];
  stg_entitlements [
    fillcolor="#fef3c7",
    label="{stg_entitlements|PK entitlement_id|FK asset_id|license / support coverage}"
  ];
  stg_support_cases [
    label="{stg_support_cases|PK case_id|FK account_id / asset_id|severity / resolution}"
  ];
  stg_competitor_signals [
    label="{stg_competitor_signals|PK signal_id|FK account_id|play / competitor / strength}"
  ];
  stg_opportunities [
    label="{stg_opportunities|PK opportunity_id|FK account_id|stage / amount / forecast}"
  ];
  stg_product_events [
    style="rounded,dashed,filled",
    label="{stg_product_events|PK event_id|product family|lifecycle reference}"
  ];

  asset_reconciliation [
    fillcolor="#fee2e2",
    label="{asset_reconciliation|asset grain|quality flags|confidence score}"
  ];
  account_features [
    fillcolor="#ede9fe",
    label="{account_features|account grain|portfolio mix|renewal / support / pipeline features}"
  ];
  account_positioning [
    fillcolor="#e0f2fe",
    label="{account_positioning|account grain|priority / play|story / governance}"
  ];
  renewal_pipeline [
    fillcolor="#f1f5f9",
    label="{renewal_pipeline|contract grain|days to renewal|priority context}"
  ];
  portfolio_summary [
    fillcolor="#f1f5f9",
    label="{portfolio_summary|portfolio grain|executive KPIs}"
  ];

  stg_accounts -> stg_assets [label="1:N account_id"];
  stg_accounts -> stg_contracts [label="1:N account_id"];
  stg_accounts -> stg_support_cases [label="1:N account_id"];
  stg_accounts -> stg_competitor_signals [label="1:N account_id"];
  stg_accounts -> stg_opportunities [label="1:N account_id"];

  stg_assets -> asset_reconciliation [label="base inventory"];
  stg_contracts -> asset_reconciliation [label="contract_id"];
  stg_entitlements -> asset_reconciliation [label="entitlement_id"];

  asset_reconciliation -> account_features [label="aggregate"];
  stg_contracts -> account_features [label="aggregate"];
  stg_support_cases -> account_features [label="aggregate"];
  stg_competitor_signals -> account_features [label="aggregate"];
  stg_opportunities -> account_features [label="aggregate"];
  stg_accounts -> account_features [label="dimension"];

  account_features -> account_positioning [label="score"];
  account_positioning -> renewal_pipeline [label="context"];
  account_positioning -> portfolio_summary [label="rollup"];
  stg_contracts -> renewal_pipeline [label="renewals"];
  stg_product_events -> account_features [style=dashed, label="future lifecycle signal"];
}
"""


def _sql_value(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def table_inventory() -> pd.DataFrame:
    table_names = [row["table_name"] for row in BLUEPRINT_TABLES]
    count_sql = "\nUNION ALL\n".join(
        f"SELECT {_sql_value(table_name)} AS table_name, "
        f"COUNT(*) AS record_count FROM {_sql_identifier(table_name)}"
        for table_name in table_names
    )
    counts = read_df(count_sql)

    table_list = ", ".join(_sql_value(table_name) for table_name in table_names)
    columns = read_df(
        f"""
        SELECT table_name, COUNT(*) AS column_count
        FROM information_schema.columns
        WHERE table_schema = 'main'
          AND table_name IN ({table_list})
        GROUP BY table_name
        """
    )

    blueprint = pd.DataFrame(BLUEPRINT_TABLES)
    inventory = blueprint.merge(counts, on="table_name", how="left").merge(
        columns, on="table_name", how="left"
    )
    layer_order = {
        "Source landing": 1,
        "Staging": 2,
        "Governed mart": 3,
        "Decision mart": 4,
        "Decision view": 5,
    }
    inventory["layer_order"] = inventory["layer"].map(layer_order)
    return inventory.sort_values(["layer_order", "table_name"]).drop(columns=["layer_order"])


metrics = read_df(
    """
    SELECT
        (SELECT COUNT(*) FROM stg_accounts) AS accounts,
        (SELECT COUNT(*) FROM stg_assets) AS assets,
        (SELECT COUNT(*) FROM stg_contracts) AS contracts,
        (SELECT COUNT(*) FROM stg_entitlements) AS entitlements,
        (SELECT COUNT(*) FROM account_positioning) AS scored_accounts,
        (
            SELECT COUNT(*) FROM account_positioning
            WHERE governance_status = 'Forecast-ready'
        ) AS forecast_ready_accounts
    """
).iloc[0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Accounts", f"{int(metrics['accounts']):,}")
m2.metric("Assets", f"{int(metrics['assets']):,}")
m3.metric("Contracts", f"{int(metrics['contracts']):,}")
m4.metric("Entitlements", f"{int(metrics['entitlements']):,}")
m5.metric("Forecast-ready", f"{int(metrics['forecast_ready_accounts']):,}")

st.subheader("ER-style relationship map")
st.markdown(
    "The core grain is **account_id**. Asset, contract, entitlement, support, "
    "competitive, and opportunity tables stay separate until governed features "
    "are built, which keeps joins auditable and avoids row multiplication."
)
st.graphviz_chart(ER_DOT, use_container_width=True)

left, right = st.columns([1, 1])
with left:
    st.subheader("Assumed source systems")
    st.dataframe(pd.DataFrame(SOURCE_SYSTEMS), use_container_width=True, hide_index=True)

with right:
    st.subheader("Relationship rules")
    st.dataframe(pd.DataFrame(RELATIONSHIP_RULES), use_container_width=True, hide_index=True)

st.subheader("Table inventory")
inventory = table_inventory()
st.dataframe(
    inventory,
    use_container_width=True,
    hide_index=True,
    column_config={
        "record_count": st.column_config.NumberColumn("record_count", format="%d"),
        "column_count": st.column_config.NumberColumn("column_count", format="%d"),
    },
)

st.subheader("Physical schema inspector")
selected_table = st.selectbox(
    "Inspect table schema",
    [row["table_name"] for row in BLUEPRINT_TABLES],
    index=[row["table_name"] for row in BLUEPRINT_TABLES].index("account_positioning"),
)
schema = read_df(
    """
    SELECT ordinal_position, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'main'
      AND table_name = ?
    ORDER BY ordinal_position
    """,
    [selected_table],
)
st.dataframe(schema, use_container_width=True, hide_index=True)
