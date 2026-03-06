from typing import List, Dict, Any, Optional
from src.core.plugin.interfaces import LearningPlugin, ContentItem, GradeResult

class DefaultPlugin(LearningPlugin):
    async def get_content(self, difficulty_level: float, context: Optional[Dict] = None) -> ContentItem:
        return ContentItem(
            content_id="generic_101",
            text="This is a generic learning item. Please configure a domain plugin.",
            difficulty=0.5,
            metadata={}
        )
    
    def generate_items(self, context: Dict[str, Any]) -> List[Any]:
        return []
        
    async def grade_attempt(self, item_id: str, user_input: str, context: Optional[Dict] = None) -> GradeResult:
        return GradeResult(
            score=1.0,
            errors=[],
            feedback_short="Good job!",
            feedback_long="This is a generic feedback.",
            suggested_next_difficulty=0.6
        )
        
    def explain_hint(self, item_id: str, context: Dict) -> str:
        return "No specific hints available in generic mode."
