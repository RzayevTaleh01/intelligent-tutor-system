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
    items: Optional[List[Dict[str, Any]]] = None

class LearningItem(BaseModel):
    id: str
    type: str # Simplified from Enum to str for flexibility
    question: str = Field(alias="prompt") # Map prompt to question
    correct_answer: Optional[str] = Field(None, alias="expected_answer")
    options: Optional[List[str]] = Field(None, alias="choices")
    difficulty: float = 0.5
    skill_tag: str = "general"

    class Config:
        populate_by_name = True

class GradeResult(BaseModel):
    score: float
    feedback_short: str
    error_codes: List[str] = []
    feedback_long: Optional[str] = None

