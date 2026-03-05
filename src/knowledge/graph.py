import networkx as nx
from typing import List, Dict, Any
from collections import Counter
import re
from src.knowledge.stopwords_en import STOPWORDS

class TopicGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def extract_keywords(self, text: str, top_k=5) -> List[str]:
        # Simple frequency-based extraction
        words = re.findall(r'\w+', text.lower())
        filtered = [w for w in words if w not in STOPWORDS and len(w) > 3]
        counts = Counter(filtered)
        return [w for w, c in counts.most_common(top_k)]

    def build_graph(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.graph.clear()
        
        # Add nodes
        chunk_keywords = {}
        for chunk in chunks:
            keywords = self.extract_keywords(chunk["text"])
            chunk_keywords[chunk["id"]] = keywords
            self.graph.add_node(chunk["id"], keywords=keywords)
            
        # Add edges based on overlap
        chunk_ids = list(chunk_keywords.keys())
        edges = []
        
        for i in range(len(chunk_ids)):
            for j in range(i + 1, len(chunk_ids)):
                id_a = chunk_ids[i]
                id_b = chunk_ids[j]
                
                kw_a = set(chunk_keywords[id_a])
                kw_b = set(chunk_keywords[id_b])
                
                overlap = len(kw_a.intersection(kw_b))
                if overlap >= 2:
                    weight = float(overlap)
                    self.graph.add_edge(id_a, id_b, weight=weight)
                    edges.append({
                        "from_chunk_id": id_a,
                        "to_chunk_id": id_b,
                        "weight": weight
                    })
                    
        return {
            "nodes": [{"chunk_id": nid, "keywords": attrs["keywords"]} for nid, attrs in self.graph.nodes(data=True)],
            "edges": edges
        }
