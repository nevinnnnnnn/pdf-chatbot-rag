import subprocess
import sys

MODEL_NAME = "mistral:7b-instruct"


def ask_llm_stream(context, question):
    prompt = f"""
You are a PDF analysis assistant.

Rules:
- Answer ONLY from the given context.
- If not answerable, reply exactly: the question is irrelavant
- No explanations, no markdown, no reasoning.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    process = subprocess.Popen(
        ["ollama", "run", MODEL_NAME],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="ignore"     
    )

    try:
        process.stdin.write(prompt)
        process.stdin.close()
    except Exception:
        yield "the question is irrelavant"
        return

    for line in process.stdout:
        if line.strip():
            yield line.strip()

    process.stdout.close()
    process.wait()
