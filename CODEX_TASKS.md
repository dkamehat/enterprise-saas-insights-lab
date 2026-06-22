# Suggested Codex tasks

Use these as follow-on prompts after the baseline repository is running.

## Task 1 — Replace CSV ingestion with Salesforce extracts
Implement adapters behind a `DataSource` protocol. Keep the synthetic adapter as the default. Add schema validation, incremental loads, and a field-mapping document. Do not add credentials to the repository.

## Task 2 — Add champion/challenger propensity models
Keep the deterministic score as the champion. Add a calibrated, interpretable challenger model with time-based validation, feature leakage checks, SHAP-style explanations or equivalent, and model-card documentation. The dashboard must show both models and disagreement cases.

## Task 3 — Add governed AI summarization
Add an optional interface that summarizes approved, redacted account evidence into an AE briefing. It must not calculate price, determine entitlement, change forecast category, or send content externally. Store prompt version, source record IDs, output, reviewer, and override reason.

## Task 4 — Production hardening
Add role-based access control, row-level security, encrypted secrets, observability, lineage, scheduled pipeline runs, data contracts, and deployment manifests. Preserve the local demo path.
