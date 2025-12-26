from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.analytics_logger import log_interaction
from core.entity_extractor import extract_entities

DISTANCE_THRESHOLD = 3.5  # relaxed for resumes & structured docs


def answer_question(question, top_k=3):
    if not question or not question.strip():
        return {
            "answer": "Please ask a question in context to the pdf.",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Load Vector Store ----------------
    try:
        index, metadata = load_vector_store()
    except Exception:
        return {
            "answer": "No document knowledge is available yet.",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Similarity Search ----------------
    results = similarity_search(question, index, metadata, top_k=top_k)

    if not results:
        return {
            "answer": "the question is irrelavant",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Build Context ----------------
    context = ""
    sources = []
    distances = []

    for r in results:
        context += f"[Page {r['page']}]\n{r['text']}\n\n"
        sources.append({
            "page": r["page"],
            "distance": round(r["distance"], 4)
        })
        distances.append(r["distance"])

    # ---------------- Structured Entity Extraction ----------------
    entities = extract_entities(context)
    q = question.lower()

    # -------- Entity-based Direct Answers (High Confidence) --------
    if "email" in q and entities.get("emails"):
        answer = ", ".join(entities["emails"])
        log_interaction(question, answer, [], 1.0)
        return {"answer": answer, "sources": [], "confidence": 1.0}

    if any(k in q for k in ["phone", "contact", "mobile"]) and entities.get("phones"):
        answer = ", ".join(entities["phones"])
        log_interaction(question, answer, [], 1.0)
        return {"answer": answer, "sources": [], "confidence": 1.0}

    if any(k in q for k in ["website", "url", "link"]) and entities.get("urls"):
        answer = ", ".join(entities["urls"])
        log_interaction(question, answer, [], 1.0)
        return {"answer": answer, "sources": [], "confidence": 1.0}

    if any(k in q for k in ["date", "dob", "issued", "invoice date"]) and entities.get("dates"):
        answer = ", ".join(entities["dates"])
        log_interaction(question, answer, [], 1.0)
        return {"answer": answer, "sources": [], "confidence": 1.0}

    if any(k in q for k in ["amount", "salary", "price", "cost", "total"]) and entities.get("amounts"):
        answer = ", ".join(entities["amounts"])
        log_interaction(question, answer, [], 1.0)
        return {"answer": answer, "sources": [], "confidence": 1.0}

    # ---------------- Relevance Check ----------------
    if min(distances) > DISTANCE_THRESHOLD:
        return {
            "answer": "the question is irrelavant",
            "sources": [],
            "confidence": 0.0
        }

    # ---------------- Ask LLM (RAG) ----------------
    answer_chunks = []
    for token in ask_llm_stream(context, question):
        answer_chunks.append(token)

    answer = " ".join(answer_chunks).strip()

    if not answer:
        answer = "the question is irrelavant"

    # ---------------- Confidence Score ----------------
    confidence = round(1 / (1 + sum(distances) / len(distances)), 3)

    # ---------------- Analytics ----------------
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