# Build Report

## Validation status

- Unit and integration tests: 4 passed
- Ruff: passed
- Streamlit health endpoint: passed
- Warehouse invariants: passed

## Demo dataset

- Accounts: 250
- Assets: 25,000
- Scored accounts: 250
- Verified assets: 8,045
- Forecast-ready accounts: 214
- Evidence-required accounts: 36

## Sales-play distribution

- AI Data Platform: 113
- Renewal / Enterprise Plan: 65
- Platform Modernization: 39
- Security Platform: 33

## Priority distribution

- High: 69
- Medium: 160
- Low: 21

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
