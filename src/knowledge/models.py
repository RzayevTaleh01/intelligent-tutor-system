from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SourceResponse(BaseModel):
    source_id: str
    pages_or_chars: int
    chunks_created: int

class SearchResult(BaseModel):
    chunk_id: str
    score: float
    text_snippet: str
    position: int

class GraphNode(BaseModel):
    chunk_id: str
    keywords: List[str]

class GraphEdge(BaseModel):
    from_chunk_id: str
    to_chunk_id: str
    weight: float

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class LessonFromBookRequest(BaseModel):
    source_id: str
    level: str = "A2"
    focus: Optional[str] = None
