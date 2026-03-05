from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ContentType(str, Enum):
    TEXT = "text"
    EXERCISE = "exercise"

@dataclass
class ContentItem:
    content_id: str
    text: str
    difficulty: float
    metadata: Dict[str, Any]

@dataclass
class GradeResult:
    score: float
    errors: List[str]
    feedback_short: str
    feedback_long: str
    suggested_next_difficulty: float

class LearningPlugin(Protocol):
    """Interface that all domain plugins must implement."""
    
    def get_content(self, difficulty_level: str) -> ContentItem:
        """Retrieves learning content based on difficulty."""
        ...
    
    def generate_items(self, context: Dict[str, Any]) -> List[Any]:
        """Generates new items dynamically."""
        ...
        
    def grade_attempt(self, item_id: str, user_input: str, context: Optional[Dict] = None) -> GradeResult:
        """Grades a user's attempt."""
        ...
        
    def explain_hint(self, item_id: str, context: Dict) -> str:
        """Provides a hint for the current problem."""
        ...
