import os
import json
from typing import Generator, List, Optional
import requests

# Use Groq API with Vision support
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Correct endpoint

def check_groq_connection() -> bool:
    """Verify Groq API key is set."""
    return bool(GROQ_API_KEY)

def ask_llm_stream(
    context: str, 
    question: str, 
    images: Optional[List[str]] = None,
    max_retries: int = 3
) -> Generator[str, None, None]:
    """
    Streams responses from Groq API with vision support.
    
    Args:
        context: Retrieved text context from the PDF
        question: User's question
        images: List of base64-encoded images (optional)
        max_retries: Number of retry attempts for failed requests
    
    Yields:
        Chunks of the generated response
    """
    if not check_groq_connection():
        yield "⚠️ Error: GROQ_API_KEY not configured. Please add it to your .streamlit/secrets.toml file."
        return

    # Use vision model if images are present, otherwise use text model
    if images and len(images) > 0:
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # Build message content with text and images
        content = []
        
        # Add text context
        content.append({
            "type": "text",
            "text": f"""You are a helpful PDF analysis assistant.

Context from the document:
{context}

Question: {question}

Instructions:
- Answer based on the provided context and any images shown
- If analyzing charts/images, describe what you see and extract relevant information
- If the context doesn't contain enough information, say: "I couldn't find specific information about that in the document."
- Be concise and accurate
- Mention page numbers when relevant

Answer:"""
        })
        
        # Add images (limit to 3)
        for img_base64 in images[:3]:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        messages = [{"role": "user", "content": content}]
        
    else:
        # Text-only model for faster responses when no images
        model = "llama-3.3-70b-versatile"
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful PDF analysis assistant. Answer based ONLY on the provided context. If the context doesn't contain enough information, say so clearly."
            },
            {
                "role": "user",
                "content": f"""Context from the document:
{context}

Question: {question}

Answer concisely based only on the context above:"""
            }
        ]

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": 1000,
        "top_p": 0.9
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GROQ_API_URL,
                json=payload,
                headers=headers,
                stream=True,
                timeout=90
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', error_text)
                except:
                    error_msg = error_text
                
                yield f"⚠️ API Error ({response.status_code}): {error_msg}"
                return
            
            response.raise_for_status()

            # Process streaming response
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_text = line.decode('utf-8')
                
                # Remove 'data: ' prefix
                if line_text.startswith('data: '):
                    line_text = line_text[6:]
                
                # Check for completion
                if line_text.strip() == '[DONE]':
                    return
                    
                try:
                    data = json.loads(line_text)
                    
                    # Check for errors in response
                    if "error" in data:
                        yield f"⚠️ API Error: {data['error'].get('message', 'Unknown error')}"
                        return
                    
                    # Extract content from delta
                    choices = data.get('choices', [])
                    if choices:
                        delta = choices[0].get('delta', {})
                        content_chunk = delta.get('content', '')
                        if content_chunk:
                            yield content_chunk
                            
                except json.JSONDecodeError:
                    continue
            
            return  # Successfully completed

        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                yield f"⚠️ Error: Request timed out after {max_retries} attempts."
                return
            continue
            
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                yield f"⚠️ Error: Could not connect to Groq API. Please check your internet connection."
                return
            continue
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                yield f"⚠️ Error: {str(e)}"
                return
            continue