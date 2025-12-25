import requests

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
        "stream": False,   # IMPORTANT: force single response
        "options": {
            "temperature": 0.1,
            "num_predict": 256,
            "num_ctx": 4096
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )
        response.raise_for_status()

        # 🔑 Ollama may return NDJSON → handle safely
        raw_text = response.text.strip()

        final_answer = ""
        for line in raw_text.splitlines():
            try:
                chunk = requests.utils.json.loads(line)
                final_answer += chunk.get("response", "")
            except Exception:
                pass

        final_answer = final_answer.strip()

        if not final_answer:
            return "the question is irrelavant"

        return final_answer

    except Exception as e:
        return f"LLM error: {str(e)}"
