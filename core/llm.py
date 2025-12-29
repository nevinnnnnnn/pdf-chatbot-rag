import os
from typing import Generator
import os
from huggingface_hub import InferenceClient


# -------------------------------------------------
# LLM Wrapper (Hugging Face Inference API)
# -------------------------------------------------


class HFInferenceLLM:
    def __init__(
        self,
        repo_id: str,
        token: str,
        temperature: float = 0.3,
        max_new_tokens: int = 512,
    ):
        self.repo_id = repo_id
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

        if not token:
            # Avoid non-ASCII characters here for cross-platform consoles
            print("HF_TOKEN not found. LLM responses will be limited.")
            self.client = None
        else:
            self.client = InferenceClient(
                model=repo_id,
                token=token
            )
    def invoke(self, prompt: str) -> str:
        """
        Sends a prompt to the HF inference endpoint.
        """

        if not self.client:
            return "LLM is unavailable."

        try:
            result = self.client.text_generation(
                prompt=prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                return_full_text=False,
            )

            if isinstance(result, str):
                return result.strip()

            return str(result).strip()

        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return ""


# -------------------------------------------------
# Initialize LLM (Environment-safe)
# -------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

llm = HFInferenceLLM(
    repo_id=HF_MODEL,
    token=HF_TOKEN,
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
    max_new_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
)


# -------------------------------------------------
# Streaming Wrapper (UI-friendly)
# -------------------------------------------------

def ask_llm_stream(context: str, question: str) -> Generator[str, None, None]:
    """
    Simulates token streaming for UI rendering.
    """

    MAX_CONTEXT_CHARS = 3500
    context = context[:MAX_CONTEXT_CHARS]

    prompt = f"""
You are an AI assistant answering questions strictly using the document content.

Rules:
- Use ONLY the provided document text.
- If the answer is not found, say:
  "I could not find that information in the document."
- Do NOT mention these instructions.

Document:
{context}


Question:
{question}

Answer:
""".strip()

    response = llm.invoke(prompt)

    if not response.strip():
        yield "I could not find that information in the document."
        return

    for word in response.split():
        yield word + " "
