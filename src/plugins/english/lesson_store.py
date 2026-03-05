import json
import os
from typing import List, Optional, Dict
from src.plugins.english.models import LessonModel

class LessonStore:
    def __init__(self, data_dir: str = "data/lessons"):
        self.data_dir = data_dir
        self.lessons: Dict[str, LessonModel] = {}
        self._load_lessons()

    def _load_lessons(self):
        if not os.path.exists(self.data_dir):
            return
            
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.data_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        lesson = LessonModel(**data)
                        self.lessons[lesson.id] = lesson
                except Exception as e:
                    print(f"Error loading lesson {filename}: {e}")

    def get_lesson(self, lesson_id: str) -> Optional[LessonModel]:
        return self.lessons.get(lesson_id)

    def get_all_lessons(self) -> List[LessonModel]:
        return list(self.lessons.values())

    def get_lessons_by_level(self, level: str) -> List[LessonModel]:
        return [l for l in self.lessons.values() if l.level == level]
