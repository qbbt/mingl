# Decision Wave Engine — Master Build Prompt (Planning-First, Updated)

Use this prompt with Codex / Claude / Jules / similar agents.

## Role
You are a senior systems architect + implementation engineer. We are in **planning + MVP skeleton** stage.

## Product Intent
Build a **personal decision intelligence system** that starts as a trading-grade terminal and grows into:
1. Personal Cognitive OS
2. Trading Terminal
3. AI Decision Partner

The core value is:
- show a wave-like view of opportunities over time,
- compare predictions vs reality,
- rank what deserves attention now,
- learn from outcomes and improve weighting over time.

## Non-Negotiables
- **UI-first outcome visibility**: stock-chart-like UX, rapid timeframe switching, multi-chart workspace.
- **Data modularity**: arbitrary APIs + manual input are first-class.
- **Engine/UI separation**: core logic must be UI-agnostic.
- **Human-in-the-loop**: user can override weights and decisions.
- **Meta-awareness**: every contributor (including the user) gets measured and weighted by predictive performance.
- **Local-first** operation for solo use in MVP.

## Founder-Confirmed MVP Direction
- Build toward **IBKR execution hooks** (paper-first acceptable as staging path).
- Use **email** as first out-of-band channel; keep push/SMS/webhook pluggable.
- Manual input must support structured, parseable fields.
- Auto ranking mode should exist with easy manual override/toggle.
- Support high-power custom analytics functions for statistical/visual derivatives.
- Subsecond-readiness is required in architecture (target near-100ms capable ingestion path).

## Primary MVP Workflow
1. Display wave + predicted range for an entity.
2. Monitor residuals (predicted vs observed).
3. Trigger out-of-band alerts on bound violations/regime shifts.
4. Update leaderboard score manually/programmatically.
5. Record observations/decisions/outcomes for learning.
6. Improve contributor weights over time.

## Scope Priorities
Primary: intraday + swing, with easy zoom in/out and fast timeframe changes.
Secondary: arbitrary domains (games, life decisions, projects).
Deployment path: solo-first web app, but architect for iPhone-friendly access soon after.

## System Modules (MVP)
1. **Entity + Time Series Engine**
   - Entity abstraction for symbols/strategies/models/human notes.
   - Time-indexed values, events, and uncertainty metadata.

2. **Feed Plugin Layer**
   - Real-time and polling connectors.
   - Manual input and CSV import/export.
   - Standardized adapter interface (`fetch`, `normalize`, `publish`).
   - Broker adapter interface for IBKR execution hooks (`validate`, `paper_execute`, `live_execute`).

3. **Prediction + Bounds Layer**
   - Store predicted value/range/confidence/time window.
   - Compare against observed values continuously.

4. **Leaderboard / Ranking Layer**
   - Custom score function configurable at runtime.
   - Supports modes (risk/reward, growth, learning, overload).
   - Supports manual mode + auto mode with UI toggle/dropdown.

5. **Observation Layer**
   - Log: analysis time, decision time, execution time, outcome time.
   - Separate analysis error vs decision error vs execution error.
   - Capture manual rationale and explanation for overrides.

6. **Correlation/Regime Layer**
   - Rolling correlations, drift and regime-change detection.
   - Highlight notable correlation emergence/breakdown.
   - Maintain per-entity “Top-N relationships” view (e.g., top 10 / top 100).

7. **Notification Layer**
   - Out-of-band notifications for model failure, regime shift, high-impact anomalies.
   - MVP channel: email.
   - Pluggable channels: in-app, push, SMS, webhook.

8. **Visualization Layer (Web MVP)**
   - OHLC candlestick + overlays.
   - Prediction bands and event annotations.
   - Multi-panel workspace with synchronized time axis.
   - Fast timeframe switch UX (intraday ↔ swing ↔ multiweek).

## Data Model Requirements
Track at minimum:
- entities
- time series values
- predictions (with confidence intervals)
- outcomes
- decisions + notes
- contributor performance metrics
- leaderboard snapshots
- correlations / causal edges
- annotations with observed_time vs estimated_actual_time + margin_of_error
- user overrides + override rationale

## Ranking Model (Initial)
Use configurable weighted scoring:

`score = f(EV, confidence, volatility_penalty, opportunity_decay, attention_cost, execution_reliability)`

Must support:
- manual re-weighting,
- auto-adjustment from realized performance,
- per-context weights (e.g., high volatility vs low volatility regime),
- warning when contributor is consistently outside tolerance (e.g., 1-2 sigma miss bands).

## Meta-Aware Contributor Logic
Every signal source is a contributor:
- API feed
- indicator
- model
- AI assistant
- human input

Maintain per-contributor metrics:
- directional accuracy
- calibration error
- latency impact
- regime sensitivity
- override performance trend

Contributor weights should adapt from observed performance while allowing manual overrides.
Underperforming overrides should warn, not hard-block.

## Data Resolution + Retention Requirements
- Architect ingestion path to support subsecond events (including 100ms-class sources).
- Keep high-resolution data locally for at least 1 day before downsampling.
- Design storage strategy to optionally retain up to ~2 weeks of high-resolution history when resources permit.

## Deliverables Required from Agent
1. Proposed architecture diagram + module boundaries.
2. MVP repo skeleton with clean interfaces.
3. Database schema (MVP + migration path).
4. API/WebSocket contract definitions.
5. Example feed plugins (crypto + one non-crypto source).
6. Basic frontend with chart + leaderboard + annotation input.
7. Testing plan (unit + integration + replay harness stub).
8. “What to defer” list for post-MVP.
9. Explicit list of “assumptions requiring founder confirmation.”

## Constraints
- Don’t overfit to one data provider.
- Don’t hardcode ranking logic; keep it user-editable.
- Don’t bind core engine to one frontend framework.
- Keep implementation simple enough to ship quickly.
- Do not block user input/overrides unless explicitly configured.

## Agent Behavior
- Ask targeted clarifying questions when ambiguous.
- Prefer minimal viable architecture that preserves extensibility.
- Explicitly list assumptions.
- Highlight failure modes and observability requirements.
