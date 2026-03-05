from typing import List, Dict, Any
from src.core.plugin.interfaces import LearningPlugin, ContentItem
from src.plugins.english.lesson_store import LessonStore
from src.plugins.english.item_generator import ItemGenerator
from src.plugins.english.grader import EnglishGrader
from src.plugins.english.models import GradeResult

class EnglishPlugin(LearningPlugin):
    def __init__(self):
        super().__init__()
        self.lesson_store = LessonStore()
        self.generator = ItemGenerator()
        self.grader = EnglishGrader()
        self.active_items = {} # Simple in-memory storage for active items

    def get_content(self, difficulty: int) -> ContentItem:
        # Simple mapping for now
        level = "A2"
        if difficulty > 3: level = "B1"
        if difficulty > 4: level = "B2"
        
        lessons = self.lesson_store.get_lessons_by_level(level)
        if not lessons:
            lessons = self.lesson_store.get_all_lessons()
            
        selected_lesson = lessons[0] if lessons else None
        
        if not selected_lesson:
             return ContentItem(
                content_id="default",
                text="Welcome to English Learning. Let's start with basics.",
                difficulty=0.1,
                metadata={}
            )

        return ContentItem(
            content_id=selected_lesson.id,
            text=selected_lesson.text,
            difficulty=0.5,
            metadata={"title": selected_lesson.title}
        )

    def generate_items(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Context can include 'remediation_plan'
        """
        # If we have a remediation plan, adjust generation
        plan = context.get("remediation_plan", {})
        focus_types = plan.get("next_item_types", [])
        
        # Pass focus types to generator (if supported) - for now simplified
        # We just generate standard items but in future could filter
        
        items = self.generator.generate_items(context, count=3)
        
        # Store for grading
        for item in items:
            self.active_items[item.id] = item
            
        return [item.model_dump() for item in items]

    def grade_attempt(self, item_id: str, attempt: str) -> GradeResult:
        item = self.active_items.get(item_id)
        if not item:
            return GradeResult(score=0.0, feedback_short="Item expired or not found", error_codes=[])
            
        return self.grader.grade(item_id, attempt, item.correct_answer, item.type)
