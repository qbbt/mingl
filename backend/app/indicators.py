from __future__ import annotations
from typing import Optional, Union


def sma(values: list[float], window: int) -> list[Optional[float]]:
    if window <= 0:
        raise ValueError("window must be > 0")
    out: list[Optional[float]] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
            continue
        chunk = values[i + 1 - window : i + 1]
        out.append(sum(chunk) / window)
    return out


def ema(values: list[float], window: int) -> list[Optional[float]]:
    if window <= 0:
        raise ValueError("window must be > 0")
    out: list[Optional[float]] = []
    k = 2 / (window + 1)
    running: Optional[float] = None
    for i, v in enumerate(values):
        if running is None:
            running = v
        else:
            running = (v * k) + (running * (1 - k))
        out.append(running if i + 1 >= window else None)
    return out


INDICATOR_REGISTRY = {
    "sma": sma,
    "ema": ema,
}
