from typing import Dict, Any, List

class WhyEngine:
    def explain(
        self, 
        chosen_action: Dict[str, Any], 
        diagnostics: Dict[str, Any], 
        srs_due: List[str], 
        remediation: Dict[str, Any],
        variant: str = "A"
    ) -> str:
        
        reasons = []
        skill = chosen_action.get("skill_tag", "general")
        
        # 1. Check SRS
        if skill in srs_due:
            reasons.append(f"It's time to review '{skill}' based on spaced repetition schedule.")
            
        # 2. Check Remediation
        if remediation.get("focus_skills") and skill in remediation["focus_skills"]:
            reasons.append(f"Detected weakness in '{skill}', prioritizing practice.")
        elif remediation.get("focus_errors"):
            reasons.append(f"Targeting recent error pattern: {remediation['focus_errors'][0]}.")
            
        # 3. Check Bandit/Experiment
        if variant == "B":
            reasons.append("AI Optimizer (Bandit) selected this as the most effective path.")
            
        # 4. Fallback
        if not reasons:
            reasons.append("Standard curriculum progression.")
            
        return " ".join(reasons)
