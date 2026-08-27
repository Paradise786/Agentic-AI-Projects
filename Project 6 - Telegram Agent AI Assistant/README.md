# ⬡ NEXUS — Telegram Autonomous Agent Platform

> **Task 6: Telegram Agentic AI Assistant**  
> Production-style Autonomous Telegram Chatbot and Agent Operations Dashboard powered by Multi-Agent Workflows, RAG Architecture, and Dynamic Tool Calling.

---

## 📌 Project Overview

**NEXUS** is an autonomous agentic AI platform designed for Telegram integration. It enables users to send natural language requests or complex multi-step missions, which are processed autonomously by a network of specialized agents working behind the scenes.

The system incorporates an **Agent Operations Dashboard** built with Streamlit, providing real-time workflow tracking, live execution monitoring, knowledge base (RAG) query management, and system health diagnostics.

---

## 🏗️ Architecture & Agent Patterns

NEXUS uses a multi-agent orchestration architecture where tasks are decomposed, routed, executed using dynamic tools, validated, and returned to the user via Telegram.

```text
┌────────────────┐     ┌─────────────────────┐     ┌───────────────────────┐
│                │     │  Intent Classifier  │     │    Planner Agent      │
│  Telegram User ├────►│       Agent         ├────►│  (Decomposes Task)    │
│                │     └─────────────────────┘     └──────────┬────────────┘
└───────▲────────┘                                            │
        │                                                     ▼
┌───────┴────────┐     ┌─────────────────────┐     ┌───────────────────────┐
│  Telegram Bot  │◄────┤  Validation Agent   │◄────┤  Tool Execution & RAG │
│    Delivery    │     │  (Safety & Checks)  │     │  (ChromaDB + Search)  │
└────────────────┘     └─────────────────────┘     └───────────────────────┘
```

### 🤖 Specialized Agents
1. **Orchestrator Agent:** Master coordinator that routes user requests, assigns tasks, and maintains session context.
2. **Planner Agent:** Decomposes complex user missions into structured step-by-step execution plans.
3. **Research Agent:** Performs real-time web searches and information cross-referencing.
4. **Document & RAG Agent:** Extracts text from PDF, DOCX, TXT, and CSV files and performs vector semantic retrieval via ChromaDB.
5. **Validation & Guard Agent:** Validates output consistency, formats data, and enforces safety constraints.

---

## 🛠️ Key Features

- **Autonomous Mission Builder:** Process complex multi-step instructions (e.g., *"Read admission PDF, extract deadlines, schedule reminders, and send summary to Telegram"*).
- **RAG Knowledge Base:** Index and query documents using ChromaDB vector database with SQLite fallback token matching.
- **Dynamic Tool Registry:** Extensible tool system featuring Web Search, PDF/DOCX Readers, Calculator, and Summarizer.
- **Task & Reminder Scheduling:** Background job scheduling powered by APScheduler.
- **Operations Dashboard:** Soft-pastel UI Streamlit dashboard featuring System Overview, Agent Hub, Tools Registry, Document RAG, and System Diagnostics.

---

## 🚀 Technologies & Libraries

- **Language & Runtime:** Python 3.10+
- **Frameworks:** LangChain / LangGraph Agentic Workflows
- **LLM Provider:** Local Ollama (llama3) with Demo Mode Simulation fallback
- **Vector Database:** ChromaDB & SentenceTransformers
- **Relational Database:** SQLite & SQLAlchemy ORM
- **UI & Dashboard:** Streamlit
- **Task Scheduler:** APScheduler
- **Telegram Bot API:** python-telegram-bot

---

## 📂 Directory Structure

```text
Task 6/
├── .env                  # Environment Variables (Local)
├── .env.example          # Environment Configuration Template
├── .gitignore            # Git Exclusions
├── README.md             # Project Documentation
├── requirements.txt      # Python Dependencies
└── app/
    ├── __init__.py
    ├── config.py         # Global App Settings
    ├── database.py       # SQLAlchemy Engine & Session
    ├── models.py         # Database ORM Models
    ├── schemas.py        # Pydantic Schemas
    ├── agents/
    │   └── base.py       # BaseAgent Architecture Contract
    ├── dashboard/
    │   └── app.py        # Streamlit NEXUS Operations Dashboard
    ├── services/
    │   ├── llm_service.py      # Ollama & LLM Query Manager
    │   ├── rag_service.py      # ChromaDB Document Retrieval
    │   └── reminder_service.py # APScheduler Job Scheduler
    └── tools/
        ├── registry.py    # Dynamic Tool Registry & BaseTool
        ├── math_tool.py   # Calculator Tool
        ├── search_tool.py # Web Search Tool
        └── doc_tools.py   # PDF, DOCX, TXT & Summarizer Tools
```

---

## ⚙️ Installation & Setup

### 1. Clone & Navigate to Project
```bash
cd "Task 6"
```

### 2. Create & Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your keys:
```bash
cp .env.example .env
```
*(Optionally set your `TELEGRAM_BOT_TOKEN`. If not set, system automatically runs in simulated Demo Mode).*

---

## 🏃 Running the Application

### Launch Streamlit Dashboard
```bash
streamlit run app/dashboard/app.py
```
Open your browser at: **`http://localhost:8510`** (or printed port).

---

## 📜 License & Acknowledgments

Developed as part of **Task 6 — Agentic AI Internship Program**.  
Built with Python, Streamlit, SQLAlchemy, ChromaDB, and python-telegram-bot.
