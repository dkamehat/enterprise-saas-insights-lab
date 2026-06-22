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
- Verified assets: 7,856
- Forecast-ready accounts: 207
- Evidence-required accounts: 43

## Sales-play distribution

- AI Data Center: 104
- Renewal / EA: 63
- Security Platform: 52
- Campus Refresh: 31

## Priority distribution

- High: 69
- Medium: 155
- Low: 26

## Commands executed

```bash
pytest
ruff check .
python -m cisco_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42
python -m cisco_insights.cli export
python -m cisco_insights.cli validate
streamlit run app.py --server.headless true
```

All values are generated from synthetic data and illustrative rules.
