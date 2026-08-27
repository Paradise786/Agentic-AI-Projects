# Project 1: Intelligent Academic Task Execution Agent

**Course:** Agentic AI (Short Course Program)  
**Institution:** University of Layyah (ULSCP)  
**Instructor:** Ma'am Nabiha Komal  

## 📌 Overview
This application implements an autonomous **Task Execution Agent** designed around the **ReAct (Reasoning + Acting)** design pattern using **LangChain** and **Groq LLM**. The agent breaks high-level academic goals into sub-tasks, dynamically binds execution tools, and reasons over tool observations to generate final outcomes.

## 🏗️ Design Pattern Architecture

```
[User Input / Goal]
        │
        ▼
┌──────────────────┐
│  Streamlit UI    │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     LangChain ReAct Agent Engine        │
│  (Thought ➔ Action ➔ Observation Loop)  │
└───────┬──────────────┬─────────────┬────┘
        │              │             │
        ▼              ▼             ▼
┌──────────────┐ ┌───────────┐ ┌────────────┐
│ GPA Calc Tool│ │ Schedule  │ │ Web Search │
└──────────────┘ └───────────┘ └────────────┘
```

## 🚀 Key Features
- **ReAct Execution Loop:** Autonomous step-by-step reasoning using standard ReAct prompts.
- **Dynamic Tool Calling:** Integration of a custom GPA calculator, University Academic Schedule parser, and DuckDuckGo live web search.
- **Interactive UI:** Built with Streamlit for seamless user goal inputs and visual progress output.

## ⚙️ Setup & Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```
