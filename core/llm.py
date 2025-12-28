import streamlit as st
from langchain_huggingface import HuggingFaceEndpoint
from huggingface_hub import InferenceApi

# ---------------- LLM ----------------
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=st.secrets["HF_TOKEN"],
    temperature=0.2,
    max_new_tokens=512
)
class HFInferenceLLM:
    def __init__(self, repo_id: str, token: str, temperature: float = 0.2, max_new_tokens: int = 512):
        self.client = InferenceApi(repo_id=repo_id, token=token)
        self.params = {"temperature": temperature, "max_new_tokens": max_new_tokens}

    def invoke(self, prompt: str) -> str:
        try:
            result = self.client(inputs=prompt, parameters=self.params)
        except Exception:
            raise

        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            if "generated_text" in result:
                return result["generated_text"]
            return str(result)
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict) and "generated_text" in first:
                return first["generated_text"]
            return str(first)
        return ""

llm = HFInferenceLLM("Mistral-7B-Instruct", st.secrets["HF_TOKEN"], temperature=0.2, max_new_tokens=512)
# ---------------- Streaming Wrapper ----------------
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

    try:
        response = llm.invoke(prompt)
    except Exception:
        yield "the question is irrelavant"
        return

    if not response or not response.strip():
        yield "the question is irrelavant"
        return

    # Token-style streaming for UI typing effect
    for token in response.split():
        yield token
