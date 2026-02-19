from fastapi import APIRouter, Query, HTTPException
from app.services.market_service import market_service
from app.schemas import GraphSeriesPoint, ObservationCreate, PredictionCreate
from app.repositories.data_repository import data_repo

router = APIRouter(prefix="/market", tags=["Market Data"])

@router.get("/series", response_model=list[GraphSeriesPoint])
async def get_series(
    entity_id: int,
    metric_name: str = "price",
    limit: int = Query(default=500, le=5000)
):
    """Layered data retrieval (User Overrides > Market Data)."""
    rows = await market_service.get_layered_series(entity_id, metric_name, limit)
    return [
        GraphSeriesPoint(
            timestamp=r["timestamp"],
            value=r["value"],
            metric_name=r["metric_name"],
            source_url="",
            extra_json={}
        ) for r in rows
    ]

@router.post("/observations")
async def create_observation(payload: ObservationCreate):
    """High-scale data ingestion."""
    is_override = payload.event_type == "override"
    await market_service.push_observation(
        payload.entity_id, 
        payload.metric_name, 
        payload.value, 
        is_override,
        payload.timestamp
    )
    return {"status": "accepted"}

@router.put("/observations")
async def update_observation(payload: ObservationCreate):
    """Update an existing observation (Priority >= 1.0 logic)."""
    await data_repo.update_observation(
        payload.entity_id,
        payload.metric_name,
        payload.timestamp,
        payload.value
    )
    return {"status": "updated"}

@router.get("/metrics/{entity_id}", response_model=list[str])
async def get_metrics(entity_id: int):
    """Fetch unique metric names for an entity."""
    return await market_service.get_available_metrics(entity_id)

@router.get("/predictions/{entity_id}")
async def get_predictions(entity_id: int):
    """Fetch future predictions for an entity from SQLite."""
    preds = await data_repo.get_predictions(entity_id)
    return preds

@router.post("/predictions")
async def create_prediction(payload: PredictionCreate):
    """Manual prediction ingestion into SQLite."""
    from app.repositories.data_repository import data_repo
    await data_repo.add_prediction(payload)
    return {"status": "prediction_recorded"}

@router.delete("/overrides/{entity_id}")
async def delete_overrides(entity_id: int, metric_name: str = "price"):
    """Reset manual overrides for an entity (Soft-delete in DuckDB)."""
    # For now, we'll just implement a hard delete in DuckDB for overrides (priority >= 1.0)
    from app.repositories.data_repository import data_repo
    sql = "DELETE FROM observations WHERE entity_id = ? AND metric_name = ? AND priority >= 1.0"
    await data_repo._execute(sql, [entity_id, metric_name])
    return {"status": "overrides_cleared"}
