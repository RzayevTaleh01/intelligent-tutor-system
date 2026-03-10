from typing import Any
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import LearnerState
from src.core.runtime.cost_control import CostController
from src.core.adaptive.remediation import RemediationPlanner
from src.core.diagnostics.engine import CognitiveDiagnosticsEngine
from src.core.optimizer.bandit import BanditOptimizer
from src.core.experiments.ab import ABTestFramework
from src.core.explainability.why import WhyEngine
from src.core.adaptive.srs import SRSScheduler
from src.core.adaptive.rl.agent import RLAgent

class PedagogyEngine:
    def __init__(self):
        self.cost_controller = CostController()
        self.remediation_planner = RemediationPlanner()
        self.why_engine = WhyEngine()
        # Initialize RL Agent (Load pre-trained model)
        self.rl_agent = RLAgent(training_mode=False)

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
        Async version with full Cognitive Diagnostics + Bandit + RL + A/B
        """
        # 1. Get Components
        diagnostics_engine = CognitiveDiagnosticsEngine(db)
        bandit = BanditOptimizer(db)
        ab_test = ABTestFramework(db)
        srs = SRSScheduler(db)
        
        # 2. Get Data
        # For demo purposes, we can force RL or let A/B decide
        # variant = await ab_test.get_variant(session_id) 
        variant = "RL" # Force RL for this implementation phase
        
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
        
        # Default difficulty base
        base_difficulty = int(state.readiness_score * 4) + 1
        candidates.append({"skill_tag": default_skill, "item_type": "mixed", "difficulty": base_difficulty, "source": "default"})
        
        # 5. Select Action
        chosen_action = None
        rl_info = {}

        if variant == "RL":
            # --- RL Agent Logic ---
            # Construct Observation: [mastery, last_correct, difficulty_norm, errors_norm, fatigue]
            last_correct = 1 if (not recent_errors or len(recent_errors) == 0) else 0
            # Estimate current difficulty from last action or state (simplified)
            current_diff_norm = base_difficulty / 5.0 
            errors_norm = min(1.0, len(recent_errors) / 5.0)
            
            obs = np.array([
                state.mastery_score,
                float(last_correct),
                current_diff_norm,
                errors_norm,
                0.0 # Fatigue placeholder
            ], dtype=np.float32)
            
            # Predict Action: 0=Easier, 1=Same, 2=Harder
            action_idx = self.rl_agent.predict(obs)
            
            target_diff = base_difficulty
            if action_idx == 0:
                target_diff = max(1, base_difficulty - 1)
                strategy_desc = "RL: Decrease Difficulty"
            elif action_idx == 2:
                target_diff = min(5, base_difficulty + 1)
                strategy_desc = "RL: Increase Difficulty"
            else:
                strategy_desc = "RL: Maintain Difficulty"
                
            rl_info = {"action": action_idx, "desc": strategy_desc}
            
            # Filter candidates matching target difficulty
            matching_candidates = [c for c in candidates if c.get("difficulty") == target_diff]
            
            if matching_candidates:
                chosen_action = matching_candidates[0]
            else:
                # If no exact match, modify the default candidate
                fallback = candidates[-1].copy()
                fallback["difficulty"] = target_diff
                fallback["source"] = "rl_adjusted_default"
                chosen_action = fallback

        elif variant == "B":
            # Bandit Preference
            chosen_action = await bandit.select_action(candidates)
        else:
            # Rule-based Preference (Remediation > SRS > Diagnostics > Default)
            chosen_action = candidates[0] # Simplification
            
        # 6. Explain
        explanation = self.why_engine.explain(
            chosen_action, diag_report, srs_due, remediation_plan, variant
        )
        
        if variant == "RL":
            explanation += f" (RL Agent decided to {rl_info['desc']})"
        
        return {
            "next_difficulty": chosen_action["difficulty"],
            "strategy": remediation_plan["strategy"],
            "remediation_plan": remediation_plan,
            "chosen_action": chosen_action,
            "why_this_plan": explanation,
            "variant": variant,
            "diagnostics": diag_report,
            "rl_info": rl_info
        }

    def prepare_context(self, lesson_text: str, history: list[dict[str, str]]) -> dict[str, Any]:
        return self.cost_controller.optimize_context(history, lesson_text)
