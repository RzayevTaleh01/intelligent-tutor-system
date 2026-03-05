from typing import List, Dict, Any, Optional
from src.core.plugin.interfaces import LearningPlugin, ContentItem, GradeResult
from src.plugins.english.models import LearningItem as EngItem, GradeResultModel, ItemType
from src.plugins.english.lesson_store import LessonStore
from src.plugins.english.generator import ItemGenerator
from src.plugins.english.grader import Grader

class EnglishPlugin(LearningPlugin):
    def __init__(self):
        self.lesson_store = LessonStore()
        self.generator = ItemGenerator()
        self.grader = Grader()
        self.active_items: Dict[str, EngItem] = {} # Cache generated items for grading

    def get_content(self, difficulty_level: str) -> ContentItem:
        # Map difficulty (easy/medium/hard) to CEFR levels
        level_map = {
            "easy": "A2",
            "medium": "B1",
            "hard": "B2"
        }
        target_level = level_map.get(difficulty_level, "A2")
        lessons = self.lesson_store.get_lessons_by_level(target_level)
        
        if not lessons:
            # Fallback to any lesson
            lessons = self.lesson_store.get_all_lessons()
            
        selected_lesson = lessons[0] if lessons else None
        
        if not selected_lesson:
            return ContentItem(content_id="null", text="No content available.", difficulty=0.0, metadata={})

        return ContentItem(
            content_id=selected_lesson.id,
            text=selected_lesson.text,
            difficulty=0.5, # Normalized difficulty
            metadata={
                "title": selected_lesson.title,
                "level": selected_lesson.level,
                "tags": selected_lesson.tags,
                "domain": "english"
            }
        )

    def generate_items(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Context should contain 'content_id' to know which lesson to generate for
        content_id = context.get("content_id")
        lesson = self.lesson_store.get_lesson(content_id)
        
        if not lesson:
            return []
            
        items = self.generator.generate_items(lesson, count=2)
        
        # Cache items for grading later
        for item in items:
            self.active_items[item.id] = item
            
        # Return serializable dicts
        return [item.model_dump() for item in items]

    def grade_attempt(self, item_id: str, user_input: str, context: Optional[Dict] = None) -> GradeResult:
        item = self.active_items.get(item_id)
        if not item:
            # Fallback or error
            return GradeResult(0, ["Item expired or not found"], "Error", "Item not found in active session.", 0)
            
        result_model = self.grader.grade(item, user_input)
        
        return GradeResult(
            score=result_model.score,
            errors=result_model.errors,
            feedback_short=result_model.feedback_short,
            feedback_long=result_model.feedback_long,
            suggested_next_difficulty=result_model.suggested_next_difficulty
        )

    def explain_hint(self, item_id: str, context: Dict) -> str:
        item = self.active_items.get(item_id)
        if not item:
            return "No hint available."
            
        if item.type == ItemType.VOCAB_FILL:
            return f"The word starts with '{item.expected_answer[0]}'."
        elif item.type == ItemType.GRAMMAR_MCQ:
            return "Look at the time reference in the sentence."
        return "Try to break down the sentence into smaller parts."
