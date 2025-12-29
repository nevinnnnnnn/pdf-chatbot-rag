import os
import pickle
from typing import List, Dict, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# -----------------------------
# Model Initialization
# -----------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to load embedding model: {e}")


# -----------------------------
# Vector Store Creation
# -----------------------------
def create_vector_store(
    documents: List[Dict],
    save_path: str = "data/vectorstore"
) -> Tuple[faiss.Index, List[Dict]]:
    """
    Creates a FAISS vector store from documents and saves it to disk.

    documents: List of dicts with keys -> 'text', 'page'
    save_path: Directory to save FAISS index and metadata
    """

    if not documents:
        raise ValueError("No documents provided for vector store creation.")

    # Validate input structure
    for doc in documents:
        if "text" not in doc or "page" not in doc:
            raise KeyError("Each document must contain 'text' and 'page' keys.")

    texts = [doc["text"] for doc in documents]
    metadata = [
        {
            "page": doc["page"],
            "text": doc["text"]
        }
        for doc in documents
    ]

    # Generate embeddings
    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=False
    ).astype("float32")

    if embeddings.ndim != 2:
        raise ValueError("Embedding generation failed. Invalid embedding shape.")

    dimension = embeddings.shape[1]

    # Create FAISS index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Persist to disk
    os.makedirs(save_path, exist_ok=True)
    faiss.write_index(index, os.path.join(save_path, "index.faiss"))

    with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    return index, metadata


# -----------------------------
# Load Vector Store
# -----------------------------
def load_vector_store(
    load_path: str = "data/vectorstore"
) -> Tuple[faiss.Index, List[Dict]]:
    """
    Loads FAISS index and metadata from disk.
    """

    index_path = os.path.join(load_path, "index.faiss")
    metadata_path = os.path.join(load_path, "metadata.pkl")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError(
            "Vector store not found. Please create embeddings first."
        )

    index = faiss.read_index(index_path)

    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata


# -----------------------------
# Similarity Search
# -----------------------------
def similarity_search(
    query: str,
    index: faiss.Index,
    metadata: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    Performs similarity search on the FAISS index.
    """

    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string.")

    if index.ntotal == 0:
        return []

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    results = []

    def _distance_to_score(d: float) -> float:
        try:
            return float(1.0 / (1.0 + d))
        except Exception:
            return 0.0

    for idx, dist in zip(indices[0], distances[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        score = _distance_to_score(float(dist))
        results.append({
            "page": metadata[idx].get("page"),
            "distance": float(dist),
            "score": score,
            "text": metadata[idx].get("text")
        })

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    return results
