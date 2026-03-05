import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import torch

class EmbeddingService:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # Load model (lazy load in real prod, but eager here for simplicity)
        try:
            self.model = SentenceTransformer(model_name)
            self.dim = self.model.get_sentence_embedding_dimension()
            self.available = True
        except Exception as e:
            print(f"Embedding Model Error: {e}")
            self.available = False
            self.dim = 384 # Default for MiniLM

    def encode(self, texts: List[str]) -> List[np.ndarray]:
        if not self.available or not texts:
            return [np.zeros(self.dim, dtype=np.float32) for _ in texts]
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def cosine_similarity(self, vec_a: np.ndarray, matrix_b: np.ndarray) -> np.ndarray:
        # Cosine sim: dot(a, b) / (norm(a) * norm(b))
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(matrix_b, axis=1)
        
        dot_product = np.dot(matrix_b, vec_a)
        
        # Avoid division by zero
        if norm_a == 0:
            return np.zeros(len(matrix_b))
            
        sims = dot_product / (norm_a * norm_b + 1e-10)
        return sims
