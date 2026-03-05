from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_adaptive import LearnerSchedule

class SRSScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_update(self, session_id: str, skill_tag: str, score: float) -> Dict[str, Any]:
        """
        Updates the schedule for a skill using a hybrid SM-2 / Leitner approach.
        score: 0.0 to 1.0
        """
        stmt = select(LearnerSchedule).where(
            LearnerSchedule.session_id == session_id,
            LearnerSchedule.skill_tag == skill_tag
        )
        result = await self.db.execute(stmt)
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            schedule = LearnerSchedule(
                session_id=session_id,
                skill_tag=skill_tag,
                due_at=datetime.now(),
                interval_days=0.5, # Start with half day
                ease=2.5,
                repetitions=0
            )
            self.db.add(schedule)
            
        # Map score (0-1) to quality (0-5)
        quality = int(score * 5)
        
        if quality >= 3:
            # Correct response
            if schedule.repetitions == 0:
                schedule.interval_days = 1
            elif schedule.repetitions == 1:
                schedule.interval_days = 6
            else:
                schedule.interval_days = schedule.interval_days * schedule.ease
            
            schedule.repetitions += 1
            schedule.ease = schedule.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        else:
            # Incorrect response
            schedule.repetitions = 0
            schedule.interval_days = 1
            
        if schedule.ease < 1.3:
            schedule.ease = 1.3
            
        schedule.due_at = datetime.now() + timedelta(days=schedule.interval_days)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return {
            "due_at": schedule.due_at,
            "interval_days": schedule.interval_days,
            "ease": schedule.ease
        }

    async def get_due_skills(self, session_id: str) -> List[str]:
        now = datetime.now()
        stmt = select(LearnerSchedule.skill_tag).where(
            LearnerSchedule.session_id == session_id,
            LearnerSchedule.due_at <= now
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
