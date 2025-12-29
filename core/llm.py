from huggingface_hub import InferenceClient
import os

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

client = InferenceClient(model=MODEL, token=HF_TOKEN)


def ask_llm_stream(context: str, question: str):
    prompt = f"""
Answer ONLY using the content below.

Context:
{context}

Question:
{question}
"""

    response = client.text_generation(
        prompt=prompt,
        max_new_tokens=400,
        temperature=0.3,
        return_full_text=False,
    )

    for word in response.split():
        yield word + " "