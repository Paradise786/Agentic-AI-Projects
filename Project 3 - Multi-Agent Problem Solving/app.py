import os
import time
import json
import base64
import streamlit as st
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Multi-Agent Problem Solving System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATES -----------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "workflow_logs" not in st.session_state:
    st.session_state["workflow_logs"] = []
if "current_phase" not in st.session_state:
    st.session_state["current_phase"] = "Waiting"
if "selected_template" not in st.session_state:
    st.session_state["selected_template"] = ""
if "agent_statuses" not in st.session_state:
    st.session_state["agent_statuses"] = {
        "Supervisor": "Idle",
        "Research": "Idle",
        "Analysis": "Idle",
        "Execution": "Idle"
    }
if "followup_messages" not in st.session_state:
    st.session_state["followup_messages"] = []

# ----------------- LOAD LOGO FOR SIDEBAR ONLY -----------------
possible_paths = ["agent_logo.png", "./agent_logo.png", "logo.png", "./logo.png"]
logo_path = None
for path in possible_paths:
    if os.path.exists(path):
        logo_path = path
        break

logo_base64 = ""
if logo_path:
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")

# ----------------- STYLING & CLEAN SIDEBAR -----------------
st.html("""
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: linear-gradient(135deg, #E6F8F3 0%, #E0F2FE 50%, #FCE7F3 100%) !important;
        color: #0F172A !important;
        font-family: 'Inter', sans-serif !important;
        overflow-x: hidden !important;
    }

    section[data-testid="stSidebar"], [data-testid="stSidebarUserContent"] {
        background: linear-gradient(180deg, #EAF8F5 0%, #E2F2FE 100%) !important;
        border-right: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
    }

    div[data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        color: #0284C7 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stSidebar"] .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.5) !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid #CBD5E1 !important;
        border-top: none !important;
    }

    .screen-bg-animation {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }

    @keyframes robotSlowRise {
        0% { transform: translateY(105vh) scale(0.7) rotate(0deg); opacity: 0; }
        15% { opacity: 0.55; }
        85% { opacity: 0.55; }
        100% { transform: translateY(-10vh) scale(1.1) rotate(10deg); opacity: 0; }
    }

    .floating-robot-agent {
        position: absolute;
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255, 255, 255, 0.85);
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        animation: robotSlowRise 15s linear infinite;
        z-index: 1;
    }

    .robot-1 { left: 8%; animation-duration: 15s; animation-delay: 0s; }
    .robot-2 { left: 24%; animation-duration: 17s; animation-delay: 3s; }
    .robot-3 { left: 40%; animation-duration: 14s; animation-delay: 1.5s; }
    .robot-4 { left: 62%; animation-duration: 18s; animation-delay: 5s; }
    .robot-5 { left: 78%; animation-duration: 16s; animation-delay: 2.5s; }
    .robot-6 { left: 90%; animation-duration: 16.5s; animation-delay: 4s; }

    [data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 2;
    }

    .hero-header {
        background: linear-gradient(135deg, #0EA5E9 0%, #10B981 35%, #8B5CF6 70%, #EC4899 100%) !important;
        border-radius: 14px !important;
        padding: 24px 28px !important;
        color: #FFFFFF !important;
        margin-bottom: 20px !important;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.2) !important;
    }
    .hero-header h1 {
        color: #FFFFFF !important;
        margin: 0 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    .hero-header p {
        color: #F1F5F9 !important;
        margin: 6px 0 0 0 !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
    }

    .section-title {
        color: #0284C7;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        margin-bottom: 10px !important;
        margin-top: 20px !important;
    }

    .agent-card {
        background: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        color: #0F172A !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04) !important;
    }

    .metrics-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    .metric-pill {
        flex: 1;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(8px);
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .metric-pill-label {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-pill-value {
        font-size: 1.05rem;
        color: #0F172A;
        font-weight: 700;
    }

    .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #0EA5E9 0%, #10B981 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 9px 20px !important;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #10B981 0%, #8B5CF6 100%) !important;
    }

    .sidebar-card-box {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        font-size: 0.86rem !important;
        color: #0F172A !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
    }
</style>

<div class="screen-bg-animation">
    <div class="floating-robot-agent robot-1">🤖</div>
    <div class="floating-robot-agent robot-2">🤖</div>
    <div class="floating-robot-agent robot-3">🤖</div>
    <div class="floating-robot-agent robot-4">🤖</div>
    <div class="floating-robot-agent robot-5">🤖</div>
    <div class="floating-robot-agent robot-6">🤖</div>
</div>
""")

# ----------------- SIDEBAR -----------------
with st.sidebar:
    if logo_path:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 15px; background: rgba(255,255,255,0.8); border-radius: 12px; border: 1px solid #CBD5E1; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <img src="data:image/png;base64,{logo_base64}" style="width: 100%; height: 140px; object-fit: cover; display: block;">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ 'agent_logo.png' image file not found in the script folder!")

    with st.expander("⚙️ **Engine & Model Controls**", expanded=True):
        env_api_key = os.getenv("GROQ_API_KEY", "")
        groq_api_key = st.text_input("Groq API Key", type="password", value=env_api_key, placeholder="gsk_...")
        selected_model = st.selectbox(
            "Model Engine",
            ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b"],
            index=0
        )
        temperature_val = st.slider("Agent Creativity (Temperature)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    st.markdown("---")
    st.markdown("### 🤖 Agent List")
    agents_list = [
        ("🧠", "Supervisor"),
        ("🔍", "Research"),
        ("📊", "Analysis"),
        ("⚡", "Execution")
    ]
    for icon, agent_name in agents_list:
        st.markdown(f"""
            <div class="sidebar-card-box">
                <span>{icon} &nbsp;<b>{agent_name}</b></span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔄 Workflow Phase")
    phases = ["Waiting", "Planning", "Researching", "Analyzing", "Executing", "Completed"]
    current_p = st.session_state["current_phase"]
    for p in phases:
        is_active = (p == current_p)
        prefix = "👉" if is_active else "•"
        text_color = "#0284C7" if is_active else "#0F172A"
        font_wt = "600" if is_active else "400"
        st.markdown(f"""
            <div class="sidebar-card-box" style="border-color: {'#0284C7' if is_active else '#CBD5E1'}; background: {'rgba(14, 165, 233, 0.08)' if is_active else 'rgba(255, 255, 255, 0.9)'};">
                <span style="color: {text_color}; font-weight: {font_wt};">{prefix} &nbsp; {p}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔥 Reset Workflow Memory", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state["workflow_logs"] = []
        st.session_state["followup_messages"] = []
        st.session_state["current_phase"] = "Waiting"
        st.session_state["selected_template"] = ""
        st.session_state["agent_statuses"] = {k: "Idle" for k in st.session_state["agent_statuses"]}
        st.success("Workflow memory reset successfully!")
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    if groq_api_key and groq_api_key.startswith("gsk_"):
        st.success("LLM Connection Configured")
    else:
        st.warning("LLM Connection Not Configured")

# ----------------- HERO BANNER -----------------
st.html("""
<div class="hero-header">
    <h1>Multi-Agent Problem Solving System</h1>
    <p>Enterprise Collaborative Workflow with Supervisor, Research, Analysis, Execution & Live Metrics (LangGraph + Groq)</p>
</div>
""")

# ----------------- QUICK TASK TEMPLATES -----------------
st.html('<div class="section-title">⚡ Quick Task Templates</div>')
t_col1, t_col2, t_col3, t_col4 = st.columns(4)
with t_col1:
    if st.button("🏗️ Architecture"):
        st.session_state["selected_template"] = "Design a scalable microservices architecture for a high-traffic fintech application."
        st.rerun()
with t_col2:
    if st.button("📊 Business Analysis"):
        st.session_state["selected_template"] = "Perform a cost-benefit analysis of migrating an on-premise database cluster to AWS cloud."
        st.rerun()
with t_col3:
    if st.button("🔍 Research Data"):
        st.session_state["selected_template"] = "Compare three leading vector databases (Chroma, Pinecone, Milvus) for enterprise RAG systems."
        st.rerun()
with t_col4:
    if st.button("🧩 Problem Solver"):
        st.session_state["selected_template"] = "Develop a robust mitigation strategy for handling sudden API rate-limiting spikes in multi-agent pipelines."
        st.rerun()

# ----------------- MAIN INPUT SECTION -----------------
st.html('<div class="section-title">💡 Enter Problem or Complex Task</div>')

user_problem = st.text_area(
    "Describe the challenge or project requirement:",
    value=st.session_state["selected_template"],
    placeholder="e.g., Design a scalable cloud architecture for a university student portal with high traffic.",
    label_visibility="collapsed"
)

run_clicked = st.button("🚀 Run Multi-Agent Collaborative Workflow")

# ----------------- LANGGRAPH STATE DEFINITION -----------------
class AgentState(TypedDict):
    problem: str
    research_output: str
    analysis_output: str
    final_output: str
    current_agent: str

def get_llm():
    return ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=temperature_val)

def supervisor_node(state: AgentState):
    st.session_state["current_phase"] = "Planning"
    state["current_agent"] = "Supervisor Agent"
    return state

def research_node(state: AgentState):
    st.session_state["current_phase"] = "Researching"
    llm = get_llm()
    prompt = (
        "You are the Research Agent in a multi-agent system. Provide a comprehensive, detailed, factual research breakdown "
        "and background information for the following problem. Do NOT ask clarifying questions—provide full research details immediately.\n\n"
        f"PROBLEM STATEMENT:\n{state['problem']}"
    )
    res = llm.invoke(prompt)
    state["research_output"] = str(res.content)
    state["current_agent"] = "Research Agent"
    return state

def analysis_node(state: AgentState):
    st.session_state["current_phase"] = "Analyzing"
    llm = get_llm()
    prompt = (
        "You are the Analysis Agent in a multi-agent system. Perform a deep, structured analysis (evaluating options, pros & cons, "
        "trade-offs, risks, and performance factors) based on the research findings below. Do NOT ask conversational questions—output your complete analysis immediately.\n\n"
        f"PROBLEM:\n{state['problem']}\n\n"
        f"RESEARCH FINDINGS:\n{state['research_output']}"
    )
    res = llm.invoke(prompt)
    state["analysis_output"] = str(res.content)
    state["current_agent"] = "Analysis Agent"
    return state

def execution_node(state: AgentState):
    st.session_state["current_phase"] = "Executing"
    llm = get_llm()
    prompt = (
        "You are the Execution Agent in a multi-agent system. Provide a definitive, step-by-step actionable solution, architecture recommendations, "
        "and execution plan based on the research and analysis provided below. Output the final structured recommendations directly.\n\n"
        f"RESEARCH:\n{state['research_output']}\n\n"
        f"ANALYSIS:\n{state['analysis_output']}"
    )
    res = llm.invoke(prompt)
    state["final_output"] = str(res.content)
    state["current_agent"] = "Execution Agent"
    st.session_state["current_phase"] = "Completed"
    return state

# ----------------- BUILD GRAPH -----------------
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", research_node)
workflow.add_node("analyzer", analysis_node)
workflow.add_node("executor", execution_node)

workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "researcher")
workflow.add_edge("researcher", "analyzer")
workflow.add_edge("analyzer", "executor")
workflow.add_edge("executor", END)

app_graph = workflow.compile()

# ----------------- EXECUTION LOGIC WITH LIVE STREAMING & METRICS -----------------
if run_clicked:
    if not groq_api_key or not groq_api_key.startswith("gsk_"):
        st.error("Please enter a valid Groq API key in the sidebar.")
    elif not user_problem.strip():
        st.warning("Please enter a valid problem or select a quick template.")
    else:
        with st.status("🚀 Running Multi-Agent Collaborative Pipeline...", expanded=True) as status_container:
            st.write("🧠 **Supervisor Agent**: Initializing and planning task breakdown...")
            initial_state = {
                "problem": user_problem,
                "research_output": "",
                "analysis_output": "",
                "final_output": "",
                "current_agent": "Initializing..."
            }
            
            start_time = time.time()
            
            try:
                st.write("🔍 **Research Agent**: Gathering facts and comprehensive background data...")
                state_res = supervisor_node(initial_state)
                state_res = research_node(state_res)
                
                st.write("📊 **Analysis Agent**: Evaluating and processing research insights...")
                state_res = analysis_node(state_res)
                
                st.write("⚡ **Execution Agent**: Synthesizing final recommendations & solutions...")
                final_state = execution_node(state_res)
                
                elapsed = round(time.time() - start_time, 2)
                total_chars = len(final_state["research_output"]) + len(final_state["analysis_output"]) + len(final_state["final_output"])
                approx_tokens = int(total_chars / 4)
                
                final_state["elapsed_time"] = elapsed
                final_state["approx_tokens"] = approx_tokens
                
                status_container.update(label=f"✅ Workflow completed successfully in {elapsed}s (~{approx_tokens} tokens)", state="complete", expanded=False)
                
                st.session_state["chat_history"].append(user_problem)
                st.session_state["workflow_logs"].append(final_state)
                st.session_state["followup_messages"] = []
            except Exception as exc:
                status_container.update(label=f"❌ Workflow Failed: Groq API Error", state="error", expanded=True)
                err_str = str(exc)
                if "403" in err_str or "PermissionDenied" in err_str:
                    st.error(
                        f"🔑 **Groq Key Permission Error (403)** for model `{selected_model}`:\n\n"
                        f"Your Groq API Key has organization model limits blocked.\n\n"
                        f"👉 **Quick Fix**:\n"
                        f"1. Generate a new free key at [console.groq.com/keys](https://console.groq.com/keys)\n"
                        f"2. Paste the new key starting with `gsk_` into the sidebar API Key input box!"
                    )
                else:
                    st.error(
                        f"⚠️ **Groq Error for model `{selected_model}`**:\n\n`{err_str}`\n\n"
                        f"👉 **Fix**: Select **`openai/gpt-oss-20b`** or **`openai/gpt-oss-120b`** from the Model Engine dropdown in the sidebar!"
                    )

# ----------------- DISPLAY LATEST RESULTS & COMPACT METRICS -----------------
if st.session_state["workflow_logs"]:
    latest_res = st.session_state["workflow_logs"][-1]
    
    st.html(f"""
        <div class="metrics-container">
            <div class="metric-pill">
                <div class="metric-pill-label">⏱️ Execution Latency</div>
                <div class="metric-pill-value">{latest_res.get('elapsed_time', 0)}s</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-label">🔤 Approx Tokens</div>
                <div class="metric-pill-value">~{latest_res.get('approx_tokens', 0)}</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-label">⚡ Active Model</div>
                <div class="metric-pill-value" style="font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis;">{selected_model}</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-label">🎯 Status</div>
                <div class="metric-pill-value" style="color: #10B981;">Completed</div>
            </div>
        </div>
    """)

    st.html('<div class="section-title">🔍 1. Research Agent Output</div>')
    with st.container():
        st.markdown(f'<div class="agent-card" style="border-left: 4px solid #0EA5E9;">', unsafe_allow_html=True)
        st.markdown(latest_res["research_output"])
        st.markdown('</div>', unsafe_allow_html=True)

    st.html('<div class="section-title">📊 2. Analysis Agent Output</div>')
    with st.container():
        st.markdown(f'<div class="agent-card" style="border-left: 4px solid #10B981;">', unsafe_allow_html=True)
        st.markdown(latest_res["analysis_output"])
        st.markdown('</div>', unsafe_allow_html=True)

    st.html('<div class="section-title">⚡ 3. Execution & Final Synthesis</div>')
    with st.container():
        st.markdown(f'<div class="agent-card" style="border-left: 4px solid #EC4899;">', unsafe_allow_html=True)
        st.markdown(latest_res["final_output"])
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- INTERACTIVE FOLLOW-UP CHAT WITH AGENTS -----------------
    st.markdown("---")
    st.html('<div class="section-title">💬 Interactive Follow-up with Agents</div>')
    st.info("Have a specific question about this solution? Ask the agents below!")

    for msg in st.session_state["followup_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask a follow-up question (e.g., 'Can you detail the database scaling part?')...")
    if user_query:
        st.session_state["followup_messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agents are discussing your follow-up query..."):
                llm = get_llm()
                context_prompt = f"""
                You are an expert multi-agent assistant. Here is the previous context:
                Problem: {latest_res['problem']}
                Final Output: {latest_res['final_output']}
                
                User Follow-up Question: {user_query}
                
                Provide a clear, detailed, and professional answer:
                """
                response = llm.invoke(context_prompt)
                st.markdown(response.content)
                st.session_state["followup_messages"].append({"role": "assistant", "content": response.content})

    # ----------------- EXPORT LOGS & REPORTS -----------------
    st.markdown("---")
    st.html('<div class="section-title">📜 Export & Execution Logs</div>')
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        log_json = json.dumps(st.session_state["workflow_logs"], indent=2)
        st.download_button("📥 Download Execution Logs (JSON)", data=log_json, file_name="multi_agent_logs.json", mime="application/json")
    
    with col_exp2:
        markdown_report = f"# Multi-Agent Problem Solving Report\n\n## Problem Statement\n{latest_res['problem']}\n\n## 1. Research Output\n{latest_res['research_output']}\n\n## 2. Analysis Output\n{latest_res['analysis_output']}\n\n## 3. Final Execution & Recommendations\n{latest_res['final_output']}"
        st.download_button("📄 Download Report (.md)", data=markdown_report, file_name="agent_report.md", mime="text/markdown")