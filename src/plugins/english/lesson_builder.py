from typing import List, Dict, Any
from src.plugins.english.models import LessonModel, EnglishLevel

class LessonBuilder:
    def build_lesson_from_chunks(self, chunks: List[Dict[str, Any]], level: str = "A2") -> LessonModel:
        """
        Combines retrieved chunks into a cohesive lesson structure.
        """
        if not chunks:
            return LessonModel(
                id="empty", title="No Content", level=EnglishLevel(level), 
                tags=[], text="No relevant content found."
            )
            
        # 1. Combine texts
        # Sort by position to maintain narrative flow if possible
        sorted_chunks = sorted(chunks, key=lambda x: x.get("position", 0))
        combined_text = "\n\n".join([c["full_text"] for c in sorted_chunks])
        
        # 2. Truncate to reasonable length (e.g. 1500 chars)
        if len(combined_text) > 1500:
            combined_text = combined_text[:1500] + "..."
            
        # 3. Generate Title (Mock or First Sentence)
        first_sentence = combined_text.split('.')[0]
        title = f"Lesson: {first_sentence[:30]}..."
        
        # 4. Extract Tags
        tags = ["generated", "book-based"]
        
        return LessonModel(
            id=f"gen_{int(time.time())}",
            title=title,
            level=EnglishLevel(level),
            tags=tags,
            text=combined_text
        )

import time
