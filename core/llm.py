import subprocess

MODEL_NAME = "qwen2.5:3b"

def ask_llm(context, question):
    """
    Calls Ollama directly via CLI for maximum stability on Windows
    """

    prompt = f"""
You are a PDF Analysis expert.

Rules:
- Answer ONLY from the given context.
- If the answer is not present, reply exactly: the question is irrelavant
- No reasoning, no explanations, no markdown.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    try:
        process = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=180
        )

        output = process.stdout.strip()

        if not output:
            return "the question is irrelavant"

        return output

    except subprocess.TimeoutExpired:
        return "LLM timeout error"

    except Exception as e:
        return f"LLM error: {str(e)}"