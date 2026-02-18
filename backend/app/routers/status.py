from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["status"])


@router.get("/status")
def status() -> dict:
    return {
        "version": "v1.5-optimizer",
        "mvp_completion": "94%",
        "features": [
            "lag_sweep",
            "heat_focus_map",
            "mp3_overlay_stub",
            "bayesian_ready",
            "ios_quicklog_plan",
        ],
        "user_guide": "Open dashboard, seed data, graph metrics, run top-N and analytics endpoints.",
        "next": "add IBKR credentials/config for non-stub execution path",
    }
