from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.analytics_logger import log_interaction
from core.entity_extractor import extract_entities


def answer_question(question, vector_store_path, top_k=3):
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
    context_chunks = []
    sources = []
    distances = []

    for r in results:
        context_chunks.append(
            f"[Page {r['page']}]\n{r['text']}"
        )
        sources.append({
            "page": r["page"],
            "distance": round(r["distance"], 4)
        })
        distances.append(r["distance"])

    context = "\n\n".join(context_chunks)

    # ---------------- Entity Extraction (Fast Path) ----------------
    entities = extract_entities(context)
    q = question.lower()

    if "email" in q and entities.get("emails"):
        return {
            "answer": ", ".join(entities["emails"]),
            "sources": sources,
            "confidence": 1.0
        }

    if any(k in q for k in ["phone", "contact", "mobile"]) and entities.get("phones"):
        return {
            "answer": ", ".join(entities["phones"]),
            "sources": sources,
            "confidence": 1.0
        }

    if any(k in q for k in ["website", "url", "link"]) and entities.get("urls"):
        return {
            "answer": ", ".join(entities["urls"]),
            "sources": sources,
            "confidence": 1.0
        }

    if any(k in q for k in ["date", "dob", "issued"]) and entities.get("dates"):
        return {
            "answer": ", ".join(entities["dates"]),
            "sources": sources,
            "confidence": 1.0
        }

    if any(k in q for k in ["amount", "salary", "price", "total"]) and entities.get("amounts"):
        return {
            "answer": ", ".join(entities["amounts"]),
            "sources": sources,
            "confidence": 1.0
        }

    # ---------------- Ask LLM (LET IT DECIDE) ----------------
    answer_tokens = []
    for token in ask_llm_stream(context, question):
        answer_tokens.append(token)

    answer = " ".join(answer_tokens).strip()

    if not answer:
        answer = "the question is irrelavant"

    # ---------------- Confidence (Soft, Not Binary) ----------------
    confidence = round(
        1 / (1 + sum(distances) / len(distances)),
        3
    )

    # ---------------- Logging ----------------
    log_interaction(
        question=question,
        answer=answer,
        sources=sources,
        confidence=confidence
    )

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence
    }