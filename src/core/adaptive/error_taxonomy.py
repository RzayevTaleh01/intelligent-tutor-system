from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_adaptive import LearnerError

class ErrorTaxonomy:
    # Generic Error Codes
    MISSING_KEYWORD = "MISSING_KEYWORD"
    WRONG_CHOICE = "WRONG_CHOICE"
    GRAMMAR_TENSE = "GRAMMAR_TENSE"
    WORD_ORDER = "WORD_ORDER"
    SPELLING = "SPELLING"
    OFF_TOPIC = "OFF_TOPIC"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"
    
    @staticmethod
    def get_all_codes():
        return [
            ErrorTaxonomy.MISSING_KEYWORD,
            ErrorTaxonomy.WRONG_CHOICE,
            ErrorTaxonomy.GRAMMAR_TENSE,
            ErrorTaxonomy.WORD_ORDER,
            ErrorTaxonomy.SPELLING,
            ErrorTaxonomy.OFF_TOPIC,
            ErrorTaxonomy.INCOMPLETE,
            ErrorTaxonomy.UNKNOWN
        ]

class ErrorTracker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_errors(self, session_id: str, skill_tag: str, error_codes: List[str]):
        if not error_codes:
            return

        for code in error_codes:
            stmt = select(LearnerError).where(
                LearnerError.session_id == session_id,
                LearnerError.skill_tag == skill_tag,
                LearnerError.error_code == code
            )
            result = await self.db.execute(stmt)
            error_record = result.scalar_one_or_none()
            
            if error_record:
                error_record.count += 1
            else:
                error_record = LearnerError(
                    session_id=session_id,
                    skill_tag=skill_tag,
                    error_code=code,
                    count=1
                )
                self.db.add(error_record)
        
        await self.db.commit()

    async def get_top_errors(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        stmt = select(LearnerError).where(LearnerError.session_id == session_id).order_by(LearnerError.count.desc()).limit(limit)
        result = await self.db.execute(stmt)
        errors = result.scalars().all()
        return [{"code": e.error_code, "count": e.count, "skill": e.skill_tag} for e in errors]
