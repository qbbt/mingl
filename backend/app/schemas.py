from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    name: str
    entity_type: str = "generic"
    contributor_type: str = "manual"
    weight: float = 1.0


class EntityOut(EntityCreate):
    id: int


class ObservationCreate(BaseModel):
    entity_id: int
    timestamp: datetime
    value: float
    metric_name: str = "value"
    margin_of_error: float = 0.0
    event_type: str = "observation"
    source_url: str = ""
    extra_json: dict[str, Any] = Field(default_factory=dict)


class PredictionCreate(BaseModel):
    entity_id: int
    timestamp: datetime
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float = Field(ge=0.0, le=1.0)


class AnnotationCreate(BaseModel):
    entity_id: int
    observed_time: datetime
    estimated_actual_time: datetime
    timestamp_margin_of_error: float
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class RankingConfig(BaseModel):
    mode: str = "auto"
    ev_weight: float = 1.0
    confidence_weight: float = 1.0
    volatility_penalty_weight: float = 1.0
    decay_weight: float = 1.0
    attention_cost_weight: float = 1.0
    execution_reliability_weight: float = 1.0


class LeaderboardRow(BaseModel):
    entity_id: int
    entity_name: str
    score: float
    components: dict[str, Any]


class WaveData(BaseModel):
    entity_id: int
    entity_name: str
    observations: list[dict[str, Any]]
    predictions: list[dict[str, Any]]


class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    order_type: str = "MKT"
    notes: str = ""


class TopRelationship(BaseModel):
    source_entity_id: int
    source_entity_name: str
    target_entity_id: int
    target_entity_name: str
    correlation: float
    points_used: int


class GraphSeriesPoint(BaseModel):
    timestamp: str
    value: float
    metric_name: str
    source_url: str
    extra_json: dict[str, Any]


class CorrelationPairResult(BaseModel):
    entity_a_id: int
    entity_b_id: int
    lag_points: int
    points_used: int
    correlation: float


class IndicatorResult(BaseModel):
    indicator: str
    entity_id: int
    metric_name: str
    window: int
    values: list[Optional[float]]
    timestamps: list[str]


class MediaSyncRequest(BaseModel):
    media_url: str
    current_audio_sec: float
    entities: list[str] = []


class DecayRequest(BaseModel):
    values: list[float]
    decay_type: str = "exponential"
    params: dict[str, Any] = Field(default_factory=dict)
