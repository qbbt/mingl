from __future__ import annotations

from datetime import datetime
from random import random

from .base import BaseFeed


class MockCryptoFeed(BaseFeed):
    name = "mock_crypto"

    def __init__(self, symbol: str = "BTC-USD", base_price: float = 60000.0):
        self.symbol = symbol
        self.price = base_price

    async def fetch(self) -> dict:
        drift = (random() - 0.5) * 200
        self.price += drift
        return {"symbol": self.symbol, "price": round(self.price, 2), "timestamp": datetime.utcnow().isoformat()}

    def normalize(self, raw: dict) -> dict:
        return {
            "entity_name": raw["symbol"],
            "value": float(raw["price"]),
            "timestamp": datetime.fromisoformat(raw["timestamp"]),
            "event_type": "tick",
        }

    async def publish(self, payload: dict) -> None:
        return None
