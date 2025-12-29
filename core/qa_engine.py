from typing import Dict, List, Any

from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.analytics_logger import log_interaction
from core.entity_extractor import extract_entities


# ---------------------------------------
# Types
# ---------------------------------------

Document = Dict[str, Any]
Result = Dict[str, Any]


# ---------------------------------------
# Main QA Engine
# ---------------------------------------

def answer_question(
    question: str,
    vector_store_path: str,
    chat_history: str = "",
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Main RAG pipeline:
    - Load vector store
    - Retrieve relevant chunks
    - Extract entities
    - Generate LLM response
    """

    # ---------------- Validation ----------------
    if not question or not question.strip():
        return {
            "answer": "Please ask a question related to the document.",
            "sources": [],
            "confidence": 0.0,
        }

    # ---------------- Load Vector Store ----------------
    try:
        index, metadata = load_vector_store(vector_store_path)
    except Exception:
        return {
            "answer": "No document has been indexed yet.",
            "sources": [],
            "confidence": 0.0,
        }

    # ---------------- Similarity Search ----------------
    results: List[Result] = similarity_search(
        query=question,
        index=index,
        metadata=metadata,
        top_k=top_k,
    )

    # ---------------- Context Construction ----------------
    if results:
        context = "\n\n".join(
            f"[Page {r['page']}]\n{r['text']}" for r in results
        )
    else:
        # fallback to first chunks
        context = "\n\n".join(
            f"[Page {m['page']}]\n{m['text']}" for m in metadata[:5]
        )

    # ---------------- Entity Shortcuts ----------------
    entities = extract_entities(context)
    q_lower = question.lower()

    ENTITY_MAP = {
        "emails": ["email", "mail"],
        "phones": ["phone", "mobile", "contact"],
        "urls": ["website", "url", "link"],
        "dates": ["date", "dob", "issued"],
        "amounts": ["amount", "price", "total"],
    }

    for key, keywords in ENTITY_MAP.items():
        if any(k in q_lower for k in keywords) and entities.get(key):
            return {
                "answer": ", ".join(entities[key]),
                "sources": results,
                "confidence": 1.0,
            }

    # ---------------- LLM Generation ----------------
    answer_tokens: List[str] = []

    for token in ask_llm_stream(context, question):
        answer_tokens.append(token)

    answer: str = "".join(answer_tokens).strip()

    if not answer:
        answer = "The question goes beyond the document content."

    # ---------------- Confidence Score ----------------
    confidence: float = round(
        1 / (1 + len(results)),
        3
    )

    # ---------------- Logging ----------------
    try:
        log_interaction(
            question=question,
            answer=answer,
            sources=results,
            confidence=confidence,
        )
    except Exception:
        pass  # Never break app

    return {
        "answer": answer,
        "sources": results,
        "confidence": confidence,
    }