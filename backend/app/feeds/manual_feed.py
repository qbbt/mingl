from __future__ import annotations

from .base import BaseFeed


class ManualFeed(BaseFeed):
    name = "manual"

    async def fetch(self) -> dict:
        return {}

    def normalize(self, raw: dict) -> dict:
        return raw

    async def publish(self, payload: dict) -> None:
        return None
