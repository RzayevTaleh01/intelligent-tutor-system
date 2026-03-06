from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import LearnerState
from src.core.adaptive.bkt import BKTModel
from src.core.adaptive.srs import SRSScheduler

class LearnerEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bkt = BKTModel(db)
        self.srs = SRSScheduler(db)

    async def get_or_create_state(self, session_id: str) -> LearnerState:
        result = await self.db.execute(select(LearnerState).where(LearnerState.session_id == session_id))
        state = result.scalar_one_or_none()
        
        if not state:
            state = LearnerState(session_id=session_id, mastery_score=0.5, readiness_score=0.5, recent_errors=[])
            self.db.add(state)
            await self.db.commit()
            await self.db.refresh(state)
            
        return state

    async def update_state(self, state: LearnerState, assessment_result: dict[str, Any]):
        """
        Updates the learner state based on assessment results.
        Integrates BKT (Bayesian Knowledge Tracing) and SRS (Spaced Repetition).
        """
        session_id = state.session_id
        score = assessment_result.get("score", 0.0)
        
        # 1. Update Global Mastery (Simple Moving Average)
        alpha = 0.3
        state.mastery_score = (state.mastery_score * (1 - alpha)) + (score * alpha)
        
        # 2. Update Readiness (Heuristic)
        if score > 0.7:
            state.readiness_score = min(1.0, state.readiness_score + 0.1)
        else:
            state.readiness_score = max(0.0, state.readiness_score - 0.05)
            
        # 3. BKT Update (Skill Mastery)
        # We need a skill_tag. If not provided, assume 'general_skill' or derive from context
        skill_tag = assessment_result.get("skill_tag", "general_python") 
        is_correct = score >= 0.7 # Threshold for binary BKT
        
        new_p_mastery = await self.bkt.update_skill_state(session_id, skill_tag, is_correct)
        
        # 4. SRS Update (Forgetting Curve)
        srs_result = await self.srs.schedule_update(session_id, skill_tag, score)
        
        await self.db.commit()
        await self.db.refresh(state)
        
        return {
            "mastery_score": state.mastery_score,
            "readiness_score": state.readiness_score,
            "skill_mastery": new_p_mastery,
            "next_review": srs_result["due_at"]
        }
