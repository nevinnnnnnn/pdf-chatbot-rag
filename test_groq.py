import os
import sys
import requests

# Try to load from Streamlit secrets first
try:
    import streamlit as st
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
    print("✅ Loaded from Streamlit secrets")
except:
    # Fallback to environment variable
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    print("⚠️ Loaded from environment variable")

print(f"API Key present: {bool(GROQ_API_KEY)}")
print(f"API Key length: {len(GROQ_API_KEY)}")
print(f"API Key starts with 'gsk_': {GROQ_API_KEY.startswith('gsk_')}")

if not GROQ_API_KEY:
    print("\n❌ ERROR: No API key found!")
    print("\nPlease create .streamlit/secrets.toml with:")
    print('GROQ_API_KEY = "your_key_here"')
    sys.exit(1)

# Test the API
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Say 'test successful'"}],
    "stream": False
}

print("\n🔄 Testing Groq API...")

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API is working!")
        result = response.json()
        print(f"Response: {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")