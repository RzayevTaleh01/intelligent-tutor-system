from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import LearnerState

class LearnerEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_state(self, session_id: str) -> LearnerState:
        result = await self.db.execute(select(LearnerState).where(LearnerState.session_id == session_id))
        state = result.scalar_one_or_none()
        
        if not state:
            state = LearnerState(session_id=session_id, mastery_score=0.5, readiness_score=0.5, recent_errors=[])
            self.db.add(state)
            await self.db.commit()
            await self.db.refresh(state)
            
        return state

    async def update_state(self, state: LearnerState, assessment_result: Dict[str, Any]):
        """
        Updates the learner state based on assessment results.
        """
        score = assessment_result.get("score", 0.0)
        
        # Simple moving average for mastery update
        alpha = 0.3
        state.mastery_score = (state.mastery_score * (1 - alpha)) + (score * alpha)
        
        # Update readiness (simplified logic)
        if score > 0.7:
            state.readiness_score = min(1.0, state.readiness_score + 0.1)
        else:
            state.readiness_score = max(0.0, state.readiness_score - 0.05)
            
        await self.db.commit()
        await self.db.refresh(state)
        return state
