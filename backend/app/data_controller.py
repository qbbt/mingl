import os
import time
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Constants for Tiered Storage
STORAGE_DIR = "data_store"
DUCKDB_PATH = os.path.join(STORAGE_DIR, "warehouse.duckdb")
ARCHIVE_DIR = os.path.join(STORAGE_DIR, "archive")
HARD_CAP_GB = 20
DECAY_RATE = 0.99  # 1% decay per day for non-pinned data

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

class UnifiedDataController:
    """
    Tiered Storage Funnel:
    - Tier 1: In-Memory Ring Buffer (Real-time pulses)
    - Tier 2: DuckDB Warehouse (1m OHLC candles)
    - Tier 3: Parquet Archive (Daily OHLC compressed)
    """
    
    def __init__(self):
        # Tier 1: Entity ID -> deque of recent observations
        self.buffer: Dict[int, deque] = {}
        self.buffer_limit = 1000  # Max points per entity in memory
        
        # Tier 2: DuckDB Connection
        self.db = duckdb.connect(DUCKDB_PATH)
        self._init_warehouse()
        
        # Metadata
        self.pinned_entities = set() # Entities marked for permanent storage

    def _init_warehouse(self):
        """Initialize DuckDB tables for OHLC storage."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                entity_id INTEGER,
                timestamp TIMESTAMP,
                metric_name VARCHAR,
                value FLOAT,
                priority FLOAT DEFAULT 0.5
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_entity_ts ON observations (entity_id, timestamp)")

    def add_observation(self, entity_id: int, metric_name: str, value: float, priority: float = 0.5):
        """Adds observation to Tier 1 and persists to Tier 2 if needed."""
        ts = datetime.utcnow()
        
        # Tier 1: Buffer
        if entity_id not in self.buffer:
            self.buffer[entity_id] = deque(maxlen=self.buffer_limit)
        
        obs = {
            "entity_id": entity_id,
            "timestamp": ts,
            "metric_name": metric_name,
            "value": value,
            "priority": priority
        }
        self.buffer[entity_id].append(obs)
        
        # Tier 2: Warehouse (immediate append for safety in this MVP)
        self.db.execute(
            "INSERT INTO observations VALUES (?, ?, ?, ?, ?)",
            [entity_id, ts, metric_name, value, priority]
        )
        
        # Check storage constraints periodically
        self._enforce_constraints()

    def get_layered_series(self, entity_id: int, metric_name: str, limit: int = 500) -> List[Dict]:
        """
        Implements the 'Layered' architecture:
        Final_Value = IF(User_Override EXISTS, User_Override, Market_Data)
        Uses DuckDB to join Market data with User overrides on timestamp.
        """
        # In this implementation, 'priority >= 1.0' acts as a User Override (pinned)
        # We use a window-based join or simple coalesce if timestamps match exactly.
        # For misaligned data, we would use DuckDB's ASOF JOIN.
        
        query = """
            SELECT 
                COALESCE(u.timestamp, m.timestamp) as ts,
                COALESCE(u.value, m.value) as val,
                m.metric_name
            FROM (SELECT * FROM observations WHERE entity_id = ? AND metric_name = ? AND priority < 1.0) m
            FULL OUTER JOIN (SELECT * FROM observations WHERE entity_id = ? AND metric_name = ? AND priority >= 1.0) u
            ON m.timestamp = u.timestamp
            ORDER BY ts DESC
            LIMIT ?
        """
        res = self.db.execute(query, [entity_id, metric_name, entity_id, metric_name, limit]).fetchall()
        
        return [
            {"timestamp": r[0].isoformat(), "value": r[1], "metric_name": r[2]}
            for r in reversed(res)
        ]

    def add_user_override(self, entity_id: int, metric_name: str, value: float, ts: Optional[datetime] = None):
        """Adds a high-priority 'Pinned' observation that overrides market data."""
        if ts is None:
            ts = datetime.utcnow()
        self.add_observation(entity_id, metric_name, value, priority=1.0)

    def _enforce_constraints(self):
        """Implements entropy management and 20GB hard cap."""
        # 1. Entropy Decay (.99 daily decay)
        # In a real system, we'd run this as a background task.
        # Here we just apply it to non-pinned data older than 1 hour.
        self.db.execute("""
            UPDATE observations 
            SET priority = priority * 0.99 
            WHERE priority < 1.0 
            AND timestamp < (now() - INTERVAL 1 HOUR)
        """)
        
        # 2. Hard Cap Enforcement
        total_size_gb = self._get_storage_size()
        if total_size_gb > HARD_CAP_GB:
            # Purge lowest priority data
            self.db.execute("""
                DELETE FROM observations 
                WHERE priority < 1.0 
                AND timestamp < (SELECT timestamp FROM observations ORDER BY priority ASC LIMIT 1 OFFSET 1000)
            """)

    def _get_storage_size(self) -> float:
        """Returns total storage size in GB."""
        size: int = 0
        for root, dirs, files in os.walk(STORAGE_DIR):
            for f in files:
                try:
                    size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    continue
        return float(size) / (1024**3)

    def archive_to_parquet(self):
        """Exports older data to Tier 3 (Compressed Parquet)."""
        cutoff = datetime.utcnow() - timedelta(days=1)
        df = self.db.execute("SELECT * FROM observations WHERE timestamp < ?", [cutoff]).df()
        
        if not df.empty:
            archive_path = os.path.join(ARCHIVE_DIR, f"archive_{int(time.time())}.parquet")
            df.to_parquet(archive_path, compression="zstd")
            self.db.execute("DELETE FROM observations WHERE timestamp < ?", [cutoff])

# Global instance
data_controller = UnifiedDataController()
