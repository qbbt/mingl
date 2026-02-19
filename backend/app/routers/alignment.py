from fastapi import APIRouter, HTTPException
from app.services.alignment_service import alignment_service
from typing import List, Dict, Any
import numpy as np

router = APIRouter(prefix="/alignment", tags=["Alignment Protocol"])

@router.get("/status")
async def get_alignment_status():
    """Returns the latest alignment objective and system health."""
    return await alignment_service.get_current_status()

@router.get("/ledger")
async def get_ledger_history(limit: int = 50):
    """Returns the history of the alignment ledger."""
    from app.repositories.data_repository import data_repo
    return await data_repo.get_ledger_history(limit)

@router.post("/feedback")
async def post_alignment_feedback(user_score: float, agent_score: float, notes: str = ""):
    """Logs a new alignment event with user feedback."""
    return await alignment_service.log_alignment_event(user_score, agent_score, notes)

@router.get("/debt")
async def get_technical_debt():
    """Returns the list of architectural drift violations from the Night Watchman."""
    import os
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    scripts_dir = os.path.join(project_root, "backend", "scripts")
    
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    try:
        import night_watchman
        watchman = night_watchman.NightWatchman(project_root)
        violations = watchman.scan_for_drift()
        
        return {
            "debt_score": len(violations) * 5,
            "violations": violations
        }
    except Exception as e:
        return {"error": f"Watchman Load Error: {str(e)}", "violations": []}

@router.get("/stats")
async def get_alignment_stats():
    """Returns detailed statistics for dashboard visualization."""
    from app.repositories.data_repository import data_repo
    from app.services.stats_engine import stats_engine
    import pandas as pd
    
    try:
        history = await data_repo.get_ledger_history(limit=100)
        if not history:
            return {"objective": 0.5, "weights": {}, "history": [], "phase": "Empty"}
        
        # Defensive cleaning of history (NaN -> None)
        cleaned_history = []
        for row in history:
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                    cleaned_row[k] = None
                else:
                    cleaned_row[k] = v
            cleaned_history.append(cleaned_row)
            
        df = pd.DataFrame(cleaned_history)
        # Mapping ledger column names to stats engine expected names
        df['stability_score'] = 1.0 - df.get('aleatoric_uncertainty', 0.3).fillna(0.3)
        
        # Re-calculate current objective and weights
        results = stats_engine.compute_alignment_objective(df)
        
        return {
            "objective": float(np.nan_to_num(results["objective"], nan=0.5)),
            "weights": {k: float(np.nan_to_num(v, nan=0.33)) for k, v in results["weights"].items()},
            "history": cleaned_history,
            "phase": results.get("phase", "Unknown")
        }
    except Exception as e:
        print(f"[ALIGNMENT] Stats Error: {e}")
        return {"objective": 0.5, "weights": {}, "history": [], "error": str(e), "phase": "Error"}
