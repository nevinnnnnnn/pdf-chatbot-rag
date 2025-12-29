import os
import pickle
import faiss
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
    query_emb = model.encode([query], normalize_embeddings=True)
    scores, indices = index.search(query_emb, k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        results.append({
            "text": metadata[idx]["text"],
            "page": metadata[idx]["page"],
            "score": float(score)
        })

    return results