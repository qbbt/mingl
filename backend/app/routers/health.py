from fastapi import APIRouter, HTTPException
from app.repositories.data_repository import data_repo

router = APIRouter(prefix="/health", tags=["System"])

@router.get("")
async def health_check():
    """
    Health check for verifying DuckDB and Metadata connectivity.
    The 'Sofa Check Engine Light'.
    """
    db_ok = await data_repo.check_health()
    if not db_ok:
        raise HTTPException(status_code=503, detail="DuckDB Connection Failed")
    
    return {
        "status": "online",
        "database": "reachable",
        "lock_status": "none"
    }
