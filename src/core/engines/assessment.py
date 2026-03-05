from typing import Dict, Any
from src.core.plugin.interfaces import LearningPlugin

class AssessmentEngine:
    def __init__(self, plugin: LearningPlugin):
        self.plugin = plugin

    def evaluate_interaction(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Uses the domain plugin to grade the user's attempt.
        """
        score = self.plugin.grade_attempt(user_message, context)
        
        # Determine if there were errors (simplified)
        errors = []
        if score < 0.6:
            errors.append("Low accuracy response")
            
        return {
            "score": score,
            "errors": errors,
            "timestamp": "now" # In real app use datetime
        }
