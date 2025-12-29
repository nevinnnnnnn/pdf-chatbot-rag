import os
import pickle
import faiss # type: ignore
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# Initialize the model
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_vector_store(documents: List[Dict[str, Any]], save_path: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Creates a FAISS index and saves metadata.
    """
    texts: List[str] = [d["text"] for d in documents]
    metadata: List[Dict[str, Any]] = [{"page": d["page"], "text": d["text"]} for d in documents]

    # model.encode returns a numpy array
    embeddings = model.encode(texts).astype("float32")

    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(save_path, exist_ok=True)
    faiss.write_index(index, os.path.join(save_path, "index.faiss"))

    with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    return index, metadata


def load_vector_store(path: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Loads an existing FAISS index and metadata.
    """
    index = faiss.read_index(os.path.join(path, "index.faiss"))
    with open(os.path.join(path, "metadata.pkl"), "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def similarity_search(query: str, index: Any, metadata: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Performs a vector search and returns the top_k results.
    """
    q = model.encode([query]).astype("float32")
    distances, indices = index.search(q, top_k)

    results: List[Dict[str, Any]] = []
    # Ensure indices and distances are iterated correctly
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1:  # FAISS returns -1 if not enough matches are found
            results.append({
                "page": metadata[idx]["page"],
                "text": metadata[idx]["text"],
                "distance": float(dist)
            })

    return results