import requests
import os
import json
from typing import Generator

# Constants
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME: str = "mistral:7b-instruct"

def ask_llm_stream(context: str, question: str) -> Generator[str, None, None]:
    """
    Streams responses from the Ollama LLM based on provided context and question.
    """
    prompt: str = f"""
You are a PDF analysis assistant.

Rules:
- Answer ONLY from the given context.
- If the answer is not in the context, reply exactly: the question is irrelavant
- No explanations. No markdown.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    payload: dict = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 300
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            stream=True,
            timeout=120
        )
        response.raise_for_status() # Check for HTTP errors
    except Exception:
        yield "the question is irrelavant"
        return

    for line in response.iter_lines():
        if not line:
            continue

        try:
            # Use json.loads instead of eval() for safety and type clarity
            data: dict = json.loads(line.decode("utf-8"))
            text: str = data.get("response", "")
            if text:
                yield text
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue