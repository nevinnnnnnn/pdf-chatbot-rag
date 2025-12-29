import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"


class HFInferenceLLM:
    def __init__(self):
        self.client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)

    def invoke(self, prompt: str) -> str:
        try:
            return self.client.text_generation(
                prompt=prompt,
                max_new_tokens=512,
                temperature=0.3,
                return_full_text=False
            )
        except Exception:
            return ""


llm = HFInferenceLLM()


def ask_llm_stream(context, question):
    prompt = f"""
Use ONLY the content below.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    if not response:
        yield "I could not find that information in the document."
        return

    for word in response.split():
        yield word + " "
