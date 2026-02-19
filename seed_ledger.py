import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.alignment_service import alignment_service
from app.repositories.data_repository import data_repo

async def seed():
    print("[SEED] Ensuring ledger table exists...")
    await data_repo._init_ledger()
    print("[SEED] Seeding initial alignment ledger entry...")
    await alignment_service.log_alignment_event(
        user_score=0.8,
        agent_score=0.85,
        notes="Initial baseline seeding for Alignment Protocol v2.2."
    )
    print("[SEED] Done.")

if __name__ == "__main__":
    asyncio.run(seed())
