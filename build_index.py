import os
import json
import faiss
import numpy as np
from src.models import Policy
from src.gemini import generate_embeddings
from dotenv import load_dotenv

def build_offline_index():
    load_dotenv()
    
    # Load policy
    policy_path = "data/policy/POL-2026.json"
    if not os.path.exists(policy_path):
        print(f"Error: Policy file not found at {policy_path}")
        return
        
    with open(policy_path, "r") as f:
        data = json.load(f)
        policy = Policy(**data)
        
    texts_to_embed = []
    clause_mapping = []
    
    for clause in policy.clauses:
        text = f"CLAUSE: {clause.title}\n{clause.text}"
        texts_to_embed.append(text)
        clause_mapping.append({"type": "clause", "id": clause.id, "title": clause.title, "text": clause.text})
        
    for exclusion in policy.exclusions:
        text = f"EXCLUSION: {exclusion.title}\n{exclusion.text}"
        texts_to_embed.append(text)
        clause_mapping.append({"type": "exclusion", "id": exclusion.id, "title": exclusion.title, "text": exclusion.text})
        
    if not texts_to_embed:
        print("No clauses to embed.")
        return
        
    print(f"Generating embeddings for {len(texts_to_embed)} policy clauses/exclusions...")
    embeddings = generate_embeddings(texts_to_embed)
    
    embed_dim = len(embeddings[0])
    index = faiss.IndexFlatL2(embed_dim)
    embeddings_np = np.array(embeddings).astype("float32")
    index.add(embeddings_np)
    
    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(index, "data/index/policy.index")
    
    with open("data/index/clause_mapping.json", "w") as f:
        json.dump(clause_mapping, f, indent=2)
        
    print("Successfully built and saved FAISS index to data/index/policy.index")

if __name__ == "__main__":
    build_offline_index()
