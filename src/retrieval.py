import os
import json
import faiss
import numpy as np
from typing import List, Dict
from src.models import Policy
from src.gemini import generate_embeddings

class PolicyRetriever:
    def __init__(self, policy: Policy):
        self.policy = policy
        self.index_path = "data/index/policy.index"
        self.mapping_path = "data/index/clause_mapping.json"
        self.index = None
        self.clause_mapping = []
        self._load_index()
        
    def _load_index(self):
        if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
            raise RuntimeError(
                f"Missing precomputed FAISS index or metadata. "
                f"Expected {self.index_path} and {self.mapping_path}. "
                f"Please run build_index.py to generate them."
            )
            
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path, "r") as f:
            self.clause_mapping = json.load(f)
        
    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves the top_k most relevant clauses/exclusions for the given query.
        Returns a formatted string of the retrieved clauses.
        """
        if self.index is None:
            return "No policy clauses available."
            
        query_emb = generate_embeddings([query])[0]
        query_np = np.array([query_emb]).astype("float32")
        
        distances, indices = self.index.search(query_np, top_k)
        
        retrieved_texts = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.clause_mapping):
                item = self.clause_mapping[idx]
                retrieved_texts.append(f"[{item['type'].upper()} - {item['title']}] {item['text']}")
                
        return "\n\n".join(retrieved_texts)
