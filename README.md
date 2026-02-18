# Decision Wave Engine (MVP v1.5 Optimizer Merge)

This build merges key ideas from your Grok prompt into the existing MVP **without breaking the current architecture**.

## What was merged from Grok prompt
- `/analytics/lag_sweep` for lag-based correlation scans
- `/analytics/correlations/matrix` for heatmap-ready matrix output
- `/analytics/wave/{entity_id}` series endpoint with SMA(20)
- `/analytics/media/sync` MP3 overlay integration stub
- `/status` self-documenting runtime status endpoint
- Frontend controls for heatmap + MP3 sync stub

## Current capability snapshot
- Arbitrary metric ingestion (`POST /observations` with `metric_name`, `source_url`, `extra_json`)
- Repeated graph fetch (`GET /graph/series`)
- Indicator overlays (`GET /indicators/{sma|ema}`)
- Pair + Top-N correlations (`/correlations/pair`, `/relationships/top`)
- Lag sweep + matrix analytics (`/analytics/*`)
- Email outbox processing (`POST /notifications/outbox/process`)
- IBKR adapter hooks (`POST /orders/paper`, `POST /orders/live`)
- Demo seeds including meal/trade scenario (`POST /demo/meal-trade-flow`)

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` dashboard
- `http://127.0.0.1:8000/docs` API docs
- `http://127.0.0.1:8000/status` build status

## Meal → trade flow (your concrete example)
1. Seed meal/trade data:
```bash
curl -X POST 'http://127.0.0.1:8000/demo/meal-trade-flow'
```
2. Fetch meal graph with links:
```bash
curl 'http://127.0.0.1:8000/graph/series?entity_id=<meal_id>&metric_name=calories'
```
3. Correlate against trade activity with lag:
```bash
curl 'http://127.0.0.1:8000/correlations/pair?entity_a_id=<meal_id>&entity_b_id=<trade_id>&lookback_points=120&lag_points=1'
```
4. Run lag sweep:
```bash
curl 'http://127.0.0.1:8000/analytics/lag_sweep?entity_a_id=<meal_id>&entity_b_id=<trade_id>&metric_a=calories&metric_b=trade_count&max_lag_days=14'
```
5. Heatmap-ready matrix:
```bash
curl 'http://127.0.0.1:8000/analytics/correlations/matrix?entity_ids=<meal_id>,<trade_id>&metric_name=calories'
```

## Notes on feasibility
- The Grok pseudo-program references pandas/scipy/iOS scaffolding and frontend rewrites. We integrated core backend behaviors now, while keeping codebase consistency.
- `media/sync` is intentionally a stub for UI/audio alignment contract; actual waveform-audio sync belongs in frontend playback pipeline.
- IBKR remains adapter-stubbed by design until credentials and gateway wiring are configured.

## Tests
```bash
cd backend
pytest -q
```
