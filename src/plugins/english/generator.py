import random
import uuid
from typing import List, Dict, Any
from src.plugins.english.models import LearningItem, ItemType, LessonModel
from src.config import get_settings

settings = get_settings()

class ItemGenerator:
    def __init__(self):
        self.use_llm = os.getenv("USE_LLM_FOR_ITEM_GEN", "false").lower() == "true"
        # In a real scenario, you'd inject the Ollama client here
        
    def generate_items(self, lesson: LessonModel, count: int = 1) -> List[LearningItem]:
        items = []
        
        # Rule-based generation (deterministic, cheap)
        # 1. Vocab Fill (Simple keyword blanking)
        words = lesson.text.split()
        long_words = [w.strip(".,!?") for w in words if len(w) > 4]
        if long_words:
            target_word = random.choice(long_words)
            sentence = next((s for s in lesson.text.split(".") if target_word in s), "")
            if sentence:
                prompt = sentence.replace(target_word, "______") + "."
                items.append(LearningItem(
                    id=str(uuid.uuid4()),
                    type=ItemType.VOCAB_FILL,
                    prompt=f"Fill in the blank: {prompt}",
                    expected_answer=target_word,
                    difficulty=2,
                    skill_tag="vocabulary"
                ))

        # 2. Grammar MCQ (Mock rule-based)
        items.append(LearningItem(
            id=str(uuid.uuid4()),
            type=ItemType.GRAMMAR_MCQ,
            prompt="Choose the correct verb form: 'I ______ to London yesterday.'",
            choices=["go", "went", "gone", "going"],
            expected_answer="went",
            difficulty=2,
            skill_tag="grammar"
        ))

        # 3. LLM-based Generation (Optional)
        if self.use_llm and count > len(items):
            # This would be an async call in a real async pipeline, 
            # but for this synchronous generator interface we might skip or mock
            pass 
            
        # Ensure we return requested count (fill with mock if needed)
        while len(items) < count:
            items.append(LearningItem(
                id=str(uuid.uuid4()),
                type=ItemType.REWRITE_SENTENCE,
                prompt=f"Rewrite the following sentence in passive voice: '{lesson.text.split('.')[0]}'",
                difficulty=4,
                skill_tag="writing"
            ))
            
        return items[:count]

import os
