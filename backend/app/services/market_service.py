from app.repositories.data_repository import data_repo
from typing import List, Dict, Optional, Union
from datetime import datetime

class MarketService:
    """
    Business Logic Layer.
    Job: Orchestrates data between repositories and applies transformations.
    """
    async def get_layered_series(self, entity_id: int, metric_name: str, limit: int = 500) -> List[Dict]:
        # Business Rule: Market Overrides come from the DataRepo's layered logic
        return await data_repo.get_layered_data(entity_id, metric_name, limit)

    async def push_observation(self, entity_id: int, metric_name: str, value: float, is_override: bool = False, timestamp: Optional[Union[str, datetime]] = None):
        priority = 1.0 if is_override else 0.5
        ts = None
        if isinstance(timestamp, datetime):
            ts = timestamp
        elif isinstance(timestamp, str):
            try:
                ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                pass
        await data_repo.add_observation(entity_id, metric_name, value, priority, ts)

    async def get_available_metrics(self, entity_id: int) -> List[str]:
        return await data_repo.get_available_metrics(entity_id)

# Singleton instance
market_service = MarketService()
