import faiss
import numpy as np
from typing import List, Dict
from src.models import Policy
from src.gemini import generate_embeddings

class PolicyRetriever:
    def __init__(self, policy: Policy):
        self.policy = policy
        self.index = None
        self.clause_mapping = []  # Maps index back to clause
        self._build_index()
        
    def _build_index(self):
        # We only embed clauses and exclusions since the rest is handled by deterministic rules
        texts_to_embed = []
        
        for clause in self.policy.clauses:
            text = f"CLAUSE: {clause.title}\n{clause.text}"
            texts_to_embed.append(text)
            self.clause_mapping.append({"type": "clause", "id": clause.id, "title": clause.title, "text": clause.text})
            
        for exclusion in self.policy.exclusions:
            text = f"EXCLUSION: {exclusion.title}\n{exclusion.text}"
            texts_to_embed.append(text)
            self.clause_mapping.append({"type": "exclusion", "id": exclusion.id, "title": exclusion.title, "text": exclusion.text})
            
        if not texts_to_embed:
            return
            
        # Get embeddings from Gemini
        embeddings = generate_embeddings(texts_to_embed)
        
        # Build FAISS index
        embed_dim = len(embeddings[0])
        self.index = faiss.IndexFlatL2(embed_dim)
        
        # Convert to float32 numpy array for FAISS
        embeddings_np = np.array(embeddings).astype("float32")
        self.index.add(embeddings_np)
        
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
