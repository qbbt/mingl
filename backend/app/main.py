from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .correlations import pearson
from .db import (
    AnnotationModel,
    ContributorMetricModel,
    CorrelationModel,
    EntityModel,
    LeaderboardSnapshotModel,
    ObservationModel,
    PredictionModel,
    get_session,
    init_db,
)
from .execution import IbkrStubAdapter
from .indicators import INDICATOR_REGISTRY
from .leaderboard import DEFAULT_PROFILE, RankingProfile, compute_score
from .notifications import process_email_outbox, queue_email_notification
from .schemas import (
    AnnotationCreate,
    CorrelationPairResult,
    EntityCreate,
    EntityOut,
    GraphSeriesPoint,
    IndicatorResult,
    LeaderboardRow,
    ObservationCreate,
    OrderRequest,
    PredictionCreate,
    RankingConfig,
    TopRelationship,
    WaveData,
)

app = FastAPI(title="Decision Wave Engine", version="0.3.0")

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runtime_profile = DEFAULT_PROFILE
broker = IbkrStubAdapter()

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/")
def index() -> FileResponse:
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(FRONTEND_INDEX)


@app.post("/entities", response_model=EntityOut)
def create_entity(payload: EntityCreate) -> EntityOut:
    with get_session() as session:
        existing = session.scalar(select(EntityModel).where(EntityModel.name == payload.name))
        if existing:
            raise HTTPException(status_code=409, detail="Entity already exists")
        entity = EntityModel(**payload.model_dump())
        session.add(entity)
        session.flush()
        session.add(ContributorMetricModel(entity_id=entity.id))
        return EntityOut(id=entity.id, **payload.model_dump())


@app.get("/entities", response_model=list[EntityOut])
def list_entities() -> list[EntityOut]:
    with get_session() as session:
        entities = session.scalars(select(EntityModel).order_by(EntityModel.id.asc())).all()
        return [
            EntityOut(
                id=e.id,
                name=e.name,
                entity_type=e.entity_type,
                contributor_type=e.contributor_type,
                weight=e.weight,
            )
            for e in entities
        ]


@app.post("/observations")
def create_observation(payload: ObservationCreate) -> dict:
    with get_session() as session:
        entity = session.get(EntityModel, payload.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        session.add(ObservationModel(**payload.model_dump()))
        return {"status": "ok"}


@app.get("/graph/series", response_model=list[GraphSeriesPoint])
def graph_series(
    entity_id: int,
    metric_name: str = "value",
    limit: int = Query(default=500, le=5000),
) -> list[GraphSeriesPoint]:
    with get_session() as session:
        rows = session.scalars(
            select(ObservationModel)
            .where(ObservationModel.entity_id == entity_id)
            .where(ObservationModel.metric_name == metric_name)
            .order_by(ObservationModel.timestamp.asc())
            .limit(limit)
        ).all()
        return [
            GraphSeriesPoint(
                timestamp=r.timestamp.isoformat(),
                value=r.value,
                metric_name=r.metric_name,
                source_url=r.source_url,
                extra_json=r.extra_json or {},
            )
            for r in rows
        ]


@app.get("/indicators/{indicator_name}", response_model=IndicatorResult)
def indicator_series(
    indicator_name: str,
    entity_id: int,
    metric_name: str = "value",
    window: int = Query(default=14, ge=1, le=500),
    limit: int = Query(default=500, le=5000),
) -> IndicatorResult:
    if indicator_name not in INDICATOR_REGISTRY:
        raise HTTPException(status_code=404, detail="Indicator not found")

    with get_session() as session:
        rows = session.scalars(
            select(ObservationModel)
            .where(ObservationModel.entity_id == entity_id)
            .where(ObservationModel.metric_name == metric_name)
            .order_by(ObservationModel.timestamp.asc())
            .limit(limit)
        ).all()
        values = [r.value for r in rows]
        timestamps = [r.timestamp.isoformat() for r in rows]

    func = INDICATOR_REGISTRY[indicator_name]
    try:
        computed = func(values, window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IndicatorResult(
        indicator=indicator_name,
        entity_id=entity_id,
        metric_name=metric_name,
        window=window,
        values=computed,
        timestamps=timestamps,
    )


@app.post("/predictions")
def create_prediction(payload: PredictionCreate) -> dict:
    with get_session() as session:
        entity = session.get(EntityModel, payload.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        pred = PredictionModel(**payload.model_dump())
        session.add(pred)

        if not (payload.lower_bound <= payload.predicted_value <= payload.upper_bound):
            queue_email_notification(
                session,
                recipient="local-user@example.com",
                subject=f"Prediction bounds warning for {entity.name}",
                body="Predicted value is outside provided bounds.",
            )
        return {"status": "ok"}


@app.post("/annotations")
def create_annotation(payload: AnnotationCreate) -> dict:
    with get_session() as session:
        entity = session.get(EntityModel, payload.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        session.add(AnnotationModel(**payload.model_dump()))
        return {"status": "ok"}


@app.get("/wave/{entity_id}", response_model=WaveData)
def wave(entity_id: int) -> WaveData:
    with get_session() as session:
        entity = session.get(EntityModel, entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        observations = session.scalars(
            select(ObservationModel)
            .where(ObservationModel.entity_id == entity_id)
            .order_by(ObservationModel.timestamp.asc())
        ).all()
        predictions = session.scalars(
            select(PredictionModel)
            .where(PredictionModel.entity_id == entity_id)
            .order_by(PredictionModel.timestamp.asc())
        ).all()
        return WaveData(
            entity_id=entity.id,
            entity_name=entity.name,
            observations=[
                {
                    "timestamp": o.timestamp.isoformat(),
                    "value": o.value,
                    "metric_name": o.metric_name,
                    "margin_of_error": o.margin_of_error,
                    "event_type": o.event_type,
                    "source_url": o.source_url,
                    "extra_json": o.extra_json or {},
                }
                for o in observations
            ],
            predictions=[
                {
                    "timestamp": p.timestamp.isoformat(),
                    "predicted_value": p.predicted_value,
                    "lower_bound": p.lower_bound,
                    "upper_bound": p.upper_bound,
                    "confidence": p.confidence,
                }
                for p in predictions
            ],
        )


@app.post("/ranking/profile")
def set_ranking_profile(payload: RankingConfig) -> dict:
    global runtime_profile
    runtime_profile = RankingProfile(**payload.model_dump())
    return {"status": "ok", "mode": runtime_profile.mode}


@app.get("/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(limit: int = Query(default=20, le=500)) -> list[LeaderboardRow]:
    with get_session() as session:
        entities = session.scalars(select(EntityModel)).all()
        rows: list[LeaderboardRow] = []

        for entity in entities:
            latest_pred = session.scalar(
                select(PredictionModel)
                .where(PredictionModel.entity_id == entity.id)
                .order_by(PredictionModel.timestamp.desc())
                .limit(1)
            )
            latest_obs = session.scalar(
                select(ObservationModel)
                .where(ObservationModel.entity_id == entity.id)
                .order_by(ObservationModel.timestamp.desc())
                .limit(1)
            )
            metric = session.scalar(select(ContributorMetricModel).where(ContributorMetricModel.entity_id == entity.id))

            expected_value = (latest_pred.predicted_value - latest_obs.value) if latest_pred and latest_obs else 0.0
            confidence = latest_pred.confidence if latest_pred else 0.0
            volatility_penalty = abs(latest_pred.upper_bound - latest_pred.lower_bound) if latest_pred else 0.0
            decay = 0.1
            attention_cost = 0.1
            execution_reliability = metric.directional_accuracy if metric else 0.5

            score, components = compute_score(
                expected_value=expected_value,
                confidence=confidence,
                volatility_penalty=volatility_penalty,
                decay=decay,
                attention_cost=attention_cost,
                execution_reliability=execution_reliability,
                profile=runtime_profile,
            )

            rows.append(
                LeaderboardRow(entity_id=entity.id, entity_name=entity.name, score=score, components=components)
            )
            session.add(
                LeaderboardSnapshotModel(
                    entity_id=entity.id,
                    score=score,
                    mode=runtime_profile.mode,
                    components=components,
                )
            )

        rows.sort(key=lambda row: row.score, reverse=True)
        return rows[:limit]


def _pairwise_correlation_values(
    session,
    source_entity_id: int,
    target_entity_id: int,
    lookback_points: int,
    lag_points: int = 0,
) -> tuple[float, int]:
    source_obs = session.scalars(
        select(ObservationModel)
        .where(ObservationModel.entity_id == source_entity_id)
        .order_by(ObservationModel.timestamp.desc())
        .limit(lookback_points + abs(lag_points))
    ).all()
    target_obs = session.scalars(
        select(ObservationModel)
        .where(ObservationModel.entity_id == target_entity_id)
        .order_by(ObservationModel.timestamp.desc())
        .limit(lookback_points + abs(lag_points))
    ).all()

    source_values = [x.value for x in reversed(source_obs)]
    target_values = [x.value for x in reversed(target_obs)]

    if lag_points > 0:
        source_values = source_values[:-lag_points] if len(source_values) > lag_points else []
        target_values = target_values[lag_points:]
    elif lag_points < 0:
        shift = abs(lag_points)
        source_values = source_values[shift:]
        target_values = target_values[:-shift] if len(target_values) > shift else []

    n = min(len(source_values), len(target_values), lookback_points)
    if n < 2:
        return 0.0, n
    return pearson(source_values[-n:], target_values[-n:]), n


@app.get("/correlations/pair", response_model=CorrelationPairResult)
def correlation_pair(entity_a_id: int, entity_b_id: int, lookback_points: int = 120, lag_points: int = 0) -> CorrelationPairResult:
    with get_session() as session:
        corr, n = _pairwise_correlation_values(session, entity_a_id, entity_b_id, lookback_points, lag_points)
        session.add(
            CorrelationModel(
                entity_a_id=entity_a_id,
                entity_b_id=entity_b_id,
                correlation_value=corr,
                confidence=min(1.0, n / max(lookback_points, 1)),
                window_seconds=0,
            )
        )
        return CorrelationPairResult(
            entity_a_id=entity_a_id,
            entity_b_id=entity_b_id,
            lag_points=lag_points,
            points_used=n,
            correlation=corr,
        )


@app.get("/relationships/top", response_model=list[TopRelationship])
def top_relationships(entity_id: int, top_n: int = 10, lookback_points: int = 120) -> list[TopRelationship]:
    with get_session() as session:
        source = session.get(EntityModel, entity_id)
        if not source:
            raise HTTPException(status_code=404, detail="Entity not found")

        others = session.scalars(select(EntityModel).where(EntityModel.id != entity_id)).all()
        rows: list[TopRelationship] = []
        for target in others:
            corr, points_used = _pairwise_correlation_values(session, source.id, target.id, lookback_points)
            rows.append(
                TopRelationship(
                    source_entity_id=source.id,
                    source_entity_name=source.name,
                    target_entity_id=target.id,
                    target_entity_name=target.name,
                    correlation=corr,
                    points_used=points_used,
                )
            )
            session.add(
                CorrelationModel(
                    entity_a_id=source.id,
                    entity_b_id=target.id,
                    correlation_value=corr,
                    confidence=min(1.0, points_used / max(lookback_points, 1)),
                    window_seconds=0,
                )
            )

        rows.sort(key=lambda r: abs(r.correlation), reverse=True)
        return rows[:top_n]


@app.post("/notifications/outbox/process")
def process_notifications(limit: int = 20) -> dict:
    with get_session() as session:
        return process_email_outbox(session, limit=limit)


@app.post("/orders/paper")
def paper_order(order: OrderRequest) -> dict:
    response = broker.paper_execute(order.model_dump())
    return response


@app.post("/orders/live")
def live_order(order: OrderRequest) -> dict:
    response = broker.live_execute(order.model_dump())
    return response


@app.post("/demo/seed")
def seed_demo_data() -> dict:
    with get_session() as session:
        names = ["BTC-USD", "ETH-USD", "SOL-USD"]
        ids: list[int] = []
        for idx, name in enumerate(names):
            entity = session.scalar(select(EntityModel).where(EntityModel.name == name))
            if not entity:
                entity = EntityModel(name=name, entity_type="crypto", contributor_type="api", weight=1.0)
                session.add(entity)
                session.flush()
                session.add(ContributorMetricModel(entity_id=entity.id, directional_accuracy=0.55 + idx * 0.1))
            ids.append(entity.id)

            now = datetime.utcnow()
            for i in range(60):
                t = now - timedelta(minutes=59 - i)
                base = 50000 + idx * 2000
                value = base + ((i - 30) * (20 + idx * 5))
                session.add(
                    ObservationModel(
                        entity_id=entity.id,
                        timestamp=t,
                        value=value,
                        metric_name="price",
                        margin_of_error=10,
                        event_type="tick",
                    )
                )
            session.add(
                PredictionModel(
                    entity_id=entity.id,
                    timestamp=now,
                    predicted_value=base + 200,
                    lower_bound=base - 150,
                    upper_bound=base + 350,
                    confidence=0.72,
                )
            )

        return {"status": "ok", "seeded_entities": ids}


@app.post("/demo/meal-trade-flow")
def seed_meal_trade_flow() -> dict:
    with get_session() as session:
        meal = session.scalar(select(EntityModel).where(EntityModel.name == "MEAL-CALORIES"))
        if not meal:
            meal = EntityModel(name="MEAL-CALORIES", entity_type="nutrition", contributor_type="manual", weight=1.0)
            session.add(meal)
            session.flush()
            session.add(ContributorMetricModel(entity_id=meal.id, directional_accuracy=0.7))

        trade = session.scalar(select(EntityModel).where(EntityModel.name == "TRADES-AFTER-MEAL"))
        if not trade:
            trade = EntityModel(name="TRADES-AFTER-MEAL", entity_type="behavior", contributor_type="system", weight=1.0)
            session.add(trade)
            session.flush()
            session.add(ContributorMetricModel(entity_id=trade.id, directional_accuracy=0.6))

        now = datetime.utcnow()
        meals = [450, 700, 600, 900, 400, 800]
        trades_after = [1, 3, 2, 4, 1, 4]
        for i, (cal, tr) in enumerate(zip(meals, trades_after)):
            t = now - timedelta(hours=(len(meals) - i) * 4)
            session.add(
                ObservationModel(
                    entity_id=meal.id,
                    timestamp=t,
                    value=float(cal),
                    metric_name="calories",
                    event_type="meal",
                    source_url=f"https://example.local/meal/{i+1}.jpg",
                    extra_json={"parser": "mock", "protein_g": 20 + i, "fat_g": 10 + i},
                )
            )
            session.add(
                ObservationModel(
                    entity_id=trade.id,
                    timestamp=t + timedelta(minutes=45),
                    value=float(tr),
                    metric_name="trade_count",
                    event_type="trade_activity",
                    extra_json={"window_minutes": 90},
                )
            )

        return {"status": "ok", "meal_entity_id": meal.id, "trade_entity_id": trade.id}


@app.websocket("/ws/data")
async def ws_data(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        with get_session() as session:
            total_entities = session.query(EntityModel).count()
            total_observations = session.query(ObservationModel).count()
        await websocket.send_json(
            {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "entities": total_entities,
                "observations": total_observations,
            }
        )
        await websocket.receive_text()


@app.get("/summary")
def summary() -> dict:
    with get_session() as session:
        out = defaultdict(int)
        out["entities"] = session.query(EntityModel).count()
        out["observations"] = session.query(ObservationModel).count()
        out["predictions"] = session.query(PredictionModel).count()
        out["annotations"] = session.query(AnnotationModel).count()
        out["correlations"] = session.query(CorrelationModel).count()
        return dict(out)
