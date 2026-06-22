FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY sql ./sql
COPY pages ./pages
COPY app.py ./
COPY scripts ./scripts

RUN pip install --no-cache-dir .
RUN python -m cisco_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
