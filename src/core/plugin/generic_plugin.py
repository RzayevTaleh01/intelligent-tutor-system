
import random
from typing import List, Dict, Any, Optional
from src.core.plugin.interfaces import LearningPlugin, ContentItem, GradeResult
from src.knowledge.engine import KnowledgeEngine
from src.db.models_knowledge import KnowledgeChunk
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
        """
        AI-driven assessment that evaluates the user's input against the course material.
        Uses the LLM to provide a semantic score and detailed feedback.
        """
        if not context or "db" not in context:
             return GradeResult(0.0, [], "System Error: Missing context", "Missing DB context", 0.0)

        db: AsyncSession = context["db"]
        
        # 1. Retrieve the context/material for this item (if item_id maps to a chunk)
        # For now, since we don't have a direct item_id->chunk_id map in this simple plugin,
        # we'll search for the most relevant chunk to the user's answer to see if they are on topic.
        # Ideally, 'item_id' should be the chunk_id we served them.
        
        knowledge_engine = KnowledgeEngine(db)
        # Try to find the chunk if item_id looks like a UUID (it usually is in our flow)
        reference_text = ""
        try:
             # We can't easily fetch by ID without a direct method in KnowledgeEngine or SQL
             # Let's use search to find the "Truth" based on user input, or assume item_id IS chunk_id
             # Let's assume item_id passed from FE is the chunk_id of the content they read.
             
             # Fetch chunk text directly
             stmt = select(KnowledgeChunk).where(KnowledgeChunk.id == item_id)
             res = await db.execute(stmt)
             chunk = res.scalar_one_or_none()
             if chunk:
                 reference_text = chunk.text
             else:
                 # Fallback: Search for relevant content if we can't find exact chunk
                 results = await knowledge_engine.search(user_input, course_id=self.course_id, k=1)
                 if results:
                     reference_text = results[0]["full_text"]
        except Exception:
             pass

        if not reference_text:
            reference_text = "General knowledge about the subject."

        # 2. Construct the Grading Prompt
        system_prompt = f"""You are an expert academic grader. 
        Your task is to evaluate a student's answer based ONLY on the provided Reference Material.
        
        Reference Material:
        "{reference_text[:1000]}..."
        
        Criteria:
        1. Accuracy (Is the information correct?)
        2. Relevance (Does it answer the implied question in the material?)
        3. Depth (Is it a trivial answer or thoughtful?)
        
        Output format: JSON with keys: 'score' (0.0 to 1.0), 'feedback' (short constructive text), 'error_type' (optional category like 'fact', 'concept', 'grammar').
        """
        
        user_prompt = f"Student Answer: {user_input}"
        
        # 3. Call LLM
        # We need access to the LLM. 
        # In this architecture, Plugin doesn't hold the LLM instance directly. 
        # We should probably get it from context or instantiate a provider.
        # For this refactor, let's instantiate OllamaProvider (stateless mostly) or passed in context.
        # Let's assume it's passed in context or we create one.
        
        from src.llm.providers.ollama import OllamaProvider
        llm = OllamaProvider() # It reads config internally
        
        try:
            # We ask for JSON format
            response_str = await llm.generate_chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], options={"temperature": 0.1}) # Low temp for consistent grading
            
            # Parse JSON
            # LLM might be chatty, let's try to find JSON
            import json
            import re
            
            # Simple regex to find JSON block
            match = re.search(r'\{.*\}', response_str, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
                score = float(data.get("score", 0.0))
                feedback = data.get("feedback", "No feedback provided.")
            else:
                # Fallback if no JSON found
                score = 0.5
                feedback = response_str
                
        except Exception as e:
            print(f"Grading Error: {e}")
            score = 0.0
            feedback = "Error during AI grading. Please try again."

        return GradeResult(
            score=score,
            errors=[],
            feedback_short=feedback[:100], # Short version
            feedback_long=feedback,
            suggested_next_difficulty=0.5 # Dynamic later
        )

    def explain_hint(self, item_id: str, context: Dict) -> str:
        return "Review the course materials."
