# Repository guidance for Codex

## Purpose
Build an explainable commercial analytics environment for enterprise SaaS portfolio decisions. The repository uses synthetic data only. Never represent generated outputs as any real company's internal data, actual pricing, actual win rates, or production recommendations.

## Architecture
- `src/saas_insights/data_generator.py`: deterministic synthetic source data.
- `src/saas_insights/gtm.py`: time-aware GTM panel + SaaS efficiency metrics
  (ARR/NRR/GRR, Rule of 40, Magic Number, CAC payback, LTV/CAC) from monthly drivers.
- `sql/`: transformations from raw records to account-level + GTM marts.
- `src/saas_insights/scoring.py`: transparent play scoring and score drivers.
- `src/saas_insights/recommendations.py`: positioning and next-best-action rules.
- `src/saas_insights/tco.py`: adjustable scenario model.
- `pages/`: Streamlit decision-support views (incl. GTM Economics).
- `delivery/`: secondary surfaces (Looker LookML, Apps Script web app, AppSheet)
  reading the same marts — keep metric definitions single-sourced in the warehouse.
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
