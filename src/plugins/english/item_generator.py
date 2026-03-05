import uuid
from typing import List, Dict, Any
from src.plugins.english.models import LearningItem, LessonModel

class ItemGenerator:
    def generate_items(self, context: Any, count: int = 3) -> List[LearningItem]:
        # Handle different context types
        # 1. LessonModel (from RAG)
        if isinstance(context, LessonModel):
            return self._from_lesson_model(context, count)
            
        # 2. Dict (from Adaptive Engine)
        if isinstance(context, dict):
            content_id = context.get("content_id")
            remediation = context.get("remediation_plan", {})
            
            # Mock generation based on remediation
            items = []
            strategy = remediation.get("strategy", "practice")
            
            for i in range(count):
                item_type = "mcq"
                if strategy == "drill":
                    item_type = "vocab_fill"
                elif strategy == "explain":
                    item_type = "rewrite_sentence"
                    
                items.append(LearningItem(
                    id=str(uuid.uuid4()),
                    type=item_type,
                    question=f"Generated question {i+1} for {strategy}",
                    options=["A", "B", "C", "D"] if item_type == "mcq" else [],
                    correct_answer="A" if item_type == "mcq" else "answer",
                    difficulty=0.5,
                    skill_tag="general_english"
                ))
                
            return items
        
        return []

    def _from_lesson_model(self, lesson: LessonModel, count: int) -> List[LearningItem]:
        # If lesson already has items, use them
        if lesson.items:
            # Convert dicts to LearningItem objects if needed
            return [LearningItem(**item) if isinstance(item, dict) else item for item in lesson.items[:count]]
            
        # Fallback
        return [
            LearningItem(
                id=str(uuid.uuid4()),
                type="reading_qna",
                question=f"What is the main idea of: {lesson.title}?",
                correct_answer="To learn english",
                difficulty=0.5,
                skill_tag="reading_comprehension"
            )
        ]
