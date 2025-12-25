from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm
from core.analytics_logger import log_interaction


def answer_question(question, top_k=2):
    """
    Answers a question using FAISS retrieval + LLM
    """

    # Load vector store
    try:
        index, metadata = load_vector_store()
    except Exception:
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

    # Build context for LLM + deduplicate sources by page
    context = ""
    sources_dict = {}   
    distances = []

    for r in results:
        context += f"[Page {r['page']}]\n{r['text']}\n\n"

        dist = r["distance"]
        page = r["page"]
        distances.append(dist)

        rounded_dist = round(dist, 4)

        if page not in sources_dict or rounded_dist < sources_dict[page]:
            sources_dict[page] = rounded_dist

    # Convert deduplicated sources to list
    sources = [
        {"page": page, "distance": distance}
        for page, distance in sources_dict.items()
    ]

    # Ask LLM
    answer = ask_llm(context, question)

    # Confidence score (inverse average distance)
    confidence = round(1 / (1 + sum(distances) / len(distances)), 4)

    # Log analytics
    log_interaction(
        question=question,
        answer=answer,
        confidence=None,
        sources=sources
    )

    return {
        "answer": answer,
        "sources": sources
    }