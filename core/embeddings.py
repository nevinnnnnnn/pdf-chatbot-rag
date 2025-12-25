import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model (free & open-source)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def create_vector_store(documents, save_path="data/vectorstore"):
    """
    Creates a FAISS vector store with metadata.
    """
    texts = [doc["text"] for doc in documents]
    metadata = [
    {
        "page": doc["page"],
        "text": doc["text"]
    }
    for doc in documents
]

    embeddings = embedding_model.encode(texts, show_progress_bar=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    os.makedirs(save_path, exist_ok=True)

    faiss.write_index(index, os.path.join(save_path, "index.faiss"))

    with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    return index, metadata


def load_vector_store(load_path="data/vectorstore"):
    """
    Loads FAISS index and metadata.
    """
    index = faiss.read_index(os.path.join(load_path, "index.faiss"))

    with open(os.path.join(load_path, "metadata.pkl"), "rb") as f:
        metadata = pickle.load(f)

    return index, metadata


def similarity_search(query, index, metadata, top_k=3):
    """
    Searches similar chunks and returns results with metadata.
    """
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        results.append({
            "page": metadata[idx]["page"],
            "distance": float(dist),
            "text": metadata[idx]["text"]
        })

    return results
