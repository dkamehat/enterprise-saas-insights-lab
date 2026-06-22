# Cisco Sales Insights Lab

CiscoのSales Insights Analyst面接で説明した分析を、**合成データだけで再現する実行可能な分析環境**です。

> このリポジトリに含まれる顧客、資産、価格、競合シグナル、スコア係数はすべてデモ用です。Ciscoの社内データ、実価格、実際の勝率、正式な製品推奨ではありません。

## できること

- 25,000件のInstalled Baseを含む合成データを生成
- Asset / Contract / Entitlementの照合
- Verified / Reconcilable / Unknownへの分類
- Campus Refresh、Security Platform、AI Data Center、Renewal / EAの機会スコアリング
- Account別の競合ポジショニングとNext Best Action生成
- Baseとなるデータ信頼度を用いたForecast governance
- Cisco継続対競合移行の調整可能な3年TCOシナリオ
- StreamlitによるPortfolio、Account 360、競合、品質、ガバナンス画面
- AE向けPlaybook、Renewal Pipeline、品質サマリーのCSV出力

## 5分で起動

Python 3.11〜3.13を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m cisco_insights.cli bootstrap --accounts 250 --assets 25000 --seed 42
python -m cisco_insights.cli export
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。

Makeを使う場合：

```bash
make setup
make bootstrap
make app
```

Dockerの場合：

```bash
docker compose up --build
```

## Codexで使う

1. このフォルダをGitHubリポジトリへpushする。
2. Codexでリポジトリを開く。
3. Codexはルートの`AGENTS.md`から、テスト方法、監査性、AI利用境界を読み取る。
4. `CODEX_TASKS.md`のタスクを順番に依頼する。

最初の依頼例：

```text
Read AGENTS.md, README.md, and docs/architecture.md.
Run the existing tests and bootstrap the demo warehouse.
Then review the scoring pipeline for row multiplication, leakage,
and untraceable business rules. Fix only high-confidence issues,
add regression tests, and summarize the resulting decision logic.
```

## デモシナリオ

### 1. Executive Portfolio

Priorityが高いAccountを、Expected ValueとData Confidenceを含めて絞り込みます。

### 2. Account 360

一つの顧客について、以下を一画面で説明します。

- 推奨Sales Play
- 主要競合
- Score driver
- Data Story
- Next Best Action
- Asset reconciliation
- 3年TCO

### 3. Competitive Positioning

横軸をCisco Sales Play Fit、縦軸をCompetitive Pressureとして、以下を分離します。

- 高Fit・高競争圧力：Defend / Accelerate
- 高Fit・低競争圧力：Proactive expansion
- 低Fit・高競争圧力：選別または別ポジショニング

### 4. Data Quality

未照合資産をCommitへ含めず、Evidence requiredとして別キューにします。

### 5. Model Governance

Scoreの重み、Driver、Data Confidence、Forecast recommendationを追跡します。

## コマンド

```bash
# 合成データ生成 + Warehouse構築
cisco-insights bootstrap --accounts 250 --assets 25000 --seed 42

# raw CSVから再構築
cisco-insights build

# 整合性確認
cisco-insights validate

# CSV出力
cisco-insights export

# テスト
pytest

# Lint
ruff check .
```

## 主要成果物

- `data/warehouse/sales_insights.duckdb`
- `outputs/account_playbook.csv`
- `outputs/data_quality_summary.csv`
- `outputs/renewal_pipeline.csv`

## ディレクトリ

```text
config/              Business-owned weights and thresholds
sql/                 Staging, reconciliation, feature models, views
src/cisco_insights/  Generator, pipeline, scoring, recommendations, TCO
pages/               Streamlit decision-support pages
tests/               Unit and integration tests
docs/                Architecture, data dictionary, demo guide
AGENTS.md             Persistent repository guidance for Codex
CODEX_TASKS.md        Follow-on implementation tasks
```

## 本番化時に必要な追加項目

このデモはローカル・単一ユーザー向けです。本番投入には以下が必要です。

- Salesforce / CCW / Installed Base等への承認済みAdapter
- IAM、RBAC、Row-level security
- PII・機密情報の分類とマスキング
- Data contract、Lineage、Incremental load、監視
- 価格・Entitlement・Complianceの正式なSystem of Record
- Model validation、Override workflow、監査ログ
- APJC運用のSLA、Owner、Escalation設計
