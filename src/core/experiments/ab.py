import hashlib
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_diagnostics import ExperimentAssignment

class ABTestFramework:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_variant(self, session_id: str) -> str:
        # Check existing
        stmt = select(ExperimentAssignment).where(ExperimentAssignment.session_id == session_id)
        res = await self.db.execute(stmt)
        assign = res.scalar_one_or_none()
        
        if assign:
            return assign.variant
            
        # Assign new (Deterministic based on hash)
        hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        variant = "A" if hash_val % 2 == 0 else "B"
        
        new_assign = ExperimentAssignment(session_id=session_id, variant=variant)
        self.db.add(new_assign)
        await self.db.commit()
        
        return variant
