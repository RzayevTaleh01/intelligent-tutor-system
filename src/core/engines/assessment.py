from typing import Dict, Any
from src.core.plugin.interfaces import LearningPlugin

class AssessmentEngine:
    def __init__(self, plugin: LearningPlugin):
        self.plugin = plugin

    async def evaluate_interaction(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Uses the domain plugin to grade the user's attempt.
        """
        # Since LearningPlugin.grade_attempt is async and requires item_id, user_input, context
        # We need to adapt the call. Assuming user_message is the input.
        # But we need an item_id. If context has it, use it.
        item_id = context.get("item_id", "unknown") if context else "unknown"
        
        # Call the plugin
        # Note: The plugin returns a GradeResult object, not a float.
        # But existing code expected a float score.
        # We should handle GradeResult.
        
        result = await self.plugin.grade_attempt(item_id, user_message, context)
        
        # If result is a float (legacy mock), handle it
        if isinstance(result, (int, float)):
            score = float(result)
            errors = []
        else:
            # Assume GradeResult object
            score = result.score
            errors = result.errors
        
        if score < 0.6:
            errors.append("Low accuracy response")
            
        return {
            "score": score,
            "errors": errors,
            "timestamp": "now" # In real app use datetime
        }
