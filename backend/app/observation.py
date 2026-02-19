from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union


@dataclass
class DecisionEvent:
    entity_id: int
    analysis_started_at: Optional[datetime] = None
    analysis_finished_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    execution_at: Optional[datetime] = None
    outcome_at: Optional[datetime] = None

    @property
    def timing_deltas(self) -> dict[str, Optional[float]]:
        def seconds(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
            if not a or not b:
                return None
            return (b - a).total_seconds()

        return {
            "time_to_analysis": seconds(self.analysis_started_at, self.analysis_finished_at),
            "time_to_decision": seconds(self.analysis_finished_at, self.decision_at),
            "time_to_execution": seconds(self.decision_at, self.execution_at),
            "time_to_outcome": seconds(self.execution_at, self.outcome_at),
        }
