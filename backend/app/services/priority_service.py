import numpy as np
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from app.db import get_session, EntityModel, PredictionModel
from app.repositories.data_repository import data_repo

class PriorityService:
    """
    Orchestrates the 'Tighten the Loop' logic.
    Calculates Urgency Scores based on Uncertainty, Volatility, and Recency.
    """

    async def calculate_entity_priorities(self) -> List[Dict[str, Any]]:
        """
        Computes prioritization scores for all entities.
        Higher score = Higher urgency for alignment.
        """
        priorities = []
        with get_session() as session:
            entities = session.scalars(select(EntityModel)).all()
            
            for entity in entities:
                # 1. Uncertainty (from latest prediction confidence)
                pred = session.scalar(
                    select(PredictionModel)
                    .where(PredictionModel.entity_id == entity.id)
                    .order_by(PredictionModel.timestamp.desc())
                    .limit(1)
                )
                uncertainty = 1.0 - (pred.confidence if pred else 0.5)
                
                # 2. Recency (time since last alignment)
                last_alignment = await data_repo.get_ledger_history(limit=1) # Ideally filtered by entity
                # Simplified: for now, we'll use a placeholder for per-entity alignment recency
                # In a full impl, we'd query the ledger for the specific entity_id
                recency_days = 1.0 # Placeholder
                
                # 3. Urgency Score Calculation
                # Higher uncertainty and higher weight = higher priority
                score = (uncertainty * entity.weight) / (recency_days + 1.0)
                
                priorities.append({
                    "entity_id": entity.id,
                    "name": entity.name,
                    "urgency_score": float(score),
                    "uncertainty": float(uncertainty),
                    "weight": entity.weight
                })
        
        # Sort by urgency
        return sorted(priorities, key=lambda x: x["urgency_score"], reverse=True)

    async def get_system_tightness(self) -> Dict[str, Any]:
        """
        Calculates 'Loop Tightness': Delay between Observations and Alignment.
        """
        # Fetch last 10 observations and last 10 alignment events
        # Calculate avg lag
        return {
            "avg_latency_ms": 1250.0, # Placeholder for Phase 10
            "tightness_ratio": 0.85,  # 1.0 is perfect synchronization
            "timestamp": datetime.utcnow().isoformat()
        }

priority_service = PriorityService()
