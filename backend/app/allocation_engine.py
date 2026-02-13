from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpportunityScore:
    expected_value: float
    confidence: float
    opportunity_cost: float
    score: float


def score_opportunity(expected_value: float, confidence: float, best_alternative_ev: float) -> OpportunityScore:
    opportunity_cost = max(0.0, best_alternative_ev - expected_value)
    score = (expected_value * confidence) - opportunity_cost
    return OpportunityScore(
        expected_value=expected_value,
        confidence=confidence,
        opportunity_cost=opportunity_cost,
        score=score,
    )
