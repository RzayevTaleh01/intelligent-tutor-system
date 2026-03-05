import uuid
import time
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models_knowledge import KnowledgeSource, KnowledgeChunk, KnowledgeEmbedding, KnowledgeEdge, KnowledgeTopic
from src.knowledge.chunker import Chunker
from src.knowledge.embeddings import EmbeddingService
from src.knowledge.graph import TopicGraph

class KnowledgeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = Chunker()
        self.embedder = EmbeddingService()
        self.graph_builder = TopicGraph()

    async def ingest_file(self, filename: str, content: bytes, source_id: str = None) -> Dict[str, Any]:
        if not source_id:
            source_id = str(uuid.uuid4())
            
        # 1. Chunking
        processed = self.chunker.process_file(content, filename)
        chunks_data = processed["chunks"]
        
        # 2. Save Source
        source = KnowledgeSource(
            id=source_id,
            filename=filename,
            filetype=filename.split('.')[-1],
            created_at=time.time()
        )
        self.db.add(source)
        
        # 3. Save Chunks & Compute Embeddings
        chunk_objs = []
        emb_objs = []
        texts = [c["text"] for c in chunks_data]
        vectors = self.embedder.encode(texts)
        
        for i, chunk in enumerate(chunks_data):
            chunk_obj = KnowledgeChunk(
                id=chunk["id"],
                source_id=source_id,
                position=chunk["position"],
                text=chunk["text"],
                meta_json=chunk["meta"]
            )
            chunk_objs.append(chunk_obj)
            
            # Embeddings stored as bytes
            vec_bytes = vectors[i].astype(np.float32).tobytes()
            emb_obj = KnowledgeEmbedding(
                chunk_id=chunk["id"],
                vector=vec_bytes,
                dim=self.embedder.dim
            )
            emb_objs.append(emb_obj)
            
        self.db.add_all(chunk_objs)
        self.db.add_all(emb_objs)
        
        # 4. Build Graph (Topics & Edges)
        graph_data = self.graph_builder.build_graph(chunks_data)
        
        edge_objs = []
        for edge in graph_data["edges"]:
            edge_objs.append(KnowledgeEdge(
                id=str(uuid.uuid4()),
                source_id=source_id,
                from_chunk_id=edge["from_chunk_id"],
                to_chunk_id=edge["to_chunk_id"],
                weight=edge["weight"]
            ))
        self.db.add_all(edge_objs)
        
        await self.db.commit()
        
        return {
            "source_id": source_id,
            "pages_or_chars": processed["text_len"],
            "chunks_created": len(chunks_data)
        }

    async def search(self, source_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # 1. Encode Query
        query_vec = self.embedder.encode([query])[0]
        
        # 2. Load all embeddings for source (Naive in-memory search for now)
        # In prod: use pgvector or separate vector DB
        stmt = select(KnowledgeEmbedding).join(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id)
        result = await self.db.execute(stmt)
        embeddings = result.scalars().all()
        
        if not embeddings:
            return []
            
        # Prepare matrix
        ids = [e.chunk_id for e in embeddings]
        matrix = np.array([np.frombuffer(e.vector, dtype=np.float32) for e in embeddings])
        
        # 3. Compute Similarity
        scores = self.embedder.cosine_similarity(query_vec, matrix)
        
        # 4. Top K
        top_indices = np.argsort(scores)[::-1][:k]
        
        top_chunks = []
        for idx in top_indices:
            chunk_id = ids[idx]
            score = float(scores[idx])
            
            # Fetch text
            c_res = await self.db.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id))
            chunk = c_res.scalar_one()
            
            top_chunks.append({
                "chunk_id": chunk.id,
                "score": score,
                "text_snippet": chunk.text[:200] + "...",
                "full_text": chunk.text,
                "position": chunk.position
            })
            
        return top_chunks

    async def get_graph(self, source_id: str) -> Dict[str, Any]:
        # Fetch edges
        stmt = select(KnowledgeEdge).where(KnowledgeEdge.source_id == source_id)
        result = await self.db.execute(stmt)
        edges = result.scalars().all()
        
        # Fetch chunks to get keywords (re-extract or store keywords in DB? Re-extracting for now to save DB schema complexity)
        stmt_c = select(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id)
        res_c = await self.db.execute(stmt_c)
        chunks = res_c.scalars().all()
        
        nodes = []
        for c in chunks:
            kw = self.graph_builder.extract_keywords(c.text)
            nodes.append({"chunk_id": c.id, "keywords": kw})
            
        return {
            "nodes": nodes,
            "edges": [{"from_chunk_id": e.from_chunk_id, "to_chunk_id": e.to_chunk_id, "weight": e.weight} for e in edges]
        }
