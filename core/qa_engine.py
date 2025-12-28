from typing import Dict, List

from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.analytics_logger import log_interaction
from core.entity_extractor import extract_entities


# -------------------------------------------------
# Main QA Engine
# -------------------------------------------------

def answer_question(
    question: str,
    vector_store_path: str,
    top_k: int = 3
) -> Dict:
    """
    Main RAG pipeline:
    - Load vector store
    - Retrieve relevant chunks
    - Extract entities (fast path)
    - Query LLM if needed
    - Log interaction
    """

    # ---------------- Input Validation ----------------
    if not question or not question.strip():
        return {
            "answer": "Please ask a question related to the document.",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Load Vector Store ----------------
    try:
        index, metadata = load_vector_store(vector_store_path)
    except Exception:
        return {
            "answer": "No document is indexed for this chat yet.",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Similarity Search ----------------
    results = similarity_search(
        query=question,
        index=index,
        metadata=metadata,
        top_k=top_k
    )

    if not results:
        return {
            "answer": "the question is irrelavant",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Build Context ----------------
    context_chunks: List[str] = []
    sources: List[Dict] = []
    distances: List[float] = []

    for r in results:
        context_chunks.append(f"[Page {r['page']}]\n{r['text']}")
        sources.append({
            "page": r["page"],
            "distance": round(r["distance"], 4)
        })
        distances.append(r["distance"])

    context = "\n\n".join(context_chunks)

    # ---------------- Entity Extraction (Fast Answers) ----------------
    entities = extract_entities(context)
    q = question.lower()

    ENTITY_RULES = [
        ("emails", ["email", "mail"]),
        ("phones", ["phone", "mobile", "contact"]),
        ("urls", ["website", "url", "link"]),
        ("dates", ["date", "dob", "issued"]),
        ("amounts", ["amount", "salary", "price", "total"]),
    ]

    for entity_key, keywords in ENTITY_RULES:
        if any(word in q for word in keywords) and entities.get(entity_key):
            return {
                "answer": ", ".join(entities[entity_key]),
                "sources": sources,
                "confidence": 1.0
            }

    # ---------------- LLM Reasoning ----------------
    answer_tokens = []

    for token in ask_llm_stream(context, question):
        answer_tokens.append(token)

    answer = "".join(answer_tokens).strip()

    if not answer:
        answer = "the question is irrelavant"

    # ---------------- Confidence Score ----------------
    confidence = round(
        1 / (1 + (sum(distances) / max(len(distances), 1))),
        3
    )

    # ---------------- Logging ----------------
    try:
        log_interaction(
            question=question,
            answer=answer,
            sources=sources,
            confidence=confidence
        )
    except Exception:
        pass  # Logging should never break main flow

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence
    }