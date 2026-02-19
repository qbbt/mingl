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
# Decision Wave Engine (MVP v1)

Yes — with current build you can repeatedly fetch and graph **arbitrary metrics** (not only price), run Top-N correlations, apply indicators, trigger notifications, and call IBKR adapter hooks.


## Abstract Fundamental Form (Design North Star)

This system is intentionally built around a minimal invariant:
- entity -> metric stream -> state snapshot -> prediction -> evaluation -> allocation

Everything else (UI, notifications, IBKR integration, plugins) is layered tooling around that core.

See `docs/EVOLUTION_ARCHITECTURE.md` for the feasibility roadmap and phased evolution plan.

## What works now
- Arbitrary metric ingestion (`metric_name`) via `POST /observations`
- Repeated graph fetch via `GET /graph/series`
- Indicator overlays (`sma`, `ema`) via `GET /indicators/{indicator_name}`
- Pairwise + Top-N correlation endpoints
- Email outbox queue + SMTP processing endpoint
- IBKR adapter contract endpoints (`/orders/paper`, `/orders/live`)
- Dashboard served by backend at `/`

## Current Endpoint Map
- `GET /` dashboard
- `GET /docs` swagger docs
- `POST /entities`, `GET /entities`
- `POST /observations`
- `GET /graph/series?entity_id=&metric_name=&limit=`
- `GET /indicators/{sma|ema}?entity_id=&metric_name=&window=&limit=`
- `POST /predictions`
- `GET /leaderboard`
- `GET /correlations/pair?entity_a_id=&entity_b_id=&lookback_points=&lag_points=`
- `GET /relationships/top?entity_id=&top_n=&lookback_points=`
- `POST /notifications/outbox/process?limit=`
- `POST /orders/paper`, `POST /orders/live`
- `POST /demo/seed`
- `POST /demo/meal-trade-flow`

---

## Setup (Running)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## ⚖️ Repo Governance
- **Environment Isolation:** This project requires a dedicated virtual environment. 
- **Tool Preference:** Use the provided configuration files (`requirements.txt`, `environment.yml`, or `pyproject.toml`) as the primary source for setup.
- **Agent Permission:** You are a "Guest" in this environment. You may read everything, but you must request a 'Permission to Modify' (PTM) before changing any installed dependency or global variable.
- **Self-Documentation:** Whenever you make a major structural change to the logic, update `CHANGELOG.md` and ensure the README instructions still align with the current setup. If they conflict, flag it to the user immediately.

Open:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

Optional DB override:
```bash
export DATABASE_URL='sqlite:///./decision_wave_test.db'
```

---

## Meal → Trade Example Flow (your scenario)

### 1) Seed the demo meal/trade entities
```bash
curl -X POST 'http://127.0.0.1:8000/demo/meal-trade-flow'
```
Returns IDs for:
- `MEAL-CALORIES`
- `TRADES-AFTER-MEAL`

### 2) Query meal calories graph (time vs calories + source image URL)
```bash
curl 'http://127.0.0.1:8000/graph/series?entity_id=<meal_id>&metric_name=calories&limit=200'
```
Each point includes:
- `timestamp`
- `value`
- `metric_name`
- `source_url` (photo link)
- `extra_json` (parsed nutrition metadata)

### 3) Overlay indicator (example SMA)
```bash
curl 'http://127.0.0.1:8000/indicators/sma?entity_id=<meal_id>&metric_name=calories&window=3'
```

### 4) Correlate meal metric against trade activity
```bash
curl 'http://127.0.0.1:8000/correlations/pair?entity_a_id=<meal_id>&entity_b_id=<trade_id>&lookback_points=100&lag_points=1'
```
Use `lag_points` to test "trades after meal" offsets.

### 5) Top-N relationships from meal entity
```bash
curl 'http://127.0.0.1:8000/relationships/top?entity_id=<meal_id>&top_n=10&lookback_points=200'
```

---

## Frontend Usage
On `/` dashboard:
1. Click **Seed Meal↔Trade Demo** (or Market Demo)
2. Set `entityId`
3. Set `metricName` (`calories`, `trade_count`, `price`, etc.)
4. Click **Load Graph**
5. Click **Top-N**

Graph supports repeated refresh requests and indicator overlay.

---

## Notifications (Email)
Set SMTP env vars:
```bash
export SMTP_HOST='smtp.example.com'
export SMTP_PORT='587'
export SMTP_USERNAME='user'
export SMTP_PASSWORD='pass'
export SMTP_USE_TLS='true'
export EMAIL_FROM='decision-wave@example.com'
```

Process queued emails:
```bash
curl -X POST 'http://127.0.0.1:8000/notifications/outbox/process?limit=20'
```

---

## IBKR Adapter Hooks
Current implementation is a safe stub, but stable API contract is in place:
```bash
curl -X POST 'http://127.0.0.1:8000/orders/paper' \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"AAPL","side":"BUY","quantity":1}'
```

---

## Tests
```bash
cd backend
pytest -q
```

- API tests run if FastAPI/SQLAlchemy are available.
- Core tests validate scoring, correlation, and indicators.

---

## Next engineering target
- Plug image parser pipeline into `/observations` ingestion path (photo -> nutrition estimate -> point insertion).
- Replace IBKR stub with real gateway integration.
- Add user-defined indicator plugin files + registration endpoint.
