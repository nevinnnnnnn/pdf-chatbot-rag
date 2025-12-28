import os
from typing import Generator

from huggingface_hub import InferenceClient


# -------------------------------------------------
# LLM Wrapper (Hugging Face Inference API)
# -------------------------------------------------

class HFInferenceLLM:
    def __init__(
        self,
        repo_id: str,
        token: str,
        temperature: float = 0.2,
        max_new_tokens: int = 512,
    ):
        if not token:
            raise ValueError("HuggingFace token is missing.")

        self.repo_id = repo_id
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

        self.client = InferenceClient(
            model=repo_id,
            token=token
        )

    def invoke(self, prompt: str) -> str:
        """
        Sends a prompt to the HF inference endpoint.
        """

        try:
            response = self.client.text_generation(
                prompt=prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                return_full_text=False,
            )
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return ""

        if not response:
            return ""

        return response.strip()


# -------------------------------------------------
# Initialize LLM (Environment-safe)
# -------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN", "")

llm = HFInferenceLLM(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN,
    temperature=0.2,
    max_new_tokens=512
)


# -------------------------------------------------
# Streaming Wrapper (UI-friendly)
# -------------------------------------------------

def ask_llm_stream(context: str, question: str) -> Generator[str, None, None]:
    """
    Simulates token streaming for UI rendering.
    """

    MAX_CONTEXT_CHARS = 4000
    context = context[:MAX_CONTEXT_CHARS]

    prompt = f"""
You are a PDF analysis assistant.

Rules:
- Answer ONLY using the provided context.
- If the answer is not present, reply exactly:
  "the question is irrelavant"
- Do NOT explain your reasoning.
- Do NOT use markdown.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    response = llm.invoke(prompt)

    if not response.strip():
        yield "the question is irrelavant"
        return

    # Simulated streaming
    for word in response.split():
        yield word + " "
