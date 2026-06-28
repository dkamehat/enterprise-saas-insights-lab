.PHONY: setup bootstrap build app test lint clean export dashboard screenshots

PYTHON ?= python

setup:
	$(PYTHON) -m pip install -e ".[dev]"

bootstrap:
	$(PYTHON) -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42

dashboard:
	$(PYTHON) scripts/build_delivery_dashboard.py

screenshots:
	$(PYTHON) scripts/capture_screenshots.py

demo-gif:
	$(PYTHON) scripts/capture_demo_gif.py

build:
	$(PYTHON) -m saas_insights.cli build

app:
	streamlit run app.py

test:
	pytest

lint:
	ruff check .

export:
	$(PYTHON) -m saas_insights.cli export

clean:
	rm -f data/raw/*.csv data/warehouse/*.duckdb outputs/*.csv
