from typing import List, Dict, Any, Optional
from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.entity_extractor import extract_entities 

def answer_question(
    question: str, 
    vector_store_path: str, 
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Coordinates the RAG process: loads index, searches, and queries the LLM.
    """
    # 1. Load the vector store
    index, metadata = load_vector_store(vector_store_path)

    # 2. Search for relevant context
    search_results = similarity_search(question, index, metadata, top_k=top_k)
    
    # 3. Combine context for the LLM
    context_text: str = "\n".join([res["text"] for res in search_results])
    
    # 4. Get response from LLM (Streaming)
    # Note: For the dict return, we collect the stream into a single string
    full_answer: List[str] = []
    for chunk in ask_llm_stream(context_text, question):
        full_answer.append(chunk)
    
    final_answer: str = "".join(full_answer)

    # 5. Extract entities for metadata/logging
    entities = extract_entities(final_answer)

    return {
        "answer": final_answer,
        "sources": search_results,
        "entities": entities,
        "confidence": 0.0  # Placeholder for logic
    }