from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import os
from typing import Generator

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./decision_wave.db")


class Base(DeclarativeBase):
    pass


class EntityModel(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="generic")
    contributor_type: Mapped[str] = mapped_column(String(64), default="manual")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    observations: Mapped[list[ObservationModel]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    predictions: Mapped[list[PredictionModel]] = relationship(back_populates="entity", cascade="all, delete-orphan")


class ObservationModel(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    value: Mapped[float] = mapped_column(Float)
    metric_name: Mapped[str] = mapped_column(String(64), default="value")
    margin_of_error: Mapped[float] = mapped_column(Float, default=0.0)
    event_type: Mapped[str] = mapped_column(String(64), default="observation")
    source_url: Mapped[str] = mapped_column(String(512), default="")
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)

    entity: Mapped[EntityModel] = relationship(back_populates="observations")


class PredictionModel(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    predicted_value: Mapped[float] = mapped_column(Float)
    lower_bound: Mapped[float] = mapped_column(Float)
    upper_bound: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)

    entity: Mapped[EntityModel] = relationship(back_populates="predictions")


class AnnotationModel(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    observed_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    estimated_actual_time: Mapped[datetime] = mapped_column(DateTime)
    timestamp_margin_of_error: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text, default="")


class ContributorMetricModel(Base):
    __tablename__ = "contributor_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), unique=True)
    directional_accuracy: Mapped[float] = mapped_column(Float, default=0.5)
    calibration_error: Mapped[float] = mapped_column(Float, default=0.0)
    latency_impact: Mapped[float] = mapped_column(Float, default=0.0)
    regime_sensitivity: Mapped[float] = mapped_column(Float, default=0.0)
    override_performance_trend: Mapped[float] = mapped_column(Float, default=0.0)


class LeaderboardSnapshotModel(Base):
    __tablename__ = "leaderboard_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    mode: Mapped[str] = mapped_column(String(64), default="auto")
    components: Mapped[dict] = mapped_column(JSON)


class CorrelationModel(Base):
    __tablename__ = "correlations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_a_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    entity_b_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), index=True)
    correlation_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    window_seconds: Mapped[int] = mapped_column(Integer, default=3600)


class NotificationOutboxModel(Base):
    __tablename__ = "notification_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    recipient: Mapped[str] = mapped_column(String(256))
    subject: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
