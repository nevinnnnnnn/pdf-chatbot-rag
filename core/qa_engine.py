from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.analytics_logger import log_interaction


def answer_question(question, top_k=2):
    """
    Answers a question using FAISS retrieval + LLM
    """

    if not question or not question.strip():
        return {
            "answer": "Please ask a valid question.",
            "sources": [],
            "confidence": 0.0
        }

    # Load vector store
    try:
        index, metadata = load_vector_store()
    except Exception as e:
        return {
            "answer": "No document knowledge is available yet.",
            "sources": [],
            "confidence": 0.0
        }

    # Retrieve relevant chunks
    results = similarity_search(question, index, metadata, top_k=top_k)

    if not results:
        return {
            "answer": "The question is irrelevant or not covered in the document.",
            "sources": [],
            "confidence": 0.0
        }

    # Build context
    context = ""
    sources_dict = {}
    distances = []

    for r in results:
        context += f"[Page {r['page']}]\n{r['text']}\n\n"

        dist = float(r.get("distance", 1.0))
        page = r.get("page", "N/A")

        distances.append(dist)

        rounded_dist = round(dist, 4)
        if page not in sources_dict or rounded_dist < sources_dict[page]:
            sources_dict[page] = rounded_dist

    sources = [
        {"page": page, "distance": distance}
        for page, distance in sources_dict.items()
    ]

    # Ask LLM safely
    try:
        answer_stream = ask_llm_stream(context, question)
        if not answer or not answer.strip():
            answer = "The question is irrelevant."
    except Exception as e:
        answer = "The question is irrelevant."

    # Confidence score
    confidence = round(1 / (1 + sum(distances) / len(distances)), 4)

    # Log interaction
    log_interaction(
        question=question,
        answer=answer,
        confidence=confidence,
        sources=sources
    )

    return {
        "answer_stream": answer_stream,
        "sources": sources
    }