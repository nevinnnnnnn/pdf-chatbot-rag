import subprocess


MODEL_NAME = "deepseek-r1:7b"


def ask_llm(context, question):
    """
    Sends context + question to DeepSeek via Ollama
    """

    prompt = f"""
You are a PDF Analysis Assistant.

Your task:
- Answer user questions strictly using the content provided from the PDF.
- Use only the information explicitly present in the PDF text.
- Do NOT use external knowledge, assumptions, or hallucinations.

Rules:
1. If the answer exists in the PDF, give a clear, concise, and factual response.
2. If the question is NOT related to the PDF content or cannot be answered using the PDF, respond exactly with:
   "the question is irrelavant"
3. Do NOT explain your reasoning.
4. Do NOT show any internal thinking, analysis, or step-by-step logic.
5. Do NOT mention the PDF structure, embeddings, retrieval process, or metadata.
6. Do NOT add disclaimers like “based on the document” or “according to the PDF”.
7. Keep responses short and precise.
8. Do NOT rephrase the question in your answer.

Output format:
- Plain text only.
- No markdown.
- No bullet points.
- No extra commentary.

Document Context:
{context}

Question:
{question}

Answer:
"""

    process = subprocess.Popen(
        ["ollama", "run", MODEL_NAME],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    output, _ = process.communicate(prompt)

    return output.strip()
