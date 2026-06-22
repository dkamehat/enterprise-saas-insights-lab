from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

AS_OF_DATE = pd.Timestamp("2026-06-21")

PRODUCT_FAMILIES = [
    "Campus Network",
    "Data Center Network",
    "Security",
    "Observability",
    "Collaboration",
]

VENDOR_PROBABILITIES: dict[str, tuple[list[str], list[float]]] = {
    "Campus Network": (
        ["Cisco", "HPE Networking", "Arista", "Huawei", "Other"],
        [0.67, 0.16, 0.07, 0.04, 0.06],
    ),
    "Data Center Network": (
        ["Cisco", "Arista", "NVIDIA", "HPE Networking", "White Box"],
        [0.51, 0.24, 0.09, 0.09, 0.07],
    ),
    "Security": (
        ["Cisco", "Palo Alto Networks", "Fortinet", "Zscaler", "CrowdStrike", "Other"],
        [0.27, 0.22, 0.20, 0.13, 0.10, 0.08],
    ),
    "Observability": (
        ["Cisco", "Datadog", "Dynatrace", "New Relic", "Other"],
        [0.34, 0.25, 0.18, 0.13, 0.10],
    ),
    "Collaboration": (
        ["Cisco", "Microsoft", "Zoom", "RingCentral", "Other"],
        [0.34, 0.37, 0.18, 0.06, 0.05],
    ),
}

MODELS: dict[tuple[str, str], list[str]] = {
    ("Campus Network", "Cisco"): ["Catalyst 9300", "Catalyst 9500", "Meraki MS", "Catalyst AP"],
    ("Campus Network", "HPE Networking"): ["Aruba CX", "Aruba Central AP"],
    ("Campus Network", "Arista"): ["Arista 720XP", "Arista Campus"],
    ("Data Center Network", "Cisco"): ["Nexus 9300", "Nexus 9500", "Cisco 8000"],
    ("Data Center Network", "Arista"): ["Arista 7050X", "Arista 7800R"],
    ("Data Center Network", "NVIDIA"): ["Spectrum-X", "Quantum InfiniBand"],
    ("Security", "Cisco"): ["Secure Firewall", "Duo", "Umbrella", "Secure Access"],
    ("Security", "Palo Alto Networks"): ["PA-Series", "Prisma Access", "Cortex"],
    ("Security", "Fortinet"): ["FortiGate", "FortiSASE"],
    ("Security", "Zscaler"): ["ZIA", "ZPA"],
    ("Security", "CrowdStrike"): ["Falcon"],
    ("Observability", "Cisco"): ["Splunk", "ThousandEyes", "AppDynamics"],
    ("Observability", "Datadog"): ["Datadog Platform"],
    ("Observability", "Dynatrace"): ["Dynatrace Platform"],
    ("Observability", "New Relic"): ["New Relic One"],
    ("Collaboration", "Cisco"): ["Webex Suite", "Webex Contact Center", "Cisco Room"],
    ("Collaboration", "Microsoft"): ["Teams", "Teams Rooms"],
    ("Collaboration", "Zoom"): ["Zoom Workplace", "Zoom Rooms"],
}

PLAY_COMPETITORS = {
    "Campus Refresh": ["HPE Networking", "Arista", "Huawei", "No Decision"],
    "Security Platform": [
        "Palo Alto Networks",
        "Fortinet",
        "Zscaler",
        "CrowdStrike",
        "No Decision",
    ],
    "AI Data Center": ["Arista", "NVIDIA", "HPE Networking", "White Box", "No Decision"],
    "Renewal / EA": ["No Decision", "HPE Networking", "Palo Alto Networks", "Fortinet"],
}


def _choice(
    rng: np.random.Generator, values: list[Any], probabilities: list[float] | None = None
) -> Any:
    return (
        rng.choice(values, p=probabilities).item()
        if hasattr(rng.choice(values, p=probabilities), "item")
        else rng.choice(values, p=probabilities)
    )


def _random_date(rng: np.random.Generator, start: pd.Timestamp, end: pd.Timestamp) -> pd.Timestamp:
    days = max((end - start).days, 1)
    return start + pd.Timedelta(days=int(rng.integers(0, days)))


def _vendor_for_family(rng: np.random.Generator, family: str, cisco_affinity: float = 0.0) -> str:
    vendors, base_probs = VENDOR_PROBABILITIES[family]
    probs = np.array(base_probs, dtype=float)
    if "Cisco" in vendors:
        idx = vendors.index("Cisco")
        shift = min(max(cisco_affinity, -0.20), 0.20)
        probs[idx] = max(0.05, probs[idx] + shift)
        others = [i for i in range(len(probs)) if i != idx]
        delta = probs.sum() - 1.0
        for i in others:
            probs[i] = max(0.01, probs[i] - delta * (probs[i] / probs[others].sum()))
        probs = probs / probs.sum()
    return str(rng.choice(vendors, p=probs))


def _model_for(rng: np.random.Generator, family: str, vendor: str) -> str:
    candidates = MODELS.get((family, vendor), [f"{vendor} {family} Product"])
    return str(rng.choice(candidates))


def generate_dataset(
    output_dir: Path,
    account_count: int = 250,
    asset_count: int = 25_000,
    seed: int = 42,
) -> dict[str, Path]:
    if account_count < 5:
        raise ValueError("account_count must be at least 5")
    if asset_count < account_count * 5:
        raise ValueError("asset_count must be at least five times account_count")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    industries = [
        "Manufacturing",
        "Financial Services",
        "Retail",
        "Public Sector",
        "Healthcare",
        "Technology",
        "Logistics",
        "Telecommunications",
    ]
    prefixes = ["Kanto", "Kansai", "Chubu", "Hokkaido", "Kyushu", "Setouchi", "Tohoku"]
    suffixes = ["Industries", "Systems", "Holdings", "Services", "Group", "Network", "Solutions"]
    segments = ["Enterprise", "Commercial", "Public Sector"]
    regions = ["Japan East", "Japan West", "Japan Central"]
    tiers = ["Tier 1", "Tier 2", "Tier 3"]

    accounts: list[dict[str, Any]] = []
    for i in range(account_count):
        segment = str(rng.choice(segments, p=[0.50, 0.34, 0.16]))
        tier = str(rng.choice(tiers, p=[0.22, 0.43, 0.35]))
        enterprise_factor = 1.8 if segment == "Enterprise" else 1.0
        tier_factor = {"Tier 1": 1.8, "Tier 2": 1.25, "Tier 3": 0.8}[tier]
        revenue = float(
            np.clip(rng.lognormal(mean=7.6, sigma=0.85) * enterprise_factor, 200, 120_000)
        )
        employees = int(np.clip(rng.lognormal(mean=7.2, sigma=0.9) * tier_factor, 200, 120_000))
        ai_horizon = int(
            rng.choice([6, 12, 18, 24, 36, 60], p=[0.10, 0.18, 0.18, 0.19, 0.20, 0.15])
        )
        gpu_planned = bool(ai_horizon <= 18 and rng.random() < 0.70)
        accounts.append(
            {
                "account_id": f"A{i + 1:05d}",
                "account_name": f"{rng.choice(prefixes)} {rng.choice(suffixes)} {i + 1:03d}",
                "industry": str(rng.choice(industries)),
                "segment": segment,
                "region": str(rng.choice(regions, p=[0.46, 0.34, 0.20])),
                "ae_name": f"AE-{int(rng.integers(1, 31)):02d}",
                "partner_name": str(
                    rng.choice(
                        [
                            "Partner Alpha",
                            "Partner Beta",
                            "Partner Gamma",
                            "Partner Delta",
                            "Direct",
                        ]
                    )
                ),
                "strategic_tier": tier,
                "annual_revenue_jpy_mn": round(revenue, 1),
                "employee_count": employees,
                "cisco_relationship_years": int(rng.integers(0, 19)),
                "security_tool_count": int(rng.integers(1, 10)),
                "splunk_installed": bool(
                    rng.random() < (0.48 if segment == "Enterprise" else 0.22)
                ),
                "ai_investment_horizon_months": ai_horizon,
                "gpu_cluster_planned": gpu_planned,
                "budget_readiness_pct": round(float(rng.beta(2.4, 1.9) * 100), 1),
                "managed_service_interest": round(float(rng.beta(2.0, 2.4) * 100), 1),
                "budget_cycle_month": int(rng.integers(1, 13)),
            }
        )
    accounts_df = pd.DataFrame(accounts)

    contracts: list[dict[str, Any]] = []
    contract_lookup: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    contract_counter = 1
    for account in accounts:
        base = {"Tier 1": 8, "Tier 2": 5, "Tier 3": 3}[account["strategic_tier"]]
        count = max(2, int(rng.poisson(base)))
        for _ in range(count):
            family = str(rng.choice(PRODUCT_FAMILIES, p=[0.30, 0.19, 0.22, 0.15, 0.14]))
            affinity = min(account["cisco_relationship_years"] / 100.0, 0.15)
            vendor = _vendor_for_family(rng, family, affinity)
            contract_type = str(
                rng.choice(
                    ["Support", "Subscription", "Enterprise Agreement"], p=[0.43, 0.48, 0.09]
                )
            )
            term_years = int(rng.choice([1, 3, 5], p=[0.48, 0.42, 0.10]))
            start = _random_date(
                rng, AS_OF_DATE - pd.Timedelta(days=4 * 365), AS_OF_DATE + pd.Timedelta(days=180)
            )
            end = start + pd.Timedelta(days=term_years * 365)
            status = (
                "Expired" if end < AS_OF_DATE else ("Pending" if start > AS_OF_DATE else "Active")
            )
            annual_value = float(np.clip(rng.lognormal(mean=2.4, sigma=1.0), 0.8, 650.0))
            adoption = float(np.clip(rng.beta(2.8, 1.8) * 100, 5, 100))
            contract_id = f"C{contract_counter:07d}"
            contract_counter += 1
            record = {
                "contract_id": contract_id,
                "account_id": account["account_id"],
                "vendor": vendor,
                "product_family": family,
                "contract_type": contract_type,
                "start_date": start.date().isoformat(),
                "end_date": end.date().isoformat(),
                "annual_value_jpy_mn": round(annual_value, 2),
                "currency": "JPY",
                "status": status,
                "renewal_probability_pct": round(
                    float(np.clip(adoption * 0.7 + rng.normal(20, 12), 5, 98)), 1
                ),
                "adoption_pct": round(adoption, 1),
                "discount_pct": round(float(np.clip(rng.normal(17, 9), 0, 48)), 1),
                "ea_eligible": bool(
                    vendor == "Cisco"
                    and contract_type != "Enterprise Agreement"
                    and annual_value > 8
                ),
                "source_system": str(
                    rng.choice(["Salesforce", "CCW", "Partner Feed"], p=[0.48, 0.37, 0.15])
                ),
            }
            contracts.append(record)
            contract_lookup[(account["account_id"], vendor, family)].append(contract_id)
    contracts_df = pd.DataFrame(contracts)

    base_assets_per_account = 5
    remaining = asset_count - account_count * base_assets_per_account
    account_weights = np.array(
        [
            np.sqrt(a["employee_count"])
            * ({"Tier 1": 1.6, "Tier 2": 1.15, "Tier 3": 0.8}[a["strategic_tier"]])
            for a in accounts
        ],
        dtype=float,
    )
    account_weights /= account_weights.sum()
    allocations = rng.multinomial(remaining, account_weights) + base_assets_per_account

    assets: list[dict[str, Any]] = []
    asset_counter = 1
    for account, allocation in zip(accounts, allocations, strict=True):
        cisco_affinity = min(account["cisco_relationship_years"] / 80.0, 0.20)
        for _ in range(int(allocation)):
            family = str(rng.choice(PRODUCT_FAMILIES, p=[0.37, 0.19, 0.20, 0.12, 0.12]))
            vendor = _vendor_for_family(rng, family, cisco_affinity)
            model = _model_for(rng, family, vendor)
            install_date = _random_date(rng, pd.Timestamp("2014-01-01"), AS_OF_DATE)
            lifetime_years = int(rng.integers(5, 10))
            eol_date = install_date + pd.Timedelta(days=lifetime_years * 365)
            eos_date = eol_date + pd.Timedelta(days=int(rng.integers(365, 1095)))
            matching_contracts = contract_lookup.get((account["account_id"], vendor, family), [])
            contract_id = (
                str(rng.choice(matching_contracts))
                if matching_contracts and rng.random() > 0.10
                else None
            )
            assets.append(
                {
                    "asset_id": f"AS{asset_counter:09d}",
                    "account_id": account["account_id"],
                    "site_id": f"{account['account_id']}-S{int(rng.integers(1, 18)):03d}",
                    "serial_number": f"SN{asset_counter:011d}",
                    "vendor": vendor,
                    "product_family": family,
                    "product_line": model.split()[0],
                    "model": model,
                    "install_date": install_date.date().isoformat(),
                    "eol_date": eol_date.date().isoformat(),
                    "end_of_support_date": eos_date.date().isoformat(),
                    "criticality": str(
                        rng.choice(
                            ["Critical", "High", "Medium", "Low"], p=[0.12, 0.30, 0.43, 0.15]
                        )
                    ),
                    "utilization_pct": round(float(np.clip(rng.beta(2.5, 2.2) * 110, 2, 100)), 1),
                    "port_speed_gbps": int(
                        rng.choice(
                            [1, 10, 25, 40, 100, 400, 800],
                            p=[0.20, 0.23, 0.12, 0.10, 0.22, 0.10, 0.03],
                        )
                    ),
                    "contract_id": contract_id,
                    "entitlement_id": None,
                    "source_system": str(
                        rng.choice(
                            ["Install Base", "Partner Feed", "Telemetry", "Manual Upload"],
                            p=[0.48, 0.22, 0.20, 0.10],
                        )
                    ),
                    "last_verified_date": _random_date(
                        rng, AS_OF_DATE - pd.Timedelta(days=730), AS_OF_DATE
                    )
                    .date()
                    .isoformat(),
                }
            )
            asset_counter += 1
    assets_df = pd.DataFrame(assets)

    duplicate_count = max(1, int(len(assets_df) * 0.018))
    duplicate_rows = rng.choice(assets_df.index[1:], size=duplicate_count, replace=False)
    source_rows = rng.choice(assets_df.index[:-1], size=duplicate_count, replace=True)
    assets_df.loc[duplicate_rows, "serial_number"] = assets_df.loc[
        source_rows, "serial_number"
    ].to_numpy()
    missing_serial_rows = rng.choice(
        assets_df.index, size=max(1, int(len(assets_df) * 0.004)), replace=False
    )
    assets_df.loc[missing_serial_rows, "serial_number"] = None

    all_contract_ids = contracts_df["contract_id"].to_numpy()
    wrong_contract_rows = rng.choice(
        assets_df.index, size=max(1, int(len(assets_df) * 0.012)), replace=False
    )
    assets_df.loc[wrong_contract_rows, "contract_id"] = rng.choice(
        all_contract_ids, size=len(wrong_contract_rows), replace=True
    )

    entitlements: list[dict[str, Any]] = []
    entitlement_counter = 1
    eligible_mask = (assets_df["vendor"] == "Cisco") | (rng.random(len(assets_df)) < 0.22)
    eligible_indices = assets_df.index[eligible_mask]
    selected = eligible_indices[rng.random(len(eligible_indices)) < 0.82]
    for idx in selected:
        asset = assets_df.loc[idx]
        entitlement_id = f"E{entitlement_counter:09d}"
        entitlement_counter += 1
        account_id = str(asset["account_id"])
        if rng.random() < 0.009:
            account_id = str(
                rng.choice(accounts_df.loc[accounts_df["account_id"] != account_id, "account_id"])
            )
        consumed = float(np.clip(rng.beta(2.5, 1.7), 0.01, 1.0))
        entitlements.append(
            {
                "entitlement_id": entitlement_id,
                "asset_id": asset["asset_id"],
                "account_id": account_id,
                "vendor": asset["vendor"],
                "product_family": asset["product_family"],
                "license_quantity": 1,
                "consumed_quantity": round(consumed, 3),
                "support_level": str(
                    rng.choice(["Basic", "Enhanced", "Premium"], p=[0.34, 0.49, 0.17])
                ),
                "start_date": asset["install_date"],
                "end_date": (AS_OF_DATE + pd.Timedelta(days=int(rng.integers(-300, 900))))
                .date()
                .isoformat(),
            }
        )
        assets_df.at[idx, "entitlement_id"] = entitlement_id
    entitlements_df = pd.DataFrame(entitlements)

    support_assets = assets_df.sample(
        n=min(max(500, int(asset_count * 0.09)), len(assets_df)), random_state=seed
    )
    support_cases: list[dict[str, Any]] = []
    for i, (_, asset) in enumerate(support_assets.iterrows(), start=1):
        opened = _random_date(rng, AS_OF_DATE - pd.Timedelta(days=540), AS_OF_DATE)
        severity = str(rng.choice(["S1", "S2", "S3", "S4"], p=[0.05, 0.20, 0.48, 0.27]))
        resolution = float(
            np.clip(
                rng.lognormal(mean=3.2 if severity in {"S1", "S2"} else 2.2, sigma=0.9), 0.5, 1500
            )
        )
        is_open = bool(rng.random() < (0.18 if severity in {"S1", "S2"} else 0.08))
        support_cases.append(
            {
                "case_id": f"SC{i:08d}",
                "account_id": asset["account_id"],
                "asset_id": asset["asset_id"],
                "severity": severity,
                "opened_date": opened.date().isoformat(),
                "closed_date": None
                if is_open
                else (opened + pd.Timedelta(hours=resolution)).date().isoformat(),
                "resolution_hours": round(resolution, 1),
                "status": "Open" if is_open else "Closed",
            }
        )
    support_cases_df = pd.DataFrame(support_cases)

    play_families = {
        "Campus Refresh": ["Campus Network"],
        "Security Platform": ["Security", "Observability"],
        "AI Data Center": ["Data Center Network"],
        "Renewal / EA": PRODUCT_FAMILIES,
    }
    competitor_signals: list[dict[str, Any]] = []
    signal_counter = 1
    for account in accounts:
        count = int(rng.poisson(1.4))
        account_assets = assets_df[assets_df["account_id"] == account["account_id"]]
        for _ in range(count):
            play = str(rng.choice(list(PLAY_COMPETITORS)))
            related_assets = account_assets[
                account_assets["product_family"].isin(play_families[play])
            ]
            non_cisco = related_assets.loc[related_assets["vendor"] != "Cisco", "vendor"]
            incumbent_candidates = non_cisco.value_counts().head(3).index.tolist()
            candidates = list(dict.fromkeys(incumbent_candidates + PLAY_COMPETITORS[play]))
            competitor = str(rng.choice(candidates)) if candidates else "No Decision"
            signal_type = str(
                rng.choice(
                    [
                        "Incumbent",
                        "RFP",
                        "PoC",
                        "Price Quote",
                        "Executive Mention",
                        "Renewal Delay",
                    ],
                    p=[0.24, 0.17, 0.16, 0.16, 0.13, 0.14],
                )
            )
            competitor_signals.append(
                {
                    "signal_id": f"CS{signal_counter:07d}",
                    "account_id": account["account_id"],
                    "sales_play": play,
                    "competitor": competitor,
                    "signal_type": signal_type,
                    "signal_strength_pct": round(float(np.clip(rng.normal(62, 22), 10, 100)), 1),
                    "observed_date": _random_date(
                        rng, AS_OF_DATE - pd.Timedelta(days=420), AS_OF_DATE
                    )
                    .date()
                    .isoformat(),
                    "source": str(
                        rng.choice(["AE Note", "Partner", "RFP", "Customer Meeting", "Win/Loss DB"])
                    ),
                }
            )
            signal_counter += 1
    competitor_signals_df = pd.DataFrame(competitor_signals)

    opportunities: list[dict[str, Any]] = []
    opp_counter = 1
    for account in accounts:
        count = max(1, int(rng.poisson(1.6)))
        account_signals = competitor_signals_df[
            competitor_signals_df["account_id"] == account["account_id"]
        ]
        for _ in range(count):
            play = str(rng.choice(list(PLAY_COMPETITORS), p=[0.31, 0.24, 0.17, 0.28]))
            matching = account_signals[account_signals["sales_play"] == play]
            competitor = (
                str(
                    matching.sort_values("signal_strength_pct", ascending=False).iloc[0][
                        "competitor"
                    ]
                )
                if not matching.empty
                else str(rng.choice(PLAY_COMPETITORS[play]))
            )
            stage = str(
                rng.choice(
                    [
                        "Discovery",
                        "Qualified",
                        "Proposal",
                        "Negotiation",
                        "Closed Won",
                        "Closed Lost",
                    ],
                    p=[0.22, 0.23, 0.20, 0.14, 0.13, 0.08],
                )
            )
            amount = float(np.clip(rng.lognormal(mean=3.7, sigma=1.0), 3, 2500))
            quote_multiplier = float(np.clip(rng.normal(1.0, 0.08), 0.75, 1.28))
            win_probability = {
                "Discovery": 15,
                "Qualified": 35,
                "Proposal": 55,
                "Negotiation": 72,
                "Closed Won": 100,
                "Closed Lost": 0,
            }[stage]
            win_probability = float(np.clip(win_probability + rng.normal(0, 8), 0, 100))
            opportunities.append(
                {
                    "opportunity_id": f"O{opp_counter:08d}",
                    "account_id": account["account_id"],
                    "sales_play": play,
                    "competitor": competitor,
                    "stage": stage,
                    "close_date": (AS_OF_DATE + pd.Timedelta(days=int(rng.integers(-120, 500))))
                    .date()
                    .isoformat(),
                    "amount_jpy_mn": round(amount, 2),
                    "quote_amount_jpy_mn": round(amount * quote_multiplier, 2),
                    "discount_pct": round(float(np.clip(rng.normal(19, 10), 0, 55)), 1),
                    "win_probability_pct": round(win_probability, 1),
                    "forecast_category": str(
                        rng.choice(
                            ["Pipeline", "Best Case", "Commit", "Omitted"],
                            p=[0.45, 0.25, 0.22, 0.08],
                        )
                    ),
                    "source_system": "Salesforce",
                }
            )
            opp_counter += 1
    opportunities_df = pd.DataFrame(opportunities)

    product_events_df = pd.DataFrame(
        [
            {
                "event_id": "PE001",
                "product_family": "Campus Network",
                "event_type": "Lifecycle",
                "effective_date": "2026-09-30",
                "description": "Illustrative legacy campus support transition",
                "recommended_action": "Assess refresh candidates",
            },
            {
                "event_id": "PE002",
                "product_family": "Data Center Network",
                "event_type": "New Offering",
                "effective_date": "2026-07-15",
                "description": "Illustrative higher-speed fabric option",
                "recommended_action": "Re-evaluate AI-ready design",
            },
            {
                "event_id": "PE003",
                "product_family": "Security",
                "event_type": "Service Level",
                "effective_date": "2026-08-01",
                "description": "Illustrative support tier change",
                "recommended_action": "Re-price affected renewals",
            },
            {
                "event_id": "PE004",
                "product_family": "Observability",
                "event_type": "Packaging",
                "effective_date": "2026-10-01",
                "description": "Illustrative packaging update",
                "recommended_action": "Review consolidation scenarios",
            },
        ]
    )

    metadata_df = pd.DataFrame(
        [
            {
                "generated_at": pd.Timestamp.utcnow().isoformat(),
                "as_of_date": AS_OF_DATE.date().isoformat(),
                "seed": seed,
                "account_count": len(accounts_df),
                "asset_count": len(assets_df),
                "synthetic_data": True,
                "disclaimer": (
                    "Illustrative synthetic data; not Cisco internal data or actual pricing."
                ),
            }
        ]
    )

    frames = {
        "accounts": accounts_df,
        "contracts": contracts_df,
        "assets": assets_df,
        "entitlements": entitlements_df,
        "support_cases": support_cases_df,
        "competitor_signals": competitor_signals_df,
        "opportunities": opportunities_df,
        "product_events": product_events_df,
        "dataset_meta": metadata_df,
    }
    paths: dict[str, Path] = {}
    for name, frame in frames.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths
