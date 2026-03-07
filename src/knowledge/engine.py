import uuid
import time
import asyncio
import numpy as np
from typing import Any, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import ARRAY

from src.db.models_knowledge import KnowledgeSource, KnowledgeChunk, KnowledgeEmbedding, KnowledgeEdge
from src.knowledge.chunker import Chunker
from src.knowledge.embeddings import EmbeddingService
from src.knowledge.graph import TopicGraph
from src.config import get_settings

settings = get_settings()

class KnowledgeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = Chunker()
        self.embedder = EmbeddingService()
        self.graph_builder = TopicGraph()

    async def ingest_text(self, text: str, filename: str, course_id: str | None = None) -> dict[str, Any]:
        """Ingest raw text directly."""
        return await self.ingest_file(filename, text.encode("utf-8"), course_id=course_id)

    async def search(self, course_id: str, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        """Search for relevant chunks using vector similarity."""
        query_vector = self.embedder.encode([query])[0]
        # PGVector search query
        stmt = select(KnowledgeChunk).join(KnowledgeEmbedding).order_by(
            KnowledgeEmbedding.vector.l2_distance(query_vector)
        ).limit(limit)
        
        # Filter by course_id if needed (requires join with KnowledgeSource)
        if course_id:
            stmt = stmt.join(KnowledgeSource).where(KnowledgeSource.course_id == course_id)
            
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def ingest_file(
        self, 
        filename: str, 
        content: bytes, 
        source_id: str | None = None, 
        course_id: str | None = None
    ) -> dict[str, Any]:
        
        if not source_id:
            source_id = str(uuid.uuid4())
            
        # 1. Chunking (Run in thread pool to avoid blocking event loop)
        processed = await asyncio.to_thread(self.chunker.process_file, content, filename)
        chunks_data = processed["chunks"]
        
        # 2. Save Source Metadata
        source = KnowledgeSource(
            id=source_id,
            course_id=course_id,
            filename=filename,
            filetype=filename.split('.')[-1],
            created_at=time.time()
        )
        self.db.add(source)
        
        # 3. Compute Embeddings (Run in thread pool)
        texts = [c["text"] for c in chunks_data]
        vectors = await asyncio.to_thread(self.embedder.encode, texts)
        
        chunk_objs = []
        
        # 4. Create Chunk Objects with Vector Embedding
        # Using pgvector, we store the vector directly in the KnowledgeChunk table if schema supports it,
        # or in a separate table. Assuming standard pgvector usage here.
        
        for i, chunk in enumerate(chunks_data):
            # Convert numpy array to list for pgvector compatibility
            embedding_list = vectors[i].tolist() if hasattr(vectors[i], 'tolist') else vectors[i]
            
            chunk_obj = KnowledgeChunk(
                id=chunk["id"],
                source_id=source_id,
                position=chunk["position"],
                text=chunk["text"],
                meta_json=chunk["meta"],
                # Assuming KnowledgeChunk has an 'embedding' column of type Vector(768)
                # If using separate table, logic would differ slightly.
                # Here we stick to the provided schema but optimized.
            )
            chunk_objs.append(chunk_obj)
            
            # If using separate table for embeddings as in original code:
            emb_obj = KnowledgeEmbedding(
                chunk_id=chunk["id"],
                # PGVector expects a list/array, not raw bytes, for semantic search queries
                # But if the column is defined as BYTEA, we use bytes. 
                # If defined as Vector, we use list. 
                # Original code used bytes, implying generic storage. 
                # We will upgrade this to proper pgvector usage in SQL.
                vector=vectors[i].astype(np.float32).tobytes(), 
                dim=self.embedder.dim
            )
            self.db.add(emb_obj)
            
        self.db.add_all(chunk_objs)
        
        # 5. Build Graph (Run in thread pool)
        graph_data = await asyncio.to_thread(self.graph_builder.build_graph, chunks_data)
        
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

    async def search(
        self, 
        query: str, 
        course_id: str | None = None, 
        source_id: str | None = None, 
        k: int = settings.VECTOR_SEARCH_LIMIT
    ) -> list[dict[str, Any]]:
        """
        Optimized vector search. 
        Instead of loading all vectors into memory (O(N)), 
        we should use the database's vector index (pgvector) (O(logN)).
        """
        
        # 1. Encode Query
        query_vec = await asyncio.to_thread(self.embedder.encode, [query])
        query_vec = query_vec[0]
        
        # Optimized for pgvector: ORDER BY embedding <-> query_vec LIMIT k
        # Since the current schema seems to use a separate KnowledgeEmbedding table with raw bytes,
        # we still have to do in-memory comparison UNLESS we migrate to pgvector type.
        # For now, we will implement the "Toy Mode" fix: 
        # Only fetch vectors from the specific course/source to reduce memory footprint.
        
        stmt = select(KnowledgeEmbedding).join(KnowledgeChunk).join(KnowledgeSource)
        
        if course_id:
            stmt = stmt.where(KnowledgeSource.course_id == course_id)
        elif source_id:
            stmt = stmt.where(KnowledgeSource.id == source_id)
        else:
            return [] 
            
        result = await self.db.execute(stmt)
        embeddings = result.scalars().all()
        
        if not embeddings:
            return []
            
        # In-memory cosine similarity (Legacy method - pending PGVector migration)
        # This is now non-blocking thanks to thread pool if we wrap it, 
        # but for small datasets (<10k chunks) numpy is fast enough.
        
        ids = [e.chunk_id for e in embeddings]
        # Faster numpy construction
        matrix = np.frombuffer(b''.join([e.vector for e in embeddings]), dtype=np.float32).reshape(len(embeddings), -1)
        
        scores = self.embedder.cosine_similarity(query_vec, matrix)
        
        # Top K
        # Use argpartition for O(N) instead of argsort O(NlogN)
        k = min(k, len(scores))
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]] # Sort top k
        
        top_chunk_ids = [ids[idx] for idx in top_indices]
        
        # Fetch chunk details in a single query
        chunk_stmt = select(KnowledgeChunk).where(KnowledgeChunk.id.in_(top_chunk_ids))
        chunk_res = await self.db.execute(chunk_stmt)
        chunks_map = {c.id: c for c in chunk_res.scalars().all()}
        
        results = []
        for idx in top_indices:
            chunk_id = ids[idx]
            if chunk_id in chunks_map:
                chunk = chunks_map[chunk_id]
                results.append({
                    "chunk_id": chunk.id,
                    "score": float(scores[idx]),
                    "text_snippet": chunk.text[:200] + "...",
                    "full_text": chunk.text,
                    "position": chunk.position,
                    "meta": chunk.meta_json
                })
                
        return results

    async def get_graph(self, source_id: str) -> dict[str, Any]:
        # Fetch edges
        stmt = select(KnowledgeEdge).where(KnowledgeEdge.source_id == source_id)
        result = await self.db.execute(stmt)
        edges = result.scalars().all()
        
        # Fetch chunks
        stmt_c = select(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id)
        res_c = await self.db.execute(stmt_c)
        chunks = res_c.scalars().all()
        
        # Extract keywords (Async optimization)
        async def extract_keywords_safe(text_content):
             return await asyncio.to_thread(self.graph_builder.extract_keywords, text_content)

        # Process nodes in parallel batches if needed, or simple loop with await
        nodes = []
        for c in chunks:
            # For now, re-extracting is expensive. Ideally, keywords should be stored in KnowledgeChunk.meta_json
            # Fallback to metadata if available
            kw = c.meta_json.get("keywords") if c.meta_json else []
            if not kw:
                 kw = await extract_keywords_safe(c.text)
            
            nodes.append({"chunk_id": c.id, "keywords": kw})
            
        return {
            "nodes": nodes,
            "edges": [{"from_chunk_id": e.from_chunk_id, "to_chunk_id": e.to_chunk_id, "weight": e.weight} for e in edges]
        }
