import streamlit as st
from huggingface_hub import InferenceApi

# -------------------------------------------------
# Hugging Face Inference LLM Wrapper
# -------------------------------------------------

class HFInferenceLLM:
    def __init__(
        self,
        repo_id: str,
        token: str,
        temperature: float = 0.2,
        max_new_tokens: int = 512,
    ):
        self.client = InferenceApi(
            repo_id=repo_id,
            token=token
        )
        self.params = {
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "return_full_text": False
        }

    def invoke(self, prompt: str) -> str:
        try:
            result = self.client(
                inputs=prompt,
                parameters=self.params
            )
        except Exception:
            return ""

        # Normalize HF responses
        if isinstance(result, list) and result:
            return result[0].get("generated_text", "")
        if isinstance(result, dict):
            return result.get("generated_text", "")
        if isinstance(result, str):
            return result

        return ""


# -------------------------------------------------
# Initialize LLM (Streamlit Cloud safe)
# -------------------------------------------------

llm = HFInferenceLLM(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    token=st.secrets["HF_TOKEN"],
    temperature=0.2,
    max_new_tokens=512
)


# -------------------------------------------------
# Streaming wrapper (pseudo-stream for UI)
# -------------------------------------------------

def ask_llm_stream(context: str, question: str):
    """
    Generates answer tokens one by one for typing effect
    """

    # 🔒 HARD LIMIT CONTEXT (VERY IMPORTANT)
    MAX_CONTEXT_CHARS = 4000
    context = context[:MAX_CONTEXT_CHARS]

    prompt = f"""
You are a PDF analysis assistant.

Rules:
- Answer ONLY using the information in the given context.
- If the context does not contain enough information, reply exactly: the question is irrelavant
- Do not explain your reasoning.
- Do not use markdown.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    response = llm.invoke(prompt)

    if not response or not response.strip():
        yield "the question is irrelavant"
        return

    # Token-style streaming (UI typing effect)
    for token in response.split():
        yield token