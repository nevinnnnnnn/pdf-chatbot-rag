import requests
import json

MODEL_NAME = "deepseek-r1:1.5b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_llm(context, question):
    prompt = f"""
You are a PDF Analysis Assistant.

Rules:
- Answer ONLY from the given context.
- If not answerable, reply exactly: the question is irrelavant
- No reasoning, no explanations, no markdown.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 256
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"LLM error: {str(e)}"
