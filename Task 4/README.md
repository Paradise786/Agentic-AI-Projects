# 🎓 University of Layyah AI Assistant & Document Intelligence System

An enterprise-grade **Document Intelligence & Retrieval-Augmented Generation (RAG) System** built with **Streamlit**, **LangChain**, **Groq LLM**, **ChromaDB**, and **Pydantic**.

---

## 🌟 Key Features

- 📤 **Multi-Document Batch Ingestion**: Upload and process multiple `PDF`, `TXT`, and `MD` files concurrently.
- 🔄 **7-Stage Processing Pipeline**:
  1. Document Parsing & Text Extraction (`pypdf`, UTF-8 decoder)
  2. Cleaning & Recursive Text Chunking (`RecursiveCharacterTextSplitter`)
  3. LLM Structured Metadata Extraction (`ChatGroq`)
  4. Strict Schema Validation (`Pydantic`)
  5. Dense Vector Embeddings (`HuggingFace all-MiniLM-L6-v2`)
  6. Hybrid Vector Indexing (`ChromaDB`)
  7. RAG Assistant Query Readiness
- 🧠 **Structured Metadata & AI Analysis**:
  - Document Title & Classification
  - Author / Organization Extraction
  - Sentiment & Tone Analysis
  - Readability Complexity Scoring
  - Named Entities Detection
- 🛡️ **Pydantic Schema Validation**: Ensures high data integrity and standard JSON formatting for all extracted document metadata.
- 💬 **RAG Knowledge Assistant & Source Citations**:
  - Contextual Q&A powered by Groq Llama 3 models
  - Accurate document source citations
  - One-click suggested query presets
- ⚖️ **Document Comparison Engine**: Compare two documents side-by-side on metadata, tone, and classifications.
- 📊 **Analytics & Reports**:
  - Real-time KPI metrics (Documents count, Chunks indexed, Pipeline status)
  - Executive JSON report download

---

## 🏗️ Project Structure

```text
Task-4/
│
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
└── README.md           # Documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- A valid [Groq API Key](https://console.groq.com/)

### 2. Clone / Open Directory
```bash
cd "c:\xampp\htdocs\xampp\internship lab1\Task 4"
```

### 3. Set Up Virtual Environment
```bash
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Configuration
Create a `.env` file from `.env.example`:
```bash
copy .env.example .env
```
Add your Groq API key inside `.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 6. Run the Application
```bash
streamlit run app.py
```

---

## 🛠️ Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **LLM Orchestration**: [LangChain](https://www.langchain.com/) / [LangChain Groq](https://python.langchain.com/docs/integrations/chat/groq/)
- **LLM Inference**: Groq (`llama-3.1-8b-instant`, `llama3-70b-8192`)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **PDF Extraction**: [pypdf](https://pypdf.readthedocs.io/)
