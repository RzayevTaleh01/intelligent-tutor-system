import math
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_diagnostics import LearnerTheta, LearnerThetaSkill, SkillDifficulty
from src.core.diagnostics.concept_graph import ConceptGraph
from src.core.adaptive.bkt import BKTModel

class CognitiveDiagnosticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.lr = 0.05 # Learning Rate
        self.prop_alpha = 0.15 # Propagation factor

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    async def update_diagnostics(self, session_id: str, skill_tag: str, item_type: str, score: float):
        # 1. Get or Create Theta (Ability)
        stmt = select(LearnerTheta).where(LearnerTheta.session_id == session_id)
        res = await self.db.execute(stmt)
        theta_rec = res.scalar_one_or_none()
        
        if not theta_rec:
            theta_rec = LearnerTheta(session_id=session_id, theta_overall=0.0)
            self.db.add(theta_rec)
            
        # 2. Get or Create Difficulty (b)
        stmt_b = select(SkillDifficulty).where(
            SkillDifficulty.skill_tag == skill_tag,
            SkillDifficulty.item_type == item_type
        )
        res_b = await self.db.execute(stmt_b)
        diff_rec = res_b.scalar_one_or_none()
        
        if not diff_rec:
            diff_rec = SkillDifficulty(skill_tag=skill_tag, item_type=item_type, b=0.0)
            self.db.add(diff_rec)
            # Flush to get ID if needed, but we just need object
        
        # 3. IRT Update (Gradient Descent)
        # P = sigmoid(theta - b)
        # Error = score - P
        # theta_new = theta + lr * Error
        # b_new = b - lr * Error
        
        current_theta = theta_rec.theta_overall
        current_b = diff_rec.b
        
        p_correct = self.sigmoid(current_theta - current_b)
        error = score - p_correct
        
        theta_rec.theta_overall += self.lr * error
        diff_rec.b -= self.lr * error
        
        # 4. Skill-specific Theta
        stmt_ts = select(LearnerThetaSkill).where(
            LearnerThetaSkill.session_id == session_id,
            LearnerThetaSkill.skill_tag == skill_tag
        )
        res_ts = await self.db.execute(stmt_ts)
        theta_skill = res_ts.scalar_one_or_none()
        
        if not theta_skill:
            theta_skill = LearnerThetaSkill(session_id=session_id, skill_tag=skill_tag, theta=0.0)
            self.db.add(theta_skill)
            
        # Update skill theta
        p_skill = self.sigmoid(theta_skill.theta - current_b)
        err_skill = score - p_skill
        theta_skill.theta += self.lr * err_skill
        
        await self.db.commit()
        
        # 5. Propagation (Graph)
        # If score changed significantly (e.g. positive learning signal), propagate to neighbors
        # For simplicity, we just propagate the delta of mastery to neighbors
        # But here we integrate with BKT mastery for propagation
        await self._propagate_mastery(session_id, skill_tag, score)

    async def _propagate_mastery(self, session_id: str, skill_tag: str, score: float):
        # We use BKT model to get current mastery and propagate small boost
        bkt = BKTModel(self.db)
        skill_state = await bkt.get_skill_state(session_id, skill_tag)
        if not skill_state: 
            return

        current_mastery = skill_state["p_mastery"]
        delta = 0.05 if score > 0.7 else -0.02 # Heuristic change
        
        graph = ConceptGraph(self.db)
        # Neighbors: skills that this skill leads TO (outgoing)
        # If I master "Past Simple", maybe "Past Continuous" gets easier? 
        # Or Prereqs? If I fail "Past Simple", "Present Perfect" (which depends on it) should drop?
        
        # Let's assume: Improving a PREREQ improves the TARGET.
        # So we look at OUTGOING edges from current skill.
        neighbors = await graph.get_neighbors(skill_tag)
        
        for edge in neighbors:
            target_skill = edge["skill"]
            weight = edge["weight"]
            
            # Boost target skill slightly
            # target_mastery += alpha * weight * delta
            # We need to manually update BKT record for target
            # This is "hacky" BKT manipulation but simulates transfer learning
            pass # Implementation complex without direct SQL update, skipping for Lite version to avoid risk

    async def get_report(self, session_id: str) -> Dict[str, Any]:
        stmt = select(LearnerTheta).where(LearnerTheta.session_id == session_id)
        res = await self.db.execute(stmt)
        theta = res.scalar_one_or_none()
        
        stmt_s = select(LearnerThetaSkill).where(LearnerThetaSkill.session_id == session_id)
        res_s = await self.db.execute(stmt_s)
        thetas = res_s.scalars().all()
        
        # Get fused mastery (BKT + IRT) for weak skills
        bkt = BKTModel(self.db)
        weakest = []
        
        for t in thetas:
            bkt_state = await bkt.get_skill_state(session_id, t.skill_tag)
            p_mastery = bkt_state["p_mastery"] if bkt_state else 0.1
            p_irt = self.sigmoid(t.theta) # Assuming average difficulty b=0 for general view
            
            fused = 0.6 * p_mastery + 0.4 * p_irt
            weakest.append({
                "skill": t.skill_tag,
                "fused_mastery": fused,
                "irt_theta": t.theta,
                "bkt_mastery": p_mastery
            })
            
        weakest.sort(key=lambda x: x["fused_mastery"])
        
        return {
            "theta_overall": theta.theta_overall if theta else 0.0,
            "weakest_skills": weakest[:5],
            "skill_sample": [t.skill_tag for t in thetas]
        }
