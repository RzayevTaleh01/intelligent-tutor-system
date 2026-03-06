
import random
from typing import List, Dict, Any, Optional
from src.core.plugin.interfaces import LearningPlugin, ContentItem, GradeResult
from src.knowledge.engine import KnowledgeEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_course import Course

class GenericPlugin(LearningPlugin):
    """
    A plugin that dynamically adapts to any course by using its Knowledge Base (RAG)
    and pedagogical settings stored in the database.
    """
    def __init__(self, course_id: str):
        self.course_id = course_id
        # We don't hold a DB session here because plugins are long-lived (singleton in registry),
        # while sessions are short-lived. We expect 'db' in context.

    async def _get_course_settings(self, db: AsyncSession) -> Dict:
        stmt = select(Course).where(Course.id == self.course_id)
        res = await db.execute(stmt)
        course = res.scalar_one_or_none()
        return course.settings if course else {}

    async def get_content(self, difficulty_level: float, context: Optional[Dict] = None) -> ContentItem:
        if not context or "db" not in context:
            return ContentItem("error", "Database context missing.", 0.0, {})
            
        db: AsyncSession = context["db"]
        knowledge_engine = KnowledgeEngine(db)
        
        # Strategy:
        # 1. Look for a "syllabus" or "curriculum" in course settings.
        # 2. If not found, use RAG to find "introduction" or "basic concepts" for low difficulty.
        # 3. If high difficulty, find "advanced" topics.
        
        # For MVP: Simple RAG based on difficulty keywords
        query = "introduction basic concepts" if difficulty_level < 0.4 else \
                "intermediate details examples" if difficulty_level < 0.7 else \
                "advanced complex scenarios"
                
        # Search specifically within this course
        results = await knowledge_engine.search(query, course_id=self.course_id, k=1)
        
        if not results:
            return ContentItem(
                content_id="no_content",
                text=f"No content found for course {self.course_id}. Please upload materials.",
                difficulty=0.0,
                metadata={}
            )
            
        chunk = results[0]
        return ContentItem(
            content_id=chunk["chunk_id"],
            text=chunk["full_text"], # Return full chunk text as lesson
            difficulty=difficulty_level,
            metadata={"score": chunk["score"]}
        )
    
    def generate_items(self, context: Dict[str, Any]) -> List[Any]:
        # TODO: Use LLM to generate questions from the content found in context
        return []
        
    async def grade_attempt(self, item_id: str, user_input: str, context: Optional[Dict] = None) -> GradeResult:
        # Generic grading: Just length check or simple heuristic for now.
        # In real impl, we'd use LLM to grade against the content.
        
        score = 0.0
        feedback = "Please try again."
        
        if len(user_input.split()) > 3:
            score = 0.8
            feedback = "Good effort! (Generic Grading)"
            
        return GradeResult(
            score=score,
            errors=[],
            feedback_short=feedback,
            feedback_long=feedback,
            suggested_next_difficulty=0.6 # Static for now
        )

    def explain_hint(self, item_id: str, context: Dict) -> str:
        return "Review the course materials."
