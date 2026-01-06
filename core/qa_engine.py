from typing import List, Dict, Any
from core.embeddings import load_vector_store, similarity_search
from core.llm import ask_llm_stream
from core.entity_extractor import extract_entities

def answer_question(
    question: str, 
    vector_store_path: str, 
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Coordinates the RAG process: loads index, searches, and queries the LLM.
    
    Args:
        question: User's question
        vector_store_path: Path to the vector store
        top_k: Number of relevant chunks to retrieve
    
    Returns:
        Dictionary containing answer, sources, entities, and confidence
    """
    try:
        # 1. Load the vector store
        index, metadata = load_vector_store(vector_store_path)
    except FileNotFoundError:
        return {
            "answer": "⚠️ Please upload and index a PDF first before asking questions.",
            "sources": [],
            "entities": {},
            "confidence": 0.0
        }
    except Exception as e:
        return {
            "answer": f"⚠️ Error loading document index: {str(e)}",
            "sources": [],
            "entities": {},
            "confidence": 0.0
        }

    try:
        # 2. Search for relevant context
        search_results = similarity_search(question, index, metadata, top_k=top_k)
        
        if not search_results:
            return {
                "answer": "I couldn't find any relevant information in the document to answer your question.",
                "sources": [],
                "entities": {},
                "confidence": 0.0
            }
        
        # 3. Combine context for the LLM
        context_text: str = "\n\n".join([
            f"[Page {res['page']}]: {res['text']}" 
            for res in search_results
        ])
        
        # 4. Get response from LLM (Streaming)
        full_answer: List[str] = []
        for chunk in ask_llm_stream(context_text, question):
            full_answer.append(chunk)
        
        final_answer: str = "".join(full_answer).strip()
        
        # Handle empty responses
        if not final_answer:
            final_answer = "I couldn't generate a proper response. Please try rephrasing your question."

        # 5. Extract entities for metadata
        entities = extract_entities(final_answer)

        # 6. Calculate simple confidence based on distance scores
        avg_distance = sum(r["distance"] for r in search_results) / len(search_results)
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 10.0)))

        return {
            "answer": final_answer,
            "sources": search_results,
            "entities": entities,
            "confidence": confidence
        }
        
    except Exception as e:
        return {
            "answer": f"⚠️ Error generating answer: {str(e)}",
            "sources": search_results if 'search_results' in locals() else [],
            "entities": {},
            "confidence": 0.0
        }