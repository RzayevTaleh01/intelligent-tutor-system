from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_adaptive import LearnerSkill

class BKTModel:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Default Parameters
        self.default_p_mastery = 0.1
        self.default_p_learn = 0.1
        self.default_p_slip = 0.1
        self.default_p_guess = 0.2

    async def update_skill_state(self, session_id: str, skill_tag: str, is_correct: bool) -> float:
        """
        Updates the mastery probability for a skill based on BKT formula.
        Returns the new posterior mastery.
        """
        stmt = select(LearnerSkill).where(
            LearnerSkill.session_id == session_id,
            LearnerSkill.skill_tag == skill_tag
        )
        result = await self.db.execute(stmt)
        skill = result.scalar_one_or_none()
        
        if not skill:
            skill = LearnerSkill(
                session_id=session_id,
                skill_tag=skill_tag,
                p_mastery=self.default_p_mastery,
                p_learn=self.default_p_learn,
                p_slip=self.default_p_slip,
                p_guess=self.default_p_guess
            )
            self.db.add(skill)
            # Need to flush to get defaults if any, but we set them manually
        
        # Current mastery (Prior)
        L_prev = skill.p_mastery
        
        # 1. Probability of mastery given evidence
        if is_correct:
            # P(L|Correct) = [P(L) * (1 - P(S))] / [P(L)*(1-P(S)) + (1-P(L))*P(G)]
            numerator = L_prev * (1 - skill.p_slip)
            denominator = numerator + (1 - L_prev) * skill.p_guess
        else:
            # P(L|Incorrect) = [P(L) * P(S)] / [P(L)*P(S) + (1-P(L))*(1-P(G))]
            numerator = L_prev * skill.p_slip
            denominator = numerator + (1 - L_prev) * (1 - skill.p_guess)
            
        L_given_evidence = numerator / (denominator + 1e-10)
        
        # 2. Update with learning rate (Posterior)
        # P(L_new) = P(L|Evidence) + (1 - P(L|Evidence)) * P(T)
        L_new = L_given_evidence + (1 - L_given_evidence) * skill.p_learn
        
        # Update state
        skill.p_mastery = min(0.99, max(0.01, L_new))
        
        await self.db.commit()
        await self.db.refresh(skill)
        return skill.p_mastery

    async def get_skill_state(self, session_id: str, skill_tag: str) -> Optional[Dict[str, float]]:
        stmt = select(LearnerSkill).where(
            LearnerSkill.session_id == session_id,
            LearnerSkill.skill_tag == skill_tag
        )
        result = await self.db.execute(stmt)
        skill = result.scalar_one_or_none()
        
        if skill:
            return {
                "p_mastery": skill.p_mastery,
                "p_slip": skill.p_slip,
                "p_guess": skill.p_guess,
                "p_learn": skill.p_learn
            }
        return None
