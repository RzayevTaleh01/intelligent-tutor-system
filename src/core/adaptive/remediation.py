from typing import List, Dict, Any
from src.core.adaptive.error_taxonomy import ErrorTaxonomy

class RemediationPlanner:
    def plan_remediation(
        self, 
        learner_skills: List[Dict[str, Any]], 
        recent_errors: List[Dict[str, Any]], 
        readiness: float
    ) -> Dict[str, Any]:
        """
        Generates a remediation plan based on BKT state and Error History.
        """
        
        plan = {
            "focus_skills": [],
            "focus_errors": [],
            "strategy": "practice",
            "difficulty_target": 1,
            "next_item_types": []
        }
        
        # 1. Identify Weak Skills (Low Mastery)
        weak_skills = [s for s in learner_skills if s.get("p_mastery", 0) < 0.4]
        if weak_skills:
            # Sort by lowest mastery
            weak_skills.sort(key=lambda x: x.get("p_mastery", 0))
            plan["focus_skills"] = [s["skill_tag"] for s in weak_skills[:2]]
            plan["strategy"] = "drill"
            plan["difficulty_target"] = max(1, int(readiness * 5) - 1)
        
        # 2. Identify Persistent Errors & Adapt Strategy
        if recent_errors:
            top_error = recent_errors[0] # Assumed sorted by count (most frequent)
            plan["focus_errors"] = [top_error["code"]]
            error_count = top_error.get("count", 1)
            
            # SCAFFOLDING: If the student is stuck (multiple errors on same concept)
            if error_count >= 2:
                plan["strategy"] = "scaffolding"
                plan["next_item_types"] = ["breakdown_step_by_step", "hint"]
                plan["difficulty_target"] = max(1, plan["difficulty_target"] - 1)
            
            # FEYNMAN: If error is conceptual (WRONG_CHOICE, LOGIC)
            elif top_error["code"] in [ErrorTaxonomy.WRONG_CHOICE, "concept_error"]:
                plan["strategy"] = "feynman"
                plan["next_item_types"] = ["explain_in_own_words"]
                
            # SOCRATIC: If error is minor or student is advanced enough to self-correct
            elif readiness > 0.6 and top_error["code"] in [ErrorTaxonomy.GRAMMAR_TENSE, ErrorTaxonomy.WORD_ORDER]:
                plan["strategy"] = "socratic"
                plan["next_item_types"] = ["guided_question"]
                
            # DEFAULT REMEDIATION
            elif top_error["code"] in [ErrorTaxonomy.SPELLING, ErrorTaxonomy.MISSING_KEYWORD]:
                plan["strategy"] = "micro_quiz"
                plan["next_item_types"] = ["recall"]
            else:
                plan["strategy"] = "review"
                plan["next_item_types"] = ["mixed"]
                
        # 3. Fallback / Advancement Strategy
        if not plan["focus_skills"] and not plan["focus_errors"]:
            plan["strategy"] = "advance"
            plan["difficulty_target"] = min(5, int(readiness * 5) + 1)
            
            # High Readiness -> Challenge with Socratic Method
            if readiness > 0.8:
                plan["strategy"] = "socratic_challenge"
            
        return plan
