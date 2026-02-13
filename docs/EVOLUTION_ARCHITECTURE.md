# Decision Wave Engine — Feasibility-First Evolution (Abstract Core → Functional UX)

This document merges the vision into a practical engineering trajectory.

## 1) Fundamental Abstract Form (Core Invariant)

At the most abstract level, the system is:

- **Entity**: any source of signal (human, API, model, sensor, behavior).
- **Metric stream**: `(timestamp, value, metric_name, uncertainty, metadata)`.
- **State snapshot**: vector of selected metrics at time `t`.
- **Transition**: update from `state_t -> state_t+1` under actions/events.
- **Predictor**: estimates future state distribution.
- **Evaluator**: compares prediction vs observation and computes error.
- **Allocator**: ranks actions/entities under opportunity cost.

Everything else (UI, feeds, broker integration, notifications) is a tool around this invariant.

## 2) Feasibility: What is achievable now vs later

### Feasible now (already in MVP scope)
- Arbitrary metric ingestion with metadata
- Repeated graph fetch for selected entity+metric
- Basic indicators (SMA/EMA)
- Pair and Top-N correlations
- Leaderboard scoring loop
- Email outbox processing
- Broker adapter hooks (paper/live contract)

### Feasible near-term (next iterations)
- Multi-step opportunity sequence evaluation (`N`-step lookahead)
- Lag sweep for causal hints (correlation across lag window)
- Indicator plugin registration via config/module discovery
- Background workers for feed polling + alert pipelines

### Feasible later (higher complexity)
- Higher-order tensor transition models
- Monte Carlo branch simulation for long-history dependencies
- Bayesian model selection and dynamic confidence calibration
- Real causal inference (not just lag-correlation)

## 3) Layered evolution model (do not skip layers)

### Layer A: Observability-first
- Get clean ingestion and graphing correct.
- Ensure all events are timestamped with uncertainty metadata.

### Layer B: Predictive reliability
- Add forecast envelopes and strict error tracking (MSE, calibration).
- Trigger OOB alerts when realized values violate predicted bounds.

### Layer C: Allocation engine
- Rank opportunities with configurable objective functions.
- Track opportunity cost relative to best alternative actions.

### Layer D: Sequential intelligence
- Add N-step scenario propagation.
- Introduce explore/exploit policy and confidence-aware branching.

### Layer E: Personal decision OS
- Learn user-specific performance context.
- Causal memory + resurfacing of high-impact historical patterns.

## 4) Minimal canonical data contract

Use this as the core event contract:

```json
{
  "entity_id": 123,
  "timestamp": "2026-02-13T12:30:00Z",
  "metric_name": "calories",
  "value": 740.0,
  "margin_of_error": 35.0,
  "source_url": "https://.../meal.jpg",
  "extra_json": {
    "protein_g": 42,
    "fat_g": 31,
    "parser_confidence": 0.81
  }
}
```

This same shape supports stocks, meals, game events, decisions, and behaviors.

## 5) Computational strategy (when to use what)

- **Matrix / vector ops**: first-order updates, low-latency scoring, streaming indicators.
- **Tensor / high-order transitions**: when interactions across many entities/history matter.
- **Monte Carlo**: non-linear branching decisions, uncertainty-heavy multi-step planning.

Rule: start with matrix-friendly approximations; add complexity only where prediction error justifies it.

## 6) Product philosophy encoded as engineering constraints

- Keep the core engine UI-agnostic.
- No signal source is privileged (human included).
- Every contributor receives ongoing reliability scoring.
- User override is always allowed; system warns rather than hard-blocking.
- Favor transparent metrics over opaque model complexity until accuracy gains are proven.

## 7) Codex-ready build direction (next implementation set)

1. Add `transition_engine.py` for state snapshots + step propagation.
2. Add `allocation_engine.py` for opportunity cost over action sets.
3. Add lag-sweep endpoint for correlation heatmaps.
4. Add background scheduler for feed + notification jobs.
5. Add plugin registry for custom indicators and scoring functions.

