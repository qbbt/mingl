import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from app.repositories.data_repository import data_repo
from app.services.stats_engine import stats_engine

class AlignmentService:
    """
    Orchestrator for the Alignment Protocol.
    Links the StatsEngine with the DataRepository.
    """
    
    async def log_alignment_event(self, user_score: float, agent_score: float, notes: str = ""):
        """
        Processes a commitment or feedback event.
        Filters noise, computes objective, and persists to ledger.
        """
        # 1. Fetch historical ledger for context
        history = await data_repo.get_ledger_history(limit=100)
        df_history = pd.DataFrame(history)
        
        # 2. Filter User Score
        filtered_user = stats_engine.filter_user_score(user_score)
        
        # 3. Compute Metrics (Simplified for initial bootstrap)
        # In a full impl, pearson_r and knowledge_gain would be calculated from the history
        pearson_r = 0.8 # Placeholder for initial row
        knowledge_gain = 0.1 # Placeholder
        stability_score = 0.7 # Placeholder
        
        # 4. Compute Alignment Objective
        # We append the current row to history to get the latest objective
        new_row = {
            "pearson_r": pearson_r,
            "knowledge_gain": knowledge_gain,
            "stability_score": stability_score,
            "user_score": user_score,
            "agent_score": agent_score
        }
        
        # If history is empty, use defaults
        if df_history.empty:
            df_for_calc = pd.DataFrame([new_row])
        else:
            df_for_calc = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            
        objective_data = stats_engine.compute_alignment_objective(df_for_calc)
        
        # Calculate Alignment Lag (Time since last observation for context)
        # Simplified: fetch latest observation timestamp for this entity-metric
        # In this initial bootstrap, we use the timestamp of the event
        alignment_lag = 0.0 # Placeholder
        
        # 5. Persist to Repository
        entry = {
            "timestamp": datetime.utcnow(),
            "commit_id": "manual-" + datetime.utcnow().strftime("%Y%m%d%H%M"),
            "agent_score": agent_score,
            "user_score": user_score,
            "filtered_user_score": filtered_user,
            "pearson_r": pearson_r,
            "r_squared": pearson_r ** 2,
            "knowledge_gain": knowledge_gain,
            "aleatoric_uncertainty": 1.0 - stability_score,
            "technical_debt_score": 0, # To be filled by Night Watchman
            "alignment_objective": objective_data["objective"],
            "alignment_lag": alignment_lag, # Enshrining the 'Loop Tightness'
            "notes": notes
        }
        
        await data_repo.add_ledger_entry(entry)
        
        # 6. Meta-Alignment: Feed back into the system as an observation
        # Register SYSTEM-ALIGNMENT (Entity ID 0)
        from app.services.market_service import market_service
        try:
            await market_service.push_observation(
                entity_id=0, # Meta-Entity
                metric_name="loyalty",
                value=float(objective_data["objective"]),
                is_override=False,
                timestamp=entry["timestamp"]
            )
        except Exception as e:
            # Don't fail the primary log if meta-logging fails
            print(f"[META-ALIGNMENT] Warning: Failed to log system-alignment: {e}")

        return entry

    async def get_current_status(self) -> Dict[str, Any]:
        """Returns the latest alignment snapshot."""
        history = await data_repo.get_ledger_history(limit=1)
        if not history:
            # Return defaults from stats_engine
            meta = stats_engine.compute_alignment_objective(pd.DataFrame())
            return {
                "status": "no_data",
                "objective": meta["objective"],
                "weights": meta["weights"],
                "pearson_r": 0.0,
                "risk": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        latest = history[0]
        return {
            "status": "active",
            "objective": latest["alignment_objective"],
            "pearson_r": latest["pearson_r"],
            "risk": 0.1, # Placeholder
            "timestamp": latest["timestamp"]
        }

# Singleton instance
alignment_service = AlignmentService()
