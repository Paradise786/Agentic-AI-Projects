# CivicFlow AI — Agentic Municipal Complaint System

## Overview
CivicFlow AI is an intelligent municipal complaint routing system built with Streamlit, LangGraph, and Groq LLM. It automates the triage, classification, risk assessment, and escalation of civic issues.

## Why Agentic Architecture?
Traditional rule-based or single-prompt LLM systems fail in municipal triage due to unpredictable inputs, complex multi-department jurisdictions, and strict safety requirements. CivicFlow adopts an **Agentic Architecture** using LangGraph to provide:
- **Separation of Concerns:** Discrete specialized agent nodes handle input validation, department routing, risk/SLA evaluation, and summarization.
- **Stateful Control Flow:** LangGraph state machine maintains context across stages with conditional branching and failure recovery.
- **Guardrails & Safety (HITL):** Automatic rejection of malicious/adversarial inputs and escalation of low-confidence or high-risk cases to human authorities.
- **Auditable Decisions:** Each agent step produces structured Pydantic outputs recorded in transparent audit logs.

## Architecture Diagram
```
        Citizen Complaint
               │
               ▼
       ┌──────────────┐
       │  Guardrails  │ ──(Unsafe)──► [Rejection / Alert]
       └──────┬───────┘
              │ (Safe)
              ▼
       ┌──────────────┐
       │  Classifier  │ ◄── Groq LLM (Structured Pydantic Output)
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  Risk + SLA  │ ◄── Priority & SLA Calculator
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  HITL Gate   │ ◄── Admin escalation if High Risk / Ambiguous
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Notify + DB  │ ◄── Ticket persisted & User alerted
       └──────────────┘
```

## Features
- **Citizen Portal**: Multi-step wizard to report municipal issues with location pinpointing and evidence upload.
- **AI Agent Workflow**: LangGraph state machine powered by Groq (`llama-3.3-70b-versatile`) performing Intake Guardrails, Department Classification, Risk Assessment, and TL;DR Summarization.
- **Authority / Admin Hub**: Live triage, HITL safety escalations, real-time analytics, and transparent AI agent audit trails.
- **Citizen Copilot**: Integrated conversational assistant to answer questions about civic tickets and municipal processes.

## Project Structure
```
civicflow/
├── app.py                # Streamlit UI application
├── civic_graph.py        # LangGraph agent workflow & state machine
├── core_agents.py        # Structured Pydantic LLM prompts & agents
├── guardrails.py         # Pydantic input security & validation guardrails
├── llm_config.py         # Groq LLM setup
├── database.py           # SQLAlchemy database models & operations
├── settings.py           # Centralized configuration & SLA matrix
├── chatbot_engine.py     # AI Copilot assistant
├── .env.example          # Environment variables template
└── requirements.txt      # Python dependencies
```

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Groq API Key (from [console.groq.com](https://console.groq.com))

### 2. Setup Environment
```bash
# Clone or open repository
cd "c:/xampp/htdocs/xampp/internship lab1/no name"

# Create and activate virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure `.env`
Copy `.env.example` to `.env` and enter your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_key_here
LANGCHAIN_TRACING_V2=false
DATABASE_URL=sqlite:///./civicflow.db
CHROMA_DB_PATH=./chroma_store
```

### 4. Run Application
```bash
streamlit run app.py
```

## ⚠️ Known Limitations & Future Work

**Current Limitations:**
- Telemetry data is simulated for demo purposes (real LangSmith integration planned)
- Vision evidence verification not yet implemented
- SOP RAG ingestion pending (Phase 2)

**Future Enhancements:**
- Geo-temporal hotspot prediction
- Urdu/Roman Urdu intake normalization
- Real email/push notifications (SendGrid/Pushover)
- SLA breach watchdog agent

## License
MIT License.
