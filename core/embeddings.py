import os
import pickle
import faiss  # type: ignore
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# Initialize the model
# Using all-MiniLM-L6-v2 for a good balance of speed and accuracy
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_vector_store(documents: List[Dict[str, Any]], save_path: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Creates a FAISS index from document chunks and saves it along with metadata.
    
    Args:
        documents: List of dicts containing 'text' and 'page' keys.
        save_path: Directory where the index and metadata will be stored.
    """
    # Type hinting lists to satisfy Pylance
    texts: List[str] = [d["text"] for d in documents]
    metadata: List[Dict[str, Any]] = [{"page": d["page"], "text": d["text"]} for d in documents]

    # model.encode returns a numpy array; cast to float32 for FAISS compatibility
    embeddings = model.encode(texts).astype("float32")

    # Initialize FAISS index. We use IndexFlatL2 for exact L2 distance search.
    # We explicitly type hint the index to resolve the "Argument missing for parameter x" error
    dimension = embeddings.shape[1]
    index: faiss.IndexFlatL2 = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Ensure the storage directory exists
    os.makedirs(save_path, exist_ok=True)

    # Save the FAISS index and metadata
    faiss.write_index(index, os.path.join(save_path, "index.faiss"))
    with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    return index, metadata


def load_vector_store(path: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Loads an existing FAISS index and its associated metadata from disk.
    """
    index_path = os.path.join(path, "index.faiss")
    metadata_path = os.path.join(path, "metadata.pkl")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Vector store not found at {path}")

    index = faiss.read_index(index_path)
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
        
    return index, metadata


def similarity_search(
    query: str, 
    index: Any, 
    metadata: List[Dict[str, Any]], 
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Converts a query into an embedding and retrieves the top_k most relevant chunks.
    """
    # Encode query and ensure it is the correct shape for FAISS
    q = model.encode([query]).astype("float32")
    
    # distances: proximity score; indices: position in the metadata list
    distances, indices = index.search(q, top_k)

    results: List[Dict[str, Any]] = []
    
    # zip the results and filter out invalid indices (-1)
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1 and idx < len(metadata):
            results.append({
                "page": metadata[idx]["page"],
                "text": metadata[idx]["text"],
                "distance": float(dist)
            })

    return results