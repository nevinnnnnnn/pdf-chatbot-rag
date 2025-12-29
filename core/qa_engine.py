from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream


def answer_question(question, vector_store_path):
    index, metadata = load_vector_store(vector_store_path)

    results = similarity_search(question, index, metadata)

    if not results:
        return {
            "answer": "I could not find an answer in the document.",
            "sources": []
        }

    context = "\n\n".join(
        f"[Page {r['page']}]\n{r['text']}" for r in results
    )

    answer = ""
    for token in ask_llm_stream(context, question):
        answer += token

    return {
        "answer": answer,
        "sources": results
    }