import os
import pickle
import faiss  # type: ignore
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# Initialize the model
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_vector_store(documents: List[Dict[str, Any]], save_path: str) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Creates a FAISS index from document chunks and saves it along with metadata.
    """
    if not documents:
        raise ValueError("No documents provided for vector store creation")
    
    texts: List[str] = [d["text"] for d in documents]
    metadata: List[Dict[str, Any]] = [
        {
            "page": d["page"], 
            "text": d["text"],
            "has_images": d.get("has_images", False)
        } 
        for d in documents
    ]

    # Encode texts into embeddings
    embeddings = model.encode(texts, show_progress_bar=True).astype("float32")

    # Initialize FAISS index with L2 distance
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

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at {index_path}")
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata not found at {metadata_path}")

    try:
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
    except Exception as e:
        raise Exception(f"Failed to load vector store: {str(e)}")
        
    return index, metadata


def similarity_search(
    query: str, 
    index: Any, 
    metadata: List[Dict[str, Any]], 
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Converts a query into an embedding and retrieves the top_k most relevant chunks.
    """
    if not query.strip():
        return []
    
    # Encode query
    query_embedding = model.encode([query]).astype("float32")
    
    # Search for similar vectors
    distances, indices = index.search(query_embedding, top_k)

    results: List[Dict[str, Any]] = []
    
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1 and idx < len(metadata):
            results.append({
                "page": metadata[idx]["page"],
                "text": metadata[idx]["text"],
                "distance": float(dist),
                "has_images": metadata[idx].get("has_images", False)
            })

    return results