from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFeed(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, payload: dict) -> None:
        raise NotImplementedError
