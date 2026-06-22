# Build Report

## Validation status

- Unit and integration tests: 5 passed
- Ruff: passed
- Streamlit health endpoint: passed
- Warehouse invariants: passed

## Demo dataset

- Accounts: 250
- Assets: 25,000
- Scored accounts: 250
- Verified assets: 8,055
- Forecast-ready accounts: 216
- Evidence-required accounts: 34
- Known quality signals: 24,802
- Quality signal recall: 100.0%
- Quality signal FPR: 0.0
- True Forward exposure: JPY 2,326.7M
- Average modeled NRR: 95.1%

## Sales-play distribution

- AI Data Platform: 115
- Renewal / Enterprise Plan: 58
- Security Platform: 40
- Platform Modernization: 37

## Priority distribution

- High: 64
- Medium: 166
- Low: 20

## Added analytical dimensions

- Industry and customer business model
- Sales theater, region, sales group, sales manager, and AE/member
- Route to market and global-account flag
- Portfolio domain, deployment model, commercial model
- Physical/hybrid mix and software-subscription mix

## Commands executed

```bash
pytest
ruff check .
python -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42
python -m saas_insights.cli export
python -m saas_insights.cli validate
streamlit run app.py --server.headless true
```

All values are generated from synthetic data and illustrative rules.
