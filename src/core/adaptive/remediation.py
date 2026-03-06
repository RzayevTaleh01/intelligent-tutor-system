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
        
        # 2. Identify Persistent Errors
        if recent_errors:
            top_error = recent_errors[0] # Assumed sorted by count
            plan["focus_errors"] = [top_error["code"]]
            
            # Strategy mapping based on error type - Simplified for generic domain
            # In a real system, this mapping should come from the plugin configuration
            if top_error["code"] in [ErrorTaxonomy.GRAMMAR_TENSE, ErrorTaxonomy.WORD_ORDER]:
                plan["strategy"] = "explain"
                plan["next_item_types"] = ["explanation", "practice_basic"]
            elif top_error["code"] in [ErrorTaxonomy.SPELLING, ErrorTaxonomy.MISSING_KEYWORD]:
                plan["strategy"] = "micro_quiz"
                plan["next_item_types"] = ["recall"]
            elif top_error["code"] == ErrorTaxonomy.WRONG_CHOICE:
                plan["strategy"] = "contrast_examples"
                plan["next_item_types"] = ["mcq"]
            else:
                plan["strategy"] = "review"
                plan["next_item_types"] = ["mixed"]
                
        # 3. Fallback if everything is good
        if not plan["focus_skills"] and not plan["focus_errors"]:
            plan["strategy"] = "advance"
            plan["difficulty_target"] = min(5, int(readiness * 5) + 1)
            
        return plan
