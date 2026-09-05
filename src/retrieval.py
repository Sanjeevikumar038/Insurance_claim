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
        
    def _lexical_search(self, query: str, top_k: int) -> str:
        import re
        words = re.findall(r'\b\w+\b', query.lower())
        query_terms = set(word for word in words if len(word) > 2 and word not in {'the', 'and', 'for', 'with', 'that', 'this', 'was', 'not', 'are'})
        
        # Add basic synonym expansion for robust fallback matching
        synonyms = {
            "ignition": ["keys", "vehicle"],
            "alcohol": ["drunk", "intoxicating", "liquor"],
            "bac": ["drunk", "intoxicating"],
            "intoxicated": ["intoxicating", "drunk"],
            "collision": ["accident", "damage"],
            "reported": ["window", "days"],
            "idv": ["value"],
            "window": ["days", "reported"]
        }
        
        expanded_terms = set(query_terms)
        for term in query_terms:
            if term in synonyms:
                expanded_terms.update(synonyms[term])
                
        scores = []
        for i, item in enumerate(self.clause_mapping):
            score = 0
            text_to_search = (item['title'] + " " + item['text']).lower()
            
            for term in expanded_terms:
                score += text_to_search.count(term)
                
            scores.append((score, i))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        
        retrieved_texts = []
        for score, idx in scores[:top_k]:
            item = self.clause_mapping[idx]
            retrieved_texts.append(f"[{item['type'].upper()} - {item['title']}] {item['text']}")
            
        return "\n\n".join(retrieved_texts)
        
    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves the top_k most relevant clauses/exclusions for the given query.
        Returns a formatted string of the retrieved clauses.
        """
        if self.index is None:
            return "No policy clauses available."
            
        try:
            query_emb = generate_embeddings([query])[0]
            query_np = np.array([query_emb]).astype("float32")
            
            distances, indices = self.index.search(query_np, top_k)
            
            retrieved_texts = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.clause_mapping):
                    item = self.clause_mapping[idx]
                    retrieved_texts.append(f"[{item['type'].upper()} - {item['title']}] {item['text']}")
                    
            print("retrieval_method = 'faiss_embedding'")
            return "\n\n".join(retrieved_texts)
            
        except Exception as e:
            print(f"Embedding API failed ({str(e)}), falling back to lexical search.")
            print("retrieval_method = 'lexical_fallback'")
            return self._lexical_search(query, top_k)
