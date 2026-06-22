# Repository guidance for Codex

## Purpose
Build an explainable commercial analytics environment for Sales Insights Analysts. The repository uses synthetic data only. Never represent generated outputs as Cisco internal data, actual pricing, actual win rates, or production recommendations.

## Architecture
- `src/cisco_insights/data_generator.py`: deterministic synthetic source data.
- `sql/`: transformations from raw records to account-level commercial features.
- `src/cisco_insights/scoring.py`: transparent play scoring and score drivers.
- `src/cisco_insights/recommendations.py`: positioning and next-best-action rules.
- `src/cisco_insights/tco.py`: adjustable scenario model.
- `pages/`: Streamlit decision-support views.
- `config/scoring.toml`: business-owned weights and thresholds.

## Required workflow
1. Read `README.md`, `docs/architecture.md`, and relevant tests before changing logic.
2. Preserve auditability: every score must expose its component drivers.
3. Keep deterministic commercial rules separate from probabilistic or generative AI.
4. Add or update tests whenever scoring, reconciliation, TCO, or governance logic changes.
5. Run `pytest` and `ruff check .` before finishing.
6. Do not add external network calls, customer data, credentials, or unapproved LLM APIs.

## Commands
- Install: `python -m pip install -e ".[dev]"`
- Generate and build: `make bootstrap`
- Run tests: `make test`
- Run dashboard: `make app`

## Review guidelines
- Flag leakage of PII or confidential commercial data.
- Flag any score without traceable drivers or bounded outputs.
- Flag generated-AI output used as a source of truth for contract scope, pricing, compliance, or forecast commit.
- Flag SQL joins that can multiply asset rows without an explicit uniqueness check.
