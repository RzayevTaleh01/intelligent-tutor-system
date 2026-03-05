from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models_diagnostics import ConceptNode, ConceptEdge

class ConceptGraph:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_edge(self, from_skill: str, to_skill: str, weight: float = 0.5):
        # Ensure nodes exist
        for skill in [from_skill, to_skill]:
            stmt = select(ConceptNode).where(ConceptNode.skill_tag == skill)
            res = await self.db.execute(stmt)
            node = res.scalar_one_or_none()
            if not node:
                self.db.add(ConceptNode(skill_tag=skill))
        
        # Check edge
        stmt = select(ConceptEdge).where(
            ConceptEdge.from_skill_tag == from_skill,
            ConceptEdge.to_skill_tag == to_skill
        )
        res = await self.db.execute(stmt)
        edge = res.scalar_one_or_none()
        
        if edge:
            edge.weight = weight
        else:
            edge = ConceptEdge(from_skill_tag=from_skill, to_skill_tag=to_skill, weight=weight)
            self.db.add(edge)
            
        await self.db.commit()

    async def get_neighbors(self, skill_tag: str) -> List[Dict[str, Any]]:
        # Outgoing edges (skills that depend on this one, or next steps)
        stmt = select(ConceptEdge).where(ConceptEdge.from_skill_tag == skill_tag)
        res = await self.db.execute(stmt)
        edges = res.scalars().all()
        return [{"skill": e.to_skill_tag, "weight": e.weight, "type": "outgoing"} for e in edges]

    async def get_prereqs(self, skill_tag: str) -> List[Dict[str, Any]]:
        # Incoming edges (prerequisites)
        stmt = select(ConceptEdge).where(ConceptEdge.to_skill_tag == skill_tag)
        res = await self.db.execute(stmt)
        edges = res.scalars().all()
        return [{"skill": e.from_skill_tag, "weight": e.weight, "type": "incoming"} for e in edges]

    async def get_all_nodes(self) -> List[str]:
        stmt = select(ConceptNode.skill_tag)
        res = await self.db.execute(stmt)
        return res.scalars().all()
