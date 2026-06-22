.PHONY: setup bootstrap build app test lint clean export

PYTHON ?= python

setup:
	$(PYTHON) -m pip install -e ".[dev]"

bootstrap:
	$(PYTHON) -m saas_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42

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
