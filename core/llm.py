import subprocess

MODEL_NAME = "mistral:7b-instruct"


def ask_llm_stream(context, question):
    prompt = f"""
You are a PDF Analysis expert.

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

    try:
        process = subprocess.Popen(
            ["ollama", "run", MODEL_NAME],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        # Send prompt
        process.stdin.write(prompt)
        process.stdin.close()

        # Stream tokens line-by-line
        for line in process.stdout:
            if line.strip():
                yield line

        process.stdout.close()
        process.wait()

    except Exception:
        yield "the question is irrelavant"
