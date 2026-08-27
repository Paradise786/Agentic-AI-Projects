# 🎓 Project 2 — Academic Advisor Decision Agent

An Agentic RAG application that combines **ChromaDB Vector Search** and **LangGraph StateGraph Workflow** to provide automated, compliance-validated academic advisement, course recommendations, GPA optimization plans, and prerequisite checks.

---

## 🛠️ Architecture & Tech Stack

- **Frontend UI:** Streamlit (Custom Academic Cyan & Navy Dark/Light Theme)
- **Agent Workflow:** LangGraph (`StateGraph` orchestration for multi-stage decision pipeline)
- **Vector Database:** ChromaDB (Persistent local vector store)
- **LLM Engine:** Groq API (`ChatGroq` - LLaMA 3.1 / Mixtral)
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2`
- **PDF Ingestion:** PyPDF Loader + Recursive Text Splitter

---

## 🔄 LangGraph Decision Workflow

```text
User Query + Student Profile
            │
            ▼
┌─────────────────────────┐
│ 🔍 1. ChromaDB Retriever │  (Fetches course catalog rules & prerequisites)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 📊 2. Situation Analyzer│  (Analyzes student standing vs degree requirements)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 🎯 3. Recommendation    │  (Generates course schedule & GPA roadmap)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ ✅ 4. Rule Validator    │  (Validates prerequisites & credit limits)
└───────────┬─────────────┘
            │
            ▼
   Final Academic Decision
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file or enter your key in the UI sidebar:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```

---

## 🌟 Key Features

- **Document Ingestion:** Upload course catalogs, degree roadmaps, and university rule PDFs.
- **Student Profile Context:** Input major, semester, current GPA, target GPA, and completed courses.
- **Visual Graph Execution:** Real-time visibility into each node of the LangGraph pipeline.
- **Compliance Validation:** Automated checks against prerequisites, workload caps, and degree rules.
- **Export & History:** Download advisement reports in JSON or TXT format.
