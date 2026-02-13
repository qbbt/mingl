from __future__ import annotations

from abc import ABC, abstractmethod


class BrokerAdapter(ABC):
    @abstractmethod
    def validate(self, order: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def paper_execute(self, order: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def live_execute(self, order: dict) -> dict:
        raise NotImplementedError


class IbkrStubAdapter(BrokerAdapter):
    def validate(self, order: dict) -> None:
        required = {"symbol", "side", "quantity"}
        missing = required - set(order.keys())
        if missing:
            raise ValueError(f"Missing order keys: {sorted(missing)}")

    def paper_execute(self, order: dict) -> dict:
        self.validate(order)
        return {"status": "paper_filled", "broker": "ibkr_stub", "order": order}

    def live_execute(self, order: dict) -> dict:
        self.validate(order)
        return {"status": "live_not_enabled", "broker": "ibkr_stub", "order": order}
