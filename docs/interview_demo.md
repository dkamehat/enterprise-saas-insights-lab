# Interview Demo Script

## 3-minute flow

### 1. Business question

「全Accountを同じ順序で追うのではなく、主力SaaSポートフォリオが価値を出せる条件、商業価値、競争圧力、データ信頼度を統合して営業工数を配分します。」

### 2. Portfolio

Executive PortfolioでHigh priorityを表示し、Sales Play別Expected Valueを見る。

### 3. Account drill-down

一つのAccountを開き、以下を順番に説明する。

1. 推奨Sales Playと競合
2. Score driver
3. Asset reconciliation
4. Positioning angle
5. Next Best Action
6. TCOシナリオ

### 4. Governance

Data Confidenceが不足する場合は、金額が大きくてもCommitへ入れず、Upside / Riskへ分ける。

## Recommended wording

> I separate commercial attractiveness from forecast confidence. A large opportunity can still be high priority for evidence collection, while remaining ineligible for Commit until the asset and contract baseline is reconciled.

> The output is not a dashboard alone. It is an account-specific recommendation: what to sell, why the primary SaaS portfolio can win, which evidence supports the position, and what the AE should do next.

## Trade-offs to explain

### Rule-based baseline

**Pros**: explainable, fast, auditable, works before labeled outcomes exist.  
**Cons**: weights require governance and may miss non-linear patterns.

### ML challenger

**Pros**: can improve ranking and calibration with sufficient outcome data.  
**Cons**: leakage, drift, explainability, and bias controls are required.

The recommended architecture is champion/challenger, not immediate replacement of business rules.
