from typing import Dict, Any
from src.db.models import LearnerState

class PedagogyEngine:
    def determine_next_step(self, state: LearnerState) -> Dict[str, Any]:
        """
        Decides the next pedagogical step based on learner state.
        Policy:
        - Mastery < 0.6: Easy task
        - Mastery 0.6 - 0.8: Medium task
        - Mastery > 0.8: Challenge
        """
        mastery = state.mastery_score
        
        if mastery < 0.6:
            difficulty = "easy"
            strategy = "reinforcement"
        elif mastery < 0.8:
            difficulty = "medium"
            strategy = "practice"
        else:
            difficulty = "hard"
            strategy = "challenge"
            
        return {
            "next_difficulty": difficulty,
            "strategy": strategy,
            "target_mastery": mastery,
            "rationale": f"Current mastery is {mastery:.2f}, triggering {difficulty} content."
        }
