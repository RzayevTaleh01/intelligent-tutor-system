import math
import random
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_diagnostics import BanditArm

class BanditOptimizer:
    def __init__(self, db: AsyncSession, policy="UCB1"):
        self.db = db
        self.policy = policy

    async def select_action(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Candidates: list of dicts with keys: skill_tag, item_type, difficulty
        """
        if not candidates:
            return None
            
        # Get arms for candidates
        arms = []
        for cand in candidates:
            key = f"{cand['skill_tag']}|{cand.get('item_type','any')}|{cand.get('difficulty',1)}"
            stmt = select(BanditArm).where(BanditArm.arm_key == key)
            res = await self.db.execute(stmt)
            arm = res.scalar_one_or_none()
            if not arm:
                # Create arm if new (lazy)
                arm = BanditArm(arm_key=key, pulls=0, reward_sum=0.0)
                self.db.add(arm)
                await self.db.commit() # Need ID/Persistence
                await self.db.refresh(arm)
            arms.append((cand, arm))
            
        # Select best arm
        best_cand = None
        best_score = -float('inf')
        total_pulls = sum([a.pulls for _, a in arms]) + 1
        
        for cand, arm in arms:
            if arm.pulls == 0:
                # Exploration bonus for unpulled arms
                score = float('inf')
            else:
                avg_reward = arm.reward_sum / arm.pulls
                if self.policy == "UCB1":
                    exploration = math.sqrt(2 * math.log(total_pulls) / arm.pulls)
                    score = avg_reward + exploration
                else:
                    score = avg_reward # Greedy fallback
            
            if score > best_score:
                best_score = score
                best_cand = cand
                
        return best_cand

    async def update_reward(self, skill_tag: str, item_type: str, difficulty: int, reward: float):
        key = f"{skill_tag}|{item_type}|{difficulty}"
        stmt = select(BanditArm).where(BanditArm.arm_key == key)
        res = await self.db.execute(stmt)
        arm = res.scalar_one_or_none()
        
        if arm:
            arm.pulls += 1
            arm.reward_sum += reward
            arm.reward_sq_sum += reward * reward
            await self.db.commit()
