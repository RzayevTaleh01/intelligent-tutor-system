from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class EnglishLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class ItemType(str, Enum):
    VOCAB_FILL = "vocab_fill"
    GRAMMAR_MCQ = "grammar_mcq"
    READING_QNA = "reading_qna"
    REWRITE_SENTENCE = "rewrite_sentence"

class LessonModel(BaseModel):
    id: str
    title: str
    level: EnglishLevel
    tags: List[str]
    text: str

class LearningItem(BaseModel):
    id: str
    type: ItemType
    prompt: str
    expected_answer: Optional[str] = None
    choices: Optional[List[str]] = None
    rubric: Optional[Dict[str, Any]] = None
    difficulty: float = Field(ge=1, le=5)
    skill_tag: str

class GradeResultModel(BaseModel):
    score: float
    errors: List[str]
    feedback_short: str
    feedback_long: str
    suggested_next_difficulty: float
