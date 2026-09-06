# 🛡️ CyberGuard AI — Security Threat Advisory Assistant

CyberGuard AI is an AI-powered security advisory assistant built for SOC
(Security Operations Center) analysts and everyday users who receive
suspicious emails, alerts, or logs and need a quick, reliable assessment of
whether they represent a real threat — and what to do about it.

## 1. Problem & Target User

**Target user:** A junior SOC analyst or a regular employee who receives a
suspicious email/log/alert and is unsure whether it is dangerous, what
technique it represents, and what steps to take next.

**Problem:** Manually cross-referencing every suspicious email or alert
against threat intelligence frameworks (like MITRE ATT&CK) and the latest
threat news is slow and requires expertise many users don't have.

**Solution:** CyberGuard AI combines a curated internal knowledge base
(RAG), real-time web search, and OCR (for screenshots) inside an agentic
workflow to produce a structured advisory report — classification, why it's
dangerous, and recommended next steps — in seconds.

## 2. Architecture

```
User Input (text or image)
        │
        ▼
   [OCR, if image]  ──►  extracted text
        │
        ▼
     Security Agent (LangChain + Gemini)
        │
        ├──► retrieve_security_knowledge (RAG / FAISS)
        │
        └──► search_current_threats (Tavily web search grounding)
        │
        ▼
  Structured Advisory (Severity + Classification + Mitigation)
        │
        ▼
  Streamlit UI (badge, PDF export, history)
        │
        ▼
  LangSmith (traces every step)
```

## 3. Tech Stack

- **LLM:** Google Gemini (`gemini-3.6-flash`) via `langchain-google-genai`
- **Agent framework:** LangChain (`create_agent`) + LangGraph
- **Vector database:** FAISS
- **Embeddings:** Gemini (`gemini-embedding-001`)
- **Web search grounding:** Tavily
- **OCR:** Tesseract (via `pytesseract`)
- **Frontend:** Streamlit (custom CSS)
- **Observability:** LangSmith
- **PDF export:** fpdf2

## 4. Project Structure

```
cyberguard-ai/
├── app.py                     # Streamlit frontend
├── agents/
│   └── security_agent.py      # Main agent: system prompt + tools + LLM
├── tools/
│   ├── ocr_tool.py            # Image → text extraction (Tesseract)
│   └── search_tool.py         # Web search grounding (Tavily)
├── rag/
│   ├── build_vectorstore.py   # Builds the FAISS index from data/
│   └── test_retrieval.py      # Standalone retrieval test script
├── data/                      # Knowledge base source documents (.txt)
├── faiss_index/               # Generated vector store (created by build_vectorstore.py)
├── .env.example                # Required environment variables (no real keys)
├── requirements.txt
└── README.md
```

## 5. Setup Instructions

### Prerequisites
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed
  (Windows default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- API keys: Google Gemini, Tavily, LangSmith

### Installation

```bash
git clone https://github.com/belal-rifat/cyberguard-ai.git
cd cyberguard-ai
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# venv\Scripts\Activate.ps1    # Windows PowerShell
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=cyberguard-ai
```

### Build the RAG knowledge base (run once)

```bash
python rag/build_vectorstore.py
```

### Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## 6. How RAG Works Here

1. **Data:** 5 curated documents in `data/` covering common attack
   techniques (Phishing, Credential Dumping, Ransomware, Brute Force,
   Malicious Macros), written in a MITRE ATT&CK-inspired format.
2. **Chunking:** Each document is split into ~500-character chunks with
   50-character overlap (`RecursiveCharacterTextSplitter`).
3. **Embedding:** Each chunk is embedded using Gemini's
   `gemini-embedding-001` model.
4. **Storage:** Embeddings are stored in a local FAISS index
   (`faiss_index/`).
5. **Retrieval:** At query time, the agent's `retrieve_security_knowledge`
   tool embeds the user's query and retrieves the top-3 most similar
   chunks, which are passed to the LLM as context before it answers.

## 7. Agent & Tools

The agent (`agents/security_agent.py`) is built with LangChain's
`create_agent`, given a system prompt instructing it to act as a SOC
advisory assistant, and two tools:

- `retrieve_security_knowledge` — queries the FAISS knowledge base
- `search_current_threats` — queries the web via Tavily for anything
  recent or not covered by the internal knowledge base

The agent decides autonomously which tool(s) to call based on the user's
query, then synthesizes a final structured advisory.

## 8. LangSmith Tracing

Every agent run is automatically traced to LangSmith (project:
`cyberguard-ai`) via the `LANGSMITH_TRACING` / `LANGSMITH_API_KEY`
environment variables. Traces show the full execution flow: the incoming
query, which tools were called (and with what arguments), the retrieved
context, and the final LLM response.

**Example public trace(s):**
- Text query (phishing example): https://smith.langchain.com/public/bf3a4ee4-f43b-436a-9125-00ee9b432fad/r/01a072e4-acf5-7591-a208-783b0e4ad8b7

## 9. Known Limitations / Future Improvements

- Knowledge base currently covers 5 attack techniques; could be expanded
  with the full MITRE ATT&CK dataset.
- Severity classification is LLM-inferred, not rule-based.
- No persistent database — history resets when the Streamlit session ends.

## 10. Screenshots

**Home — Quick examples & text query**
![Home tab](screenshots/01_home_quick_examples.png)

**Screenshot upload & OCR extraction**
![OCR upload](screenshots/02_ocr_image_upload.png)

**Generated advisory report with severity badge**
![Advisory report](screenshots/03_advisory_report.png)

**PDF export of the report**
![PDF export](screenshots/04_pdf_export.png)

**Session history**
![History tab](screenshots/05_history_tab.png)

**About tab**
![About tab](screenshots/06_about_tab.png)
