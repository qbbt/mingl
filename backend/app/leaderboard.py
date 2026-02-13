from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RankingProfile:
    mode: str = "auto"
    ev_weight: float = 1.0
    confidence_weight: float = 1.0
    volatility_penalty_weight: float = 1.0
    decay_weight: float = 1.0
    attention_cost_weight: float = 1.0
    execution_reliability_weight: float = 1.0


DEFAULT_PROFILE = RankingProfile()


def compute_score(
    *,
    expected_value: float,
    confidence: float,
    volatility_penalty: float,
    decay: float,
    attention_cost: float,
    execution_reliability: float,
    profile: RankingProfile,
) -> tuple[float, dict]:
    score = (
        (expected_value * profile.ev_weight)
        + (confidence * profile.confidence_weight)
        - (volatility_penalty * profile.volatility_penalty_weight)
        - (decay * profile.decay_weight)
        - (attention_cost * profile.attention_cost_weight)
        + (execution_reliability * profile.execution_reliability_weight)
    )
    return score, {
        "expected_value": expected_value,
        "confidence": confidence,
        "volatility_penalty": volatility_penalty,
        "decay": decay,
        "attention_cost": attention_cost,
        "execution_reliability": execution_reliability,
        "mode": profile.mode,
    }
