import duckdb
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

STORAGE_DIR = "data_store"
DUCKDB_PATH = os.path.join(STORAGE_DIR, "warehouse.duckdb")

class DataRepository:
    """
    Tiered Storage Repository for DuckDB.
    Job: Data retrieval and raw ingestion (Tier 2/3).
    """
    def __init__(self):
        # We use a ThreadPoolExecutor for blocking DuckDB calls
        self.executor = ThreadPoolExecutor(max_workers=4)
        # We connect once, but must ensure thread safety if used across threads
        self.conn = duckdb.connect(DUCKDB_PATH)

    async def _query(self, sql: str, params: List[Any] = None) -> List[Any]:
        """Runs a blocking DuckDB query in a background thread."""
        loop = asyncio.get_event_loop()
        def _exec():
            return self.conn.execute(sql, params or []).fetchall()
        return await loop.run_in_executor(self.executor, _exec)

    async def _execute(self, sql: str, params: List[Any] = None):
        """Runs a blocking DuckDB execution in a background thread."""
        loop = asyncio.get_event_loop()
        def _exec():
            self.conn.execute(sql, params or [])
        await loop.run_in_executor(self.executor, _exec)

    async def add_observation(self, entity_id: int, metric_name: str, value: float, priority: float = 0.5, timestamp: Optional[datetime] = None):
        ts = timestamp or datetime.utcnow()
        sql = "INSERT INTO observations VALUES (?, ?, ?, ?, ?)"
        await self._execute(sql, [entity_id, ts, metric_name, value, priority])

    async def _init_observations(self):
        """Initializes the observations table for market and manual data."""
        sql = """
        CREATE TABLE IF NOT EXISTS observations (
            entity_id INTEGER,
            timestamp TIMESTAMP,
            metric_name TEXT,
            value REAL,
            priority REAL
        )
        """
        await self._execute(sql)

    async def _init_ledger(self):
        """Initializes the alignment ledger table in DuckDB."""
        # Ensure observations is also ready
        await self._init_observations()
        sql = """
        CREATE TABLE IF NOT EXISTS alignment_ledger (
            timestamp TIMESTAMP,
            commit_id TEXT,
            agent_score REAL,
            user_score REAL,
            filtered_user_score REAL,
            pearson_r REAL,
            r_squared REAL,
            knowledge_gain REAL,
            commit_risk REAL,
            aleatoric_uncertainty REAL,
            technical_debt_score INTEGER,
            alignment_objective REAL,
            notes TEXT,
            PRIMARY KEY (timestamp, commit_id)
        )
        """
        await self._execute(sql)

    async def add_ledger_entry(self, entry: Dict[str, Any]):
        sql = """
        INSERT INTO alignment_ledger VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """
        params = [
            entry.get("timestamp", datetime.utcnow()),
            entry.get("commit_id", "manual"),
            entry.get("agent_score", 0.0),
            entry.get("user_score", 0.0),
            entry.get("filtered_user_score", 0.0),
            entry.get("pearson_r", 0.0),
            entry.get("r_squared", 0.0),
            entry.get("knowledge_gain", 0.0),
            entry.get("commit_risk", 0.0),
            entry.get("aleatoric_uncertainty", 0.0),
            entry.get("technical_debt_score", 0),
            entry.get("alignment_objective", 0.0),
            entry.get("notes", "")
        ]
        await self._execute(sql, params)

    async def get_ledger_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM alignment_ledger ORDER BY timestamp DESC LIMIT ?"
        rows = await self._query(sql, [limit])
        return [
            {
                "timestamp": r[0].isoformat(),
                "commit_id": r[1],
                "agent_score": r[2],
                "user_score": r[3],
                "filtered_user_score": r[4],
                "pearson_r": r[5],
                "r_squared": r[6],
                "knowledge_gain": r[7],
                "commit_risk": r[8],
                "aleatoric_uncertainty": r[9],
                "technical_debt_score": r[10],
                "alignment_objective": r[11],
                "notes": r[12]
            } for r in rows
        ]

    async def get_layered_data(self, entity_id: int, metric_name: str, limit: int = 500) -> List[Dict]:
        query = """
            SELECT 
                COALESCE(u.timestamp, m.timestamp) as ts,
                COALESCE(u.value, m.value) as val,
                COALESCE(u.metric_name, m.metric_name) as m_name
            FROM (SELECT * FROM observations WHERE entity_id = ? AND metric_name = ? AND priority < 1.0) m
            FULL OUTER JOIN (SELECT * FROM observations WHERE entity_id = ? AND metric_name = ? AND priority >= 1.0) u
            ON m.timestamp = u.timestamp
            ORDER BY ts DESC
            LIMIT ?
        """
        rows = await self._query(query, [entity_id, metric_name, entity_id, metric_name, limit])
        return [
            {"timestamp": r[0].isoformat(), "value": r[1], "metric_name": r[2]}
            for r in reversed(rows)
        ]

    async def get_available_metrics(self, entity_id: int) -> List[str]:
        """Returns unique metric names for an entity."""
        query = "SELECT DISTINCT metric_name FROM observations WHERE entity_id = ?"
        rows = await self._query(query, [entity_id])
        return [r[0] for r in rows]

    async def get_observation_count(self) -> int:
        sql = "SELECT COUNT(*) FROM observations"
        rows = await self._query(sql)
        return rows[0][0] if rows else 0

    async def check_health(self) -> bool:
        try:
            await self._query("SELECT 1")
            return True
        except:
            return False

    async def get_predictions(self, entity_id: int) -> List[Dict]:
        """Fetch predictions from SQLite warehouse via standard session pattern."""
        from app.db import get_session, PredictionModel
        from sqlalchemy import select
        with get_session() as session:
            preds = session.scalars(
                select(PredictionModel)
                .where(PredictionModel.entity_id == entity_id)
                .order_by(PredictionModel.timestamp.asc())
            ).all()
            return [
                {
                    "id": p.id,
                    "timestamp": p.timestamp.isoformat(),
                    "value": p.predicted_value,
                    "lower_bound": p.lower_bound,
                    "upper_bound": p.upper_bound,
                    "confidence": p.confidence
                } for p in preds
            ]

    async def add_prediction(self, payload: Any):
        """Persist manual prediction to SQLite."""
        from app.db import get_session, PredictionModel
        with get_session() as session:
            new_pred = PredictionModel(
                entity_id=payload.entity_id,
                timestamp=payload.timestamp,
                predicted_value=payload.predicted_value,
                lower_bound=payload.lower_bound,
                upper_bound=payload.upper_bound,
                confidence=payload.confidence
            )
            session.add(new_pred)
            session.commit()

    async def update_observation(self, entity_id: int, metric_name: str, timestamp: str, new_value: float):
        """Update a specific observation's value."""
        sql = """
        UPDATE observations 
        SET value = ? 
        WHERE entity_id = ? AND metric_name = ? AND timestamp = ?
        """
        await self._execute(sql, [new_value, entity_id, metric_name, timestamp])

# Singleton instance
data_repo = DataRepository()
