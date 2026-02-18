from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DecisionEvent:
    entity_id: int
    analysis_started_at: datetime | None = None
    analysis_finished_at: datetime | None = None
    decision_at: datetime | None = None
    execution_at: datetime | None = None
    outcome_at: datetime | None = None

    @property
    def timing_deltas(self) -> dict[str, float | None]:
        def seconds(a: datetime | None, b: datetime | None) -> float | None:
            if not a or not b:
                return None
            return (b - a).total_seconds()

        return {
            "time_to_analysis": seconds(self.analysis_started_at, self.analysis_finished_at),
            "time_to_decision": seconds(self.analysis_finished_at, self.decision_at),
            "time_to_execution": seconds(self.decision_at, self.execution_at),
            "time_to_outcome": seconds(self.execution_at, self.outcome_at),
        }
