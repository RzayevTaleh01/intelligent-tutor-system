from typing import Dict, Any, List
from src.plugins.english.models import GradeResult
from src.core.adaptive.error_taxonomy import ErrorTaxonomy

class EnglishGrader:
    def grade(self, item_id: str, attempt: str, correct_answer: str, item_type: str) -> GradeResult:
        # Simple heuristic grading
        attempt = attempt.strip().lower()
        correct = correct_answer.strip().lower()
        
        is_correct = attempt == correct
        score = 1.0 if is_correct else 0.0
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is: {correct_answer}"
        error_codes = []
        
        if not is_correct:
            # Map errors based on item type and attempt content
            if item_type == "mcq":
                error_codes.append(ErrorTaxonomy.WRONG_CHOICE)
            elif item_type == "vocab_fill":
                if attempt == "":
                    error_codes.append(ErrorTaxonomy.MISSING_KEYWORD)
                else:
                    error_codes.append(ErrorTaxonomy.SPELLING) # Simple assumption
            elif item_type == "rewrite_sentence":
                # Very basic check: length mismatch or missing key words
                correct_words = set(correct.split())
                attempt_words = set(attempt.split())
                missing = correct_words - attempt_words
                if missing:
                    error_codes.append(ErrorTaxonomy.MISSING_KEYWORD)
                else:
                    error_codes.append(ErrorTaxonomy.WORD_ORDER)
            elif item_type == "reading_qna":
                 if len(attempt) < 5:
                     error_codes.append(ErrorTaxonomy.INCOMPLETE)
                 else:
                     error_codes.append(ErrorTaxonomy.OFF_TOPIC)
            else:
                error_codes.append(ErrorTaxonomy.UNKNOWN)

        return GradeResult(
            score=score,
            feedback_short=feedback,
            error_codes=error_codes
        )
