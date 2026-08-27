# 🎓 Project 1 — University of Layyah AI Knowledge Assistant

An intelligent Retrieval-Augmented Generation (RAG) application that converts University of Layyah official documents into a persistent AI knowledge base. Users can upload PDF documents and ask natural language questions — the system retrieves relevant context and generates accurate, grounded answers using a Groq LLM.

---

## 🌟 Project Purpose

> Upload University of Layyah PDFs once → System indexes them into ChromaDB → Ask multi-turn questions → Get accurate, document-grounded AI answers.

This project demonstrates a complete **end-to-end RAG pipeline** with persistent vector storage and conversational memory.

---

## ✨ Key Features

- 📄 **Multi-PDF Upload & Indexing** — Drag-and-drop multiple University PDFs at once
- 🗄️ **Persistent ChromaDB Vector Store** — Documents remain indexed across sessions
- 🔍 **Semantic Similarity Search** — Retrieves most relevant document chunks per query
- 💬 **Conversational Memory** — Maintains multi-turn chat history
- 📑 **Source Citations** — Displays exact source document and page number for every answer
- 🔄 **RAG Pipeline Visual** — Shows real-time workflow: Upload → Extract → Chunk → Embed → Store → Retrieve → Generate
- 📥 **Export Chat History** — Download conversation logs in TXT or JSON format
- 🟢 **Knowledge Base Status** — Live indicators for DB state, document count, and memory

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Frontend UI** | Streamlit |
| **LLM Engine** | Groq API (ChatGroq) |
| **Vector Database** | ChromaDB (Persistent) |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **PDF Loader** | LangChain PyPDFLoader |
| **Text Splitter** | RecursiveCharacterTextSplitter |
| **Framework** | LangChain LCEL |

---

## 🔄 RAG Pipeline Architecture

```text
📄 PDF Upload
     │
     ▼
📝 Text Extraction (PyPDFLoader)
     │
     ▼
✂️ Text Chunking (RecursiveCharacterTextSplitter)
     │
     ▼
🧠 Embedding Generation (all-MiniLM-L6-v2)
     │
     ▼
🗄️ ChromaDB Vector Store (Persistent)
     │
     ▼ (At query time)
🔍 Semantic Similarity Search
     │
     ▼
🤖 Groq LLM Answer Generation
     │
     ▼
📋 Answer + Source Citations
```

---

## 🚀 Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in this folder:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

Or enter your API key directly in the sidebar when the app launches.

### 3. Add University Logo (Optional)

Place a `logo.png` file in this folder. It will be displayed in the sidebar automatically.

### 4. Launch the Application

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```text
pdf_rag_app/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env                # API Keys (do NOT commit to GitHub)
├── .gitignore          # Git ignore rules
├── logo.png            # University logo (optional)
└── chroma_db/          # Persistent ChromaDB vector store (auto-created)
```

---

## 📖 How to Use

1. **Launch** the app with `streamlit run app.py`
2. **Enter** your Groq API Key in the sidebar
3. **Upload** one or more University of Layyah PDF documents using the Knowledge Base Manager
4. Click **⚡ Process & Index** to embed and store documents
5. **Ask questions** in the query box about the uploaded documents
6. View the **AI Answer**, **Retrieved Sources**, and **Conversation History**

---

## 🔐 Security Note

> **Never commit your `.env` file or API keys to GitHub.**
> The `.gitignore` file already excludes `.env` from version control.
