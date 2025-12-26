PDF Chatbot – Local RAG-based Question Answering System

A local-first, privacy-preserving PDF Question Answering chatbot built using Retrieval-Augmented Generation (RAG).
The application allows users to upload a PDF and ask questions that are answered strictly from the document content using a locally running LLM via Ollama.
❗ No external APIs.
❗ No cloud inference.
❗ No data leaves your machine.

Features:
📄 Upload and process PDF documents
🔍 Semantic search using FAISS vector store
🧠 LLM-based answers generated only from PDF context
💬 ChatGPT-style chat interface (Streamlit)
⚡ Token-by-token streaming responses
📚 Source attribution (page numbers)
🌓 Dark mode support
🧹 Clear chat functionality
🔒 Fully local & private (Ollama-based LLM)

Architecture Overview:
User
 └── Streamlit Chat UI
      └── PDF Processor (Text Extraction)
           └── Embeddings + FAISS Vector Store
                └── Similarity Search
                     └── Ollama Local LLM
                          └── Streamed Answer

This project follows a standard RAG (Retrieval-Augmented Generation) pipeline.

Tech Stack:
Python 3.10+
Streamlit – UI
FAISS – Vector similarity search
Sentence Transformers – Embeddings
Ollama – Local LLM runtime
Mistral / DeepSeek – LLM models
PyPDF / PDFPlumber – PDF parsing

Requirements:
Before running the app, make sure you have:
Python 3.10 or above
Ollama installed locally

Installation & Setup:
1. Clone the repository
    git clone https://github.com/<your-username>/<repo-name>.git
    cd <repo-name>

2. create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate        # Linux / Mac
    venv\Scripts\activate           # Windows

3. Install Python dependencies
    pip install -r requirements.txt

4. Install Ollama
Download and install Ollama from:
    https://ollama.com/download

Verify installation:
    ollama --version

5. Pull a supported LLM model
Recommended:
    ollama pull mistral:7b-instruct

6. Start Ollama server
    ollama serve
Ollama runs locally on port 11434

7. Run the Streamlit app
    streamlit run ui/app.py


How to Use:
Upload a PDF using the sidebar
Wait for indexing to complete
Ask questions related to the PDF
Get answers generated only from the document
View page-level sources
Irrelevant questions return:
    the question is irrelavant

Important Notes:
This app does NOT use cloud APIs
Users must install Ollama locally
This project cannot be hosted publicly for free due to LLM runtime requirements
Intended for:
    Developer
    Researchers
    Local deployments
    Demonstration of RAG systems

Privacy & Security:
All processing happens locally
PDFs are not uploaded to any external service
No telemetry or analytics sent externally
Suitable for sensitive documents

Models Tested:
| Model                 | Notes                                |
| --------------------- | ------------------------------------ |
| `mistral:7b-instruct` | Best balance of speed & accuracy     |
| `deepseek-r1:1.5b`    | Lightweight, slower reasoning        |
| `llama3`              | Supported but weaker for document QA |

Project Structure:
pdf-chatbot/
│
├── core/
│   ├── pdf_processor.py
│   ├── embeddings.py
│   ├── qa_engine.py
│   ├── llm.py
│   └── analytics_logger.py
│
├── ui/
│   ├── app.py
│   └── dashboard.py
│
├── data/
│   ├── uploads/
│   ├── vectorstore/
│   └── analytics/
│
├── requirements.txt
└── README.md

Known Limitations:
Requires local machine resources (CPU/RAM)
Initial PDF indexing may take time for large documents
Not suitable for mobile or low-end devices
Not a hosted SaaS application

Future Improvements:
Dockerized setup
Multi-PDF support
User authentication
Hosted inference option (Hugging Face / GPU)
Better UI theming
Caching & faster retrieval

Author:
Nevin Thekkeparambil
Aspiring Data Scientist | AI & RAG Systems Developer | Data Analyst