# 🤖 Multi-Agent Problem Solving System (LangGraph + Groq + Streamlit)

> **Agentic AI Short Course — University of Layyah (Task 3 / Project 03)**

A collaborative multi-agent architecture built with **LangGraph** and **Groq LPU LLMs**, deployed as a modern interactive dashboard using **Streamlit**.

---

## 📌 Project Overview

* **Project Name**: Multi-Agent Problem Solving System
* **Course / Context**: Agentic AI Course (University of Layyah)
* **Architecture Style**: Multi-Agent Collaboration Graph (LangGraph StateGraph)
* **LLM Engine**: Groq High-Speed Inference (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.6-27b`)

---

## 🌍 Real-World Problem

Solving complex real-world problems—such as designing high-traffic cloud architectures, conducting business migration analyses, or formulating technical strategies—requires distinct phases of cognition:
1. **Fact-finding & research**
2. **Critical trade-off analysis & risk evaluation**
3. **Actionable execution planning**

A single LLM prompt often struggles with context bloat, leading to superficial responses, missed edge cases, or hallucinated facts. Manual division of work across separate chats is inefficient and hard to track.

---

## 💡 The Solution

This system implements an **autonomous multi-agent collaborative pipeline**. Instead of relying on a single prompt response, the user problem is handed over to a team of specialized AI agents built on **LangGraph**. The agents pass state sequentially, building upon each other's work to deliver a thoroughly researched, critically analyzed, and execution-ready solution.

---

## 🤖 Agent Roles & Architecture

```
User Problem Input
       │
       ▼
 🧠 Supervisor Agent  ──► Initial Planning & Routing
       │
       ▼
 🔍 Research Agent    ──► Gathers domain facts & background data
       │
       ▼
 📊 Analysis Agent    ──► Evaluates pros/cons, trade-offs & risks
       │
       ▼
 ⚡ Execution Agent   ──► Formulates actionable step-by-step plan
       │
       ▼
 🏆 Final Synthesis   ──► Multi-tab UI & Downloadable Reports
```

| Agent Icon | Agent Name | Role & Responsibility |
| :--- | :--- | :--- |
| 🧠 | **Supervisor Agent** | Analyzes user problem, sets task breakdown, monitors phase transitions, and synthesizes final output. |
| 🔍 | **Research Agent** | Gathers comprehensive background information, technical context, and domain-specific facts. |
| 📊 | **Analysis Agent** | Performs critical evaluation, identifies pros/cons, assesses risks, feasibility, and technical trade-offs. |
| ⚡ | **Execution Agent** | Translates insights into concrete, step-by-step execution plans and architectural recommendations. |

---

## 📥 Input Features

* **Custom Problem Statement**: Large text box for describing complex tasks.
* **Quick Task Templates**:
  * 🏗️ **Architecture**: Microservices & cloud platform comparisons.
  * 📊 **Business Analysis**: Cost-benefit migration & ROI analysis.
  * 🔍 **Research Data**: Vector database benchmarks (Chroma, Pinecone, Milvus).
  * 🧩 **Problem Solver**: API rate-limiting & pipeline bottleneck mitigation strategies.

---

## ⚙️ Processing Workflow

1. **State Graph Initializing**: `AgentState` dictionary maintains `problem`, `research_output`, `analysis_output`, `final_output`, and `current_agent`.
2. **Sequential Graph Execution**:
   * `supervisor` ➔ `researcher` ➔ `analyzer` ➔ `executor` ➔ `END`
3. **Execution Tracking**: Live latency tracking (seconds) and token count estimations (`~approx_tokens`).
4. **Error Handling**: Graceful API error handling for model permissions and missing environment keys.

---

## 📤 Output & Features

* **Structured Agent Outputs**: Visual cards for Research, Analysis, and Execution outputs.
* **Performance Metrics Bar**: Real-time tracking of Execution Latency, Approx Tokens, Active Model, and System Status.
* **Interactive Follow-up Chat**: Chat interface enabling post-solution queries directly with the agent memory.
* **Report Exports**:
  * 📥 **JSON Logs**: `multi_agent_logs.json` for full trajectory tracking.
  * 📄 **Markdown Report**: `agent_report.md` for client or academic submission.

---

## 🛠️ Technologies Used

* **Python 3.10+**
* **LangGraph**: StateGraph orchestration for multi-agent workflows.
* **LangChain-Groq**: Integration for Groq LPU inference models.
* **Streamlit**: Web dashboard framework.
* **Python-Dotenv**: Environment variable management.

---

## ⚙️ Installation Steps

### 1. Clone or Navigate to Project Directory
```bash
cd project-03
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and add your Groq API key:
```bash
cp .env.example .env
```
In `.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```
*(Alternatively, enter your Groq API key directly in the Streamlit sidebar.)*

---

## 🚀 Run Command

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.
