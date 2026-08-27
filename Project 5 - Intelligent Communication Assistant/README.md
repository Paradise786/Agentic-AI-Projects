# Intelligent Communication Assistant

## Overview
The **Intelligent Communication Assistant** is an autonomous AI agent system designed to automate context-aware communication workflows. Powered by Large Language Models (LLMs via Groq) and LangChain tool-calling capabilities, the system intelligently analyzes incoming communication requests, determines intent and urgency, selects the appropriate communication channels (Email, Push Notifications, or both), synthesizes context-aware messages, validates output quality, and executes action tools.

---

## Problem Statement
In educational institutions and corporate organizations, dispatching urgent announcements, exam reschedule notices, project submission reminders, and emergency alerts often requires manual drafting, formatting, priority tagging, and multi-channel distribution. Manual handling leads to delays, inconsistent styling, missing details (placeholders left unreplaced), and misrouted messages.

**Solution:** An autonomous, AI-driven Communication Assistant that accepts natural language instructions, automatically classifies priority and target audience, formats channel-specific content, runs automated quality checks, and executes tools via LangChain structured function calling.

---

## Features
- **Cognitive Intent & Priority Classifier**: Uses Groq LLM (e.g., `llama-3.1-8b-instant`) to determine intent, priority level (Low, Normal, High, Urgent), and target audience.
- **Dynamic Multi-Channel Routing**: Automatically decides whether to route communications via Email, Push Notifications, or both based on urgency and content length.
- **Context-Aware Message Synthesizer**: Generates professional email subjects, bodies, push titles, and notification messages tailored to specific audiences without leaving unreplaced placeholder brackets.
- **Automated Validation Engine (QA Gate)**: Evaluates generated content against criteria including recipient presence, non-empty subjects, valid priority tagging, and absence of raw placeholder brackets.
- **LangChain Tool Calling Architecture**: Uses `@tool` decorated functions (`send_email_tool`, `send_push_notification`) invoked directly via `.invoke()` to simulate or execute real action dispatching.
- **Dual Execution Modes**:
  - **Live External API Mode**: Connects directly to Groq API for real LLM reasoning.
  - **Simulation Mode (Demo)**: Uses a local heuristic engine when offline or testing without API keys.
- **Interactive Stepper & Real-time Trace Monitor**: Visual 7-step execution workflow with live trace logs and execution metrics tracking.
- **CSV History Export**: Export complete execution logs and communication history to CSV.

---

## How It Works
1. **Instruction Input**: The user selects a quick scenario template or inputs a custom natural language request (e.g., *"Send a high-priority announcement to students about the rescheduled Midterm Exam of CS-301 to August 24th at 10:00 AM in Room 402."*).
2. **AI Reasoning & Structured JSON Output**: The LLM parses the request and emits a structured JSON object specifying `intent`, `priority`, `audience`, `channels`, `email`, and `push_notification` payloads.
3. **Quality Validation**: The built-in Validation Engine runs automated verification checks on the synthesized payloads.
4. **Tool Execution**: Depending on the selected channels, the agent invokes `send_email_tool` and/or `send_push_notification`.
5. **Preview & Log History**: Formatted email and push notification mockups are presented in real time, and execution history is recorded for metrics and CSV export.

---

## Agent Workflow
The 7-step cognitive workflow executed by the assistant:

1. **Receiving Request**: Captures user prompt and initializes session state.
2. **AI Cognitive Analysis**: Sends system prompt & user query to Groq LLM / Local Simulator.
3. **Decision & Routing**: Extracts structured intent, priority, audience, and target channels.
4. **Message Synthesis**: Generates professional copy for email and push channels.
5. **Quality Gate Check**: Runs validation rules (recipient, subject, placeholders, priority consistency).
6. **Tool Execution**: Invokes LangChain tools (`send_email_tool`, `send_push_notification`).
7. **Finalization**: Updates metrics, dashboard logs, and renders communication previews.

---

## Tool Calling

Tool calling is the core mechanism of Task 5. The agent does not merely produce static text; it determines **action decisions** and triggers dedicated tool functions using LangChain's `@tool` decorator.

```text
User Request
     ↓
AI Agent analyzes request
     ↓
Selects appropriate tool
     ↓
Prepare Email / Notification
     ↓
Send or Return Communication Result
```

### Defined Tools in Code:

1. **`send_email_tool(recipient, subject, body)`**:
   - **Role**: Formats and dispatches structured emails to target recipients.
   - **Invocation**: `send_email_tool.invoke({"recipient": ..., "subject": ..., "body": ...})`

2. **`send_push_notification(target_user, message)`**:
   - **Role**: Formats and dispatches short push notifications to mobile/web clients.
   - **Invocation**: `send_push_notification.invoke({"target_user": ..., "message": ...})`

---

## Technologies Used
- **Frontend / UI**: [Streamlit](https://streamlit.io/) (with custom CSS styling)
- **LLM Orchestration**: [LangChain](https://www.langchain.com/) (`langchain-groq`, `langchain-core`)
- **LLM Provider**: [Groq API](https://groq.com/) (`llama-3.1-8b-instant`, `llama3-70b-8192`)
- **Data Handling**: [Pandas](https://pandas.pydata.org/)
- **Environment Management**: `python-dotenv`

---

## Installation

1. **Clone or Navigate to Task 5 directory**:
   ```bash
   cd "Task5"
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # Activate on Windows:
   venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Variables

Copy `.env.example` to `.env` and insert your actual Groq API key:

```bash
cp .env.example .env
```

`.env` content:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
EMAIL_ADDRESS=your_email_here
EMAIL_PASSWORD=your_email_password_here
```

> ⚠️ **IMPORTANT**: Never commit your `.env` file containing real API keys or passwords to GitHub. Ensure `.env` is listed in `.gitignore`.

---

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

1. (Optional) Enter your **Groq API Key** in the sidebar expander under **🔑 LLM Credentials**.
2. Select an **Execution Mode**:
   - `🟢 Simulation Mode (Demo)`: Runs locally without API keys.
   - `🔵 Live External API`: Uses live Groq LLM inference.
3. Select a **Quick Scenario Template** or type a custom request in the input box.
4. Click **🚀 Run Communication Agent**.
5. View real-time stepper progress, trace logs, tool dispatch status, validation gate results, and generated email/push previews.

---

## Project Structure

```text
Task5/
├── app.py                 # Main Streamlit application & agent logic
├── requirements.txt       # Python package dependencies
├── .env                   # Environment variables (secret - gitignored)
├── .env.example           # Environment template example
├── .gitignore             # Git ignore file for secrets and cache
└── README.md              # Project documentation & Tool Calling guide
```
