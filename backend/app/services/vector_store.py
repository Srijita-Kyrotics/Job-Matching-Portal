import json
import math
import numpy as np
import faiss
from typing import List, Optional, Tuple

def serialize_embedding(embedding: List[float]) -> str:
    return json.dumps(embedding)

def deserialize_embedding(value: Optional[str]) -> Optional[List[float]]:
    if value is None:
        return None
    return json.loads(value)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

class FAISSStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension) # Inner product for cosine sim (requires L2 normalization)
        self.job_ids: List[int] = []
        
    def add_embeddings(self, job_ids: List[int], embeddings: List[List[float]]):
        if not embeddings:
            return
        
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.job_ids.extend(job_ids)
        
    def search(self, query_embedding: List[float], k: int = 100) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []
            
        q_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(q_vec)
        
        distances, indices = self.index.search(q_vec, min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.job_ids):
                results.append((self.job_ids[idx], float(dist)))
        return results
