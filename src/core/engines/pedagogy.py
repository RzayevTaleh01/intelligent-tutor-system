from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import LearnerState
from src.core.runtime.cost_control import CostController
from src.core.adaptive.remediation import RemediationPlanner
from src.core.diagnostics.engine import CognitiveDiagnosticsEngine
from src.core.optimizer.bandit import BanditOptimizer
from src.core.experiments.ab import ABTestFramework
from src.core.explainability.why import WhyEngine
from src.core.adaptive.srs import SRSScheduler

class PedagogyEngine:
    def __init__(self):
        self.cost_controller = CostController()
        self.remediation_planner = RemediationPlanner()
        self.why_engine = WhyEngine()

    async def determine_next_step_async(
        self, 
        db: AsyncSession,
        session_id: str,
        state: LearnerState, 
        learner_skills: list[dict[str, Any]] = [], 
        recent_errors: list[dict[str, Any]] = [],
        course_id: str = "default"
    ) -> dict[str, Any]:
        """
        Async version with full Cognitive Diagnostics + Bandit + A/B
        """
        # 1. Get Components
        diagnostics_engine = CognitiveDiagnosticsEngine(db)
        bandit = BanditOptimizer(db)
        ab_test = ABTestFramework(db)
        srs = SRSScheduler(db)
        
        # 2. Get Data
        variant = await ab_test.get_variant(session_id)
        srs_due = await srs.get_due_skills(session_id)
        diag_report = await diagnostics_engine.get_report(session_id)
        
        # 3. Plan Remediation (Step 5 logic)
        remediation_plan = self.remediation_planner.plan_remediation(
            learner_skills, recent_errors, state.readiness_score
        )
        
        # 4. Generate Candidates
        candidates = []
        
        # Candidate A: Remediation/SRS focus
        if srs_due:
            candidates.append({"skill_tag": srs_due[0], "item_type": "mcq", "difficulty": 2, "source": "srs"})
            
        if remediation_plan["focus_skills"]:
            candidates.append({"skill_tag": remediation_plan["focus_skills"][0], "item_type": "vocab_fill", "difficulty": remediation_plan["difficulty_target"], "source": "remediation"})
            
        # Candidate B: Weakest Skill (Diagnostics)
        if diag_report["weakest_skills"]:
            weak_skill = diag_report["weakest_skills"][0]["skill"]
            candidates.append({"skill_tag": weak_skill, "item_type": "mcq", "difficulty": 1, "source": "diagnostics"})
            
        # Default Candidate (Dynamic based on Course)
        default_skill = f"general_{course_id}" if course_id != "default" else "general_knowledge"
        candidates.append({"skill_tag": default_skill, "item_type": "mixed", "difficulty": int(state.readiness_score * 4) + 1, "source": "default"})
        
        # 5. Select Action
        if variant == "B":
            # Bandit Preference
            chosen_action = await bandit.select_action(candidates)
        else:
            # Rule-based Preference (Remediation > SRS > Diagnostics > Default)
            chosen_action = candidates[0] # Simplification
            
        # 6. Explain
        explanation = self.why_engine.explain(
            chosen_action, diag_report, srs_due, remediation_plan, variant
        )
        
        return {
            "next_difficulty": chosen_action["difficulty"],
            "strategy": remediation_plan["strategy"],
            "remediation_plan": remediation_plan,
            "chosen_action": chosen_action,
            "why_this_plan": explanation,
            "variant": variant,
            "diagnostics": diag_report
        }

    def prepare_context(self, lesson_text: str, history: list[dict[str, str]]) -> dict[str, Any]:
        return self.cost_controller.optimize_context(history, lesson_text)
