from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from statistics import fmean

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import EntityModel, ObservationModel, get_session
from ..schemas import MediaSyncRequest

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_db():
    with get_session() as session:
        yield session


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 2:
        return 0.0
    xs = xs[-n:]
    ys = ys[-n:]
    mx = fmean(xs)
    my = fmean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return cov / (sx * sy)


@router.get("/lag_sweep")
def lag_sweep(
    entity_a_id: int,
    entity_b_id: int,
    metric_a: str = "value",
    metric_b: str = "value",
    max_lag_days: int = Query(default=30, ge=0, le=365),
    db: Session = Depends(_get_db),
) -> dict:
    obs_a = db.scalars(
        select(ObservationModel)
        .where(ObservationModel.entity_id == entity_a_id)
        .where(ObservationModel.metric_name == metric_a)
        .order_by(ObservationModel.timestamp.asc())
    ).all()
    obs_b = db.scalars(
        select(ObservationModel)
        .where(ObservationModel.entity_id == entity_b_id)
        .where(ObservationModel.metric_name == metric_b)
        .order_by(ObservationModel.timestamp.asc())
    ).all()
    if not obs_a or not obs_b:
        return {"error": "No data"}

    b_by_day: dict[str, list[float]] = defaultdict(list)
    for x in obs_b:
        b_by_day[x.timestamp.date().isoformat()].append(x.value)

    results: list[dict] = []
    for lag in range(max_lag_days + 1):
        xs: list[float] = []
        ys: list[float] = []
        for a in obs_a:
            shifted_day = (a.timestamp + timedelta(days=lag)).date().isoformat()
            vals = b_by_day.get(shifted_day)
            if vals:
                xs.append(a.value)
                ys.append(sum(vals) / len(vals))
        if len(xs) < 3:
            continue
        corr = _pearson(xs, ys)
        results.append({"lag_days": lag, "correlation": corr, "samples": len(xs)})

    if not results:
        return {"sweep": [], "best_lag": None, "best_corr": 0.0}
    best = max(results, key=lambda x: abs(x["correlation"]))
    return {"sweep": results, "best_lag": best["lag_days"], "best_corr": best["correlation"]}


@router.get("/correlations/matrix")
def correlation_matrix(
    entity_ids: str = Query(..., description="Comma-separated entity IDs"),
    metric_name: str = "value",
    db: Session = Depends(_get_db),
) -> dict:
    ids = [int(x.strip()) for x in entity_ids.split(",") if x.strip().isdigit()]
    values_by_entity: dict[int, dict[str, float]] = {}
    for eid in ids:
        rows = db.scalars(
            select(ObservationModel)
            .where(ObservationModel.entity_id == eid)
            .where(ObservationModel.metric_name == metric_name)
            .order_by(ObservationModel.timestamp.asc())
        ).all()
        daymap: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            daymap[r.timestamp.date().isoformat()].append(r.value)
        values_by_entity[eid] = {k: sum(v) / len(v) for k, v in daymap.items()}

    matrix: dict[str, dict[str, float]] = {}
    for a in ids:
        matrix[str(a)] = {}
        for b in ids:
            if a == b:
                matrix[str(a)][str(b)] = 1.0
                continue
            days = sorted(set(values_by_entity.get(a, {}).keys()) & set(values_by_entity.get(b, {}).keys()))
            xs = [values_by_entity[a][d] for d in days]
            ys = [values_by_entity[b][d] for d in days]
            matrix[str(a)][str(b)] = round(_pearson(xs, ys), 3) if len(days) >= 3 else 0.0

    return {"matrix": matrix, "heatmap_ready": True}


@router.get("/wave/{entity_id}")
def get_wave(entity_id: int, metric_name: str = "value", db: Session = Depends(_get_db)) -> dict:
    rows = db.scalars(
        select(ObservationModel)
        .where(ObservationModel.entity_id == entity_id)
        .where(ObservationModel.metric_name == metric_name)
        .order_by(ObservationModel.timestamp.asc())
        .limit(2000)
    ).all()
    if not rows:
        return {"series": []}

    values = [x.value for x in rows]

    def rolling_mean(arr: list[float], window: int) -> list[float | None]:
        out: list[float | None] = []
        for i in range(len(arr)):
            if i + 1 < window:
                out.append(None)
            else:
                c = arr[i + 1 - window : i + 1]
                out.append(sum(c) / len(c))
        return out

    sma20 = rolling_mean(values, 20)
    series = []
    for i, r in enumerate(rows):
        series.append(
            {
                "timestamp": r.timestamp.isoformat(),
                "value": r.value,
                "sma_20": sma20[i],
                "source_url": r.source_url,
                "extra_json": r.extra_json or {},
            }
        )
    return {"series": series}


@router.post("/media/sync")
async def sync_media(payload: MediaSyncRequest, db: Session = Depends(_get_db)) -> dict:
    entities = []
    for item in payload.entities:
        e = db.scalar(select(EntityModel).where(EntityModel.name == item))
        if e:
            entities.append({"id": e.id, "name": e.name})

    return {
        "status": "ready_for_mp3_overlay",
        "media_url": payload.media_url,
        "current_audio_sec": payload.current_audio_sec,
        "entities": entities,
        "example": "Wave overlays can sync to audio timeline at UI layer.",
    }
