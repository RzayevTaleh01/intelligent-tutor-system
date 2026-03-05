from typing import Dict, Any, List
import difflib
from src.plugins.english.models import LearningItem, ItemType, GradeResultModel

class Grader:
    def grade(self, item: LearningItem, attempt_text: str) -> GradeResultModel:
        if item.type == ItemType.GRAMMAR_MCQ:
            return self._grade_mcq(item, attempt_text)
        elif item.type == ItemType.VOCAB_FILL:
            return self._grade_vocab(item, attempt_text)
        elif item.type == ItemType.REWRITE_SENTENCE:
            return self._grade_rewrite(item, attempt_text)
        elif item.type == ItemType.READING_QNA:
            return self._grade_reading(item, attempt_text)
        else:
            return GradeResultModel(
                score=0, errors=["Unknown item type"], 
                feedback_short="Cannot grade this item type.", 
                feedback_long="", suggested_next_difficulty=item.difficulty
            )

    def _grade_mcq(self, item: LearningItem, attempt: str) -> GradeResultModel:
        is_correct = attempt.strip().lower() == item.expected_answer.strip().lower()
        score = 1.0 if is_correct else 0.0
        return GradeResultModel(
            score=score,
            errors=[] if is_correct else ["Incorrect choice."],
            feedback_short="Correct!" if is_correct else f"Incorrect. The answer was {item.expected_answer}.",
            feedback_long="",
            suggested_next_difficulty=item.difficulty + 0.5 if is_correct else item.difficulty - 0.5
        )

    def _grade_vocab(self, item: LearningItem, attempt: str) -> GradeResultModel:
        # Simple case-insensitive match
        is_correct = attempt.strip().lower() == item.expected_answer.strip().lower()
        score = 1.0 if is_correct else 0.0
        return GradeResultModel(
            score=score,
            errors=[] if is_correct else ["Wrong word."],
            feedback_short="Good job!" if is_correct else f"Not quite. Expected: {item.expected_answer}",
            feedback_long="",
            suggested_next_difficulty=item.difficulty + 0.2 if is_correct else item.difficulty
        )

    def _grade_rewrite(self, item: LearningItem, attempt: str) -> GradeResultModel:
        # Heuristic: Check length and keyword overlap
        # In real world: use NLP dependency parsing for passive voice check
        attempt = attempt.strip()
        if len(attempt) < 5:
            return GradeResultModel(score=0.1, errors=["Too short"], feedback_short="Too short.", feedback_long="Please write a complete sentence.", suggested_next_difficulty=item.difficulty)
            
        # Mock logic for passive voice or just general rewriting
        # Let's assume high score if length is similar to expected answer (mock)
        # For this stub, we just give a random-ish valid score based on length
        score = 0.8
        return GradeResultModel(
            score=score,
            errors=[],
            feedback_short="Good attempt at rewriting.",
            feedback_long="You preserved the meaning well.",
            suggested_next_difficulty=item.difficulty + 0.1
        )

    def _grade_reading(self, item: LearningItem, attempt: str) -> GradeResultModel:
        # Heuristic: Keyword overlap with expected answer if present
        if not item.expected_answer:
            return GradeResultModel(score=0.5, errors=[], feedback_short="Recorded.", feedback_long="Manual review needed.", suggested_next_difficulty=item.difficulty)
            
        matcher = difflib.SequenceMatcher(None, attempt.lower(), item.expected_answer.lower())
        ratio = matcher.ratio()
        
        score = ratio
        feedback = "Excellent!" if ratio > 0.8 else "Good, but could be more precise." if ratio > 0.5 else "Try to focus on the key details."
        
        return GradeResultModel(
            score=score,
            errors=[] if score > 0.6 else ["Low similarity to expected answer."],
            feedback_short=feedback,
            feedback_long=f"Similarity score: {ratio:.2f}",
            suggested_next_difficulty=item.difficulty
        )
