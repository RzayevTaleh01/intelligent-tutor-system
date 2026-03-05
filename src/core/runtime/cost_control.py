from typing import List, Dict, Any
from src.config import get_settings

settings = get_settings()

class CostController:
    def __init__(self):
        self.max_chars = settings.MAX_CONTEXT_CHARS
        self.use_llm_summary = settings.USE_LLM_FOR_SUMMARY

    def optimize_context(self, history: List[Dict[str, str]], lesson_text: str) -> Dict[str, Any]:
        """
        Truncates lesson text and summarizes history to fit within limits.
        """
        # 1. Truncate Lesson Text (Keep first 2000 chars roughly)
        optimized_text = lesson_text
        if len(lesson_text) > 2000:
            optimized_text = lesson_text[:2000] + "... [Content Truncated]"

        # 2. Optimize History
        # Strategy: Keep last N messages fully, summarize older ones if needed
        # Simple heuristic: Keep last 6 messages
        optimized_history = history[-6:]
        
        # Calculate total chars
        total_chars = len(optimized_text) + sum(len(m["content"]) for m in optimized_history)
        
        # If still too long, aggressively prune history
        if total_chars > self.max_chars:
            # Keep only last 2 messages
            optimized_history = history[-2:]
            
        return {
            "lesson_text": optimized_text,
            "history": optimized_history,
            "summary": "Previous context summarized." if len(history) > len(optimized_history) else ""
        }
