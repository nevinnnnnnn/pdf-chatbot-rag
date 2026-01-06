import requests
import os
import json
import time
from typing import Generator

# Constants
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME: str = os.getenv("MODEL_NAME", "mistral:7b-instruct")

def check_ollama_connection() -> bool:
    """Verify Ollama is accessible and responsive."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def ask_llm_stream(context: str, question: str, max_retries: int = 3) -> Generator[str, None, None]:
    """
    Streams responses from the Ollama LLM based on provided context and question.
    
    Args:
        context: Retrieved context from the PDF
        question: User's question
        max_retries: Number of retry attempts for failed requests
    
    Yields:
        Chunks of the generated response
    """
    # Check if Ollama is running
    if not check_ollama_connection():
        yield "⚠️ Error: Cannot connect to Ollama. Please ensure Ollama is running and accessible at " + OLLAMA_HOST
        return

    prompt: str = f"""You are a helpful PDF analysis assistant.

Context from the document:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided context above
- If the context doesn't contain enough information to answer the question, say: "I couldn't find specific information about that in the document."
- Be concise and accurate
- When relevant, mention the page numbers from the context
- Do not make up information

Answer:""".strip()

    payload: dict = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_predict": 500,
            "top_p": 0.9,
            "stop": ["\n\nQuestion:", "\n\nContext:"]
        }
    }

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            # Successfully connected, process the stream
            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    data: dict = json.loads(line.decode("utf-8"))
                    text: str = data.get("response", "")
                    if text:
                        yield text
                    
                    # Check if generation is complete
                    if data.get("done", False):
                        return
                        
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error decoding response: {e}")
                    continue
            
            # If we get here, stream completed successfully
            return
            
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                yield f"\n\n⚠️ Error: Request timed out after {max_retries} attempts. The model might be overloaded."
                return
            time.sleep(2 ** attempt)
            
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                yield f"\n\n⚠️ Error: Could not connect to Ollama at {OLLAMA_HOST}. Please check if Ollama is running."
                return
            time.sleep(2 ** attempt)
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                yield f"\n\n⚠️ Error: {str(e)}"
                return
            time.sleep(2 ** attempt)