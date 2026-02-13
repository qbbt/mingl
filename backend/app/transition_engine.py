from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TransitionResult:
    next_value: float
    expected_delta: float


def first_order_transition(current_value: float, drift: float, control: float = 0.0) -> TransitionResult:
    """Minimal state transition primitive for abstract engine evolution."""
    delta = drift + control
    return TransitionResult(next_value=current_value + delta, expected_delta=delta)
