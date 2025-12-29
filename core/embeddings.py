import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL)


def create_vector_store(docs, path):
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, normalize_embeddings=True)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(path, exist_ok=True)
    faiss.write_index(index, f"{path}/index.faiss")

    with open(f"{path}/metadata.pkl", "wb") as f:
        pickle.dump(docs, f)


def load_vector_store(path):
    index = faiss.read_index(f"{path}/index.faiss")
    with open(f"{path}/metadata.pkl", "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def similarity_search(query, index, metadata, k=3):
    q = model.encode([query], normalize_embeddings=True)
    scores, indices = index.search(q, k)

    results = []
    for i, score in zip(indices[0], scores[0]):
        if i < 0:
            continue
        results.append({
            "page": metadata[i]["page"],
            "text": metadata[i]["text"],
            "score": float(score)
        })

    return results