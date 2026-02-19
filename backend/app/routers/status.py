from __future__ import annotations
from fastapi import APIRouter
from app.services.priority_service import priority_service

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/status")
def status() -> dict:
    return {
        "version": "v1.6-loop-tightener",
        "mvp_completion": "96%",
        "features": [
            "autonomous_heartbeat",
            "loop_tightness_tracking",
            "urgency_prioritization",
            "bayesian_ready",
        ],
        "user_guide": "Run boot.ps1 to start the autonomous system.",
        "next": "Heatmap visualization",
    }

@router.get("/priorities")
async def get_priorities():
    """Returns entity urgency scores."""
    return await priority_service.calculate_entity_priorities()

@router.get("/tightness")
async def get_tightness():
    """Returns system loop efficiency metrics."""
    return await priority_service.get_system_tightness()
