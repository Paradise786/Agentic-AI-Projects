import os
import time
import datetime
import streamlit as st
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from tools import calculate_gpa, university_schedule_tool, web_search_tool

load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="TaskExec AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATE -----------------
if "user_prompt" not in st.session_state:
    st.session_state["user_prompt"] = ""
if "tasks_completed" not in st.session_state:
    st.session_state["tasks_completed"] = 0
if "tools_used_count" not in st.session_state:
    st.session_state["tools_used_count"] = 0
if "last_run_time" not in st.session_state:
    st.session_state["last_run_time"] = "—"

# ----------------- CUSTOM CSS WITH FLOATING ANIMATION -----------------
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #F4F7F5 !important;
        color: #2D3748 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        overflow-x: hidden;
    }

    /* Modern Styled Sidebar Container */
    section[data-testid="stSidebar"] {
        background-color: #EEF2EF !important;
        border-right: 1px solid #E2E8F0;
        padding-top: 15px;
    }

    /* Sidebar Section Card Box */
    .sidebar-card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0B6640;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Active Tool Badges */
    .tool-chip {
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #C8E6C9;
        transition: all 0.2s ease;
    }
    .tool-chip:hover {
        background-color: #C8E6C9;
        transform: translateX(2px);
    }

    /* Top Header Box */
    .header-box {
        background-color: #0B6640;
        border-radius: 16px;
        padding: 22px 28px;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(11, 102, 64, 0.15);
        margin-bottom: 20px;
        position: relative;
        z-index: 2;
    }
    .header-box h2 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .header-box p {
        color: #D1FAE5 !important;
        margin: 6px 0 0 0;
        font-size: 0.9rem;
    }

    /* Floating Academic/AI Icons Keyframes */
    @keyframes floatUp {
        0% {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        20% {
            opacity: 0.4;
        }
        80% {
            opacity: 0.4;
        }
        100% {
            transform: translateY(-10vh) rotate(360deg);
            opacity: 0;
        }
    }

    /* Floating Icon Container Styles */
    .floating-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }

    .floating-item {
        position: absolute;
        bottom: -50px;
        font-size: 1.8rem;
        animation: floatUp 12s infinite linear;
        opacity: 0;
    }

    /* Staggered Floating Elements */
    .f1 { left: 15%; animation-delay: 0s; animation-duration: 14s; }
    .f2 { left: 35%; animation-delay: 3s; animation-duration: 11s; }
    .f3 { left: 55%; animation-delay: 6s; animation-duration: 15s; }
    .f4 { left: 75%; animation-delay: 1.5s; animation-duration: 13s; }
    .f5 { left: 90%; animation-delay: 4.5s; animation-duration: 12s; }

    /* Primary Action Button Styling */
    .stButton>button {
        background-color: #0B6640 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
    }
    .stButton>button:hover {
        background-color: #085032 !important;
        transform: translateY(-1px);
    }

    /* Custom Metric Styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #0B6640 !important;
    }

    /* Ready Status Box */
    .ready-box {
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        border-radius: 12px;
        padding: 16px 20px;
        color: #1B5E20;
        font-size: 0.9rem;
    }
</style>

<!-- Floating Background Elements -->
<div class="floating-bg">
    <div class="floating-item f1">🤖</div>
    <div class="floating-item f2">🎓</div>
    <div class="floating-item f3">📚</div>
    <div class="floating-item f4">⚡</div>
    <div class="floating-item f5">💻</div>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR SYSTEM CONFIG -----------------
with st.sidebar:
    st.markdown('<div class="sidebar-card-title">⚙️ System Config</div>', unsafe_allow_html=True)
    groq_api_key = st.text_input("Groq API key", type="password", value=os.getenv("GROQ_API_KEY", ""), help="Enter your Groq API key")
    selected_model = st.selectbox("LLM model", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"])
    
    st.markdown("---")
    st.markdown('<div class="sidebar-card-title">🛠️ Active Tools</div>', unsafe_allow_html=True)
    with st.expander("🧮 GPA calculator"):
        st.write("**Purpose:** Computes SGPA / CGPA")
        st.write("**Input:** `grade:credit` pairs (e.g. A:3, B:4)")
        st.write("**Status:** 🟢 Ready")

    with st.expander("📅 Academic schedule"):
        st.write("**Purpose:** Fetches exams & deadlines")
        st.write("**Queries:** midterms, finals, holidays")
        st.write("**Status:** 🟢 Ready")

    with st.expander("🌐 Web search tool"):
        st.write("**Purpose:** Live web research via DuckDuckGo")
        st.write("**Status:** 🟢 Ready")
    
    st.markdown("---")
    st.markdown('<div class="sidebar-card-title">📊 Agent Status</div>', unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns(2)
    col_s1.metric("Tasks Done", st.session_state['tasks_completed'])
    col_s2.metric("Tools Used", st.session_state['tools_used_count'])
    
    st.caption(f"⏱️ **Last Run:** {st.session_state['last_run_time']}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state["user_prompt"] = ""
        st.session_state["tasks_completed"] = 0
        st.session_state["tools_used_count"] = 0
        st.session_state["last_run_time"] = "—"
        st.rerun()

if not groq_api_key:
    st.info("💡 **Getting Started:** Please enter your Groq API key in the sidebar to activate the agent.")
    st.stop()

# ----------------- TOP BANNER -----------------
st.markdown("""
<div class="header-box">
    <h2>🤖 TaskExec AI assistant</h2>
    <p>Autonomous academic task execution agent</p>
</div>
""", unsafe_allow_html=True)

# ----------------- QUICK PRESET HANDLERS -----------------
st.markdown("### 💡 Quick suggested requests")
col1, col2 = st.columns(2)

def set_preset_1():
    st.session_state["user_prompt"] = "Calculate my GPA for grades A in 3 credits, B in 4 credits, A in 3 credits, C in 2 credits and check when midterm exams start."

def set_preset_2():
    st.session_state["user_prompt"] = "When do final exams start and what is the registration deadline?"

col1.button("🎓 GPA and midterm query", use_container_width=True, on_click=set_preset_1)
col2.button("📅 Exam and deadline query", use_container_width=True, on_click=set_preset_2)

# ----------------- INPUT SECTION -----------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### ✍️ Enter your goal or request")

user_input = st.text_area(
    "Goal Input",
    key="user_prompt",
    placeholder="e.g. calculate my GPA for grades A2 B4 A1 C2...",
    height=100,
    label_visibility="collapsed"
)

execute_clicked = st.button("▶ Execute autonomous goal", use_container_width=True, type="primary")

# ----------------- LLM & TOOLS SETUP -----------------
llm = ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=0.1)
tools = [calculate_gpa, university_schedule_tool, web_search_tool]
tools_dict = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

# ----------------- AGENT MONITOR & OUTPUT -----------------
st.markdown("---")
st.markdown("### 🔍 Agent execution monitor and output")

if execute_clicked:
    if not user_input.strip():
        st.warning("Please enter a goal or select a quick suggested request.")
    else:
        start_time = time.time()
        status_box = st.status("⚙️ Executing Autonomous Goal...", expanded=True)
        
        system_msg = SystemMessage(
            content=(
                "You are an autonomous academic assistant agent. "
                "Break down the user request into logical steps. "
                "Use available tools if needed to gather accurate information. "
                "Provide a complete, direct, and well-formatted response with markdown sections, bold headings, and bullet points."
            )
        )
        
        messages = [system_msg, HumanMessage(content=user_input)]
        status_box.write("✔ Goal received")
        status_box.write("✔ Goal analyzed")
        
        step_count = 0
        tools_called_set = set()
        final_answer = ""
        max_iterations = 5
        
        try:
            for iteration in range(max_iterations):
                step_count += 1
                response = llm_with_tools.invoke(messages)
                messages.append(response)
                
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        t_name = tool_call["name"]
                        t_args = tool_call["args"]
                        tools_called_set.add(t_name)
                        
                        status_box.write(f"→ Executing Tool: `{t_name}`")
                        
                        if t_name in tools_dict:
                            tool_result = tools_dict[t_name].invoke(t_args)
                            messages.append(
                                ToolMessage(
                                    content=str(tool_result),
                                    tool_call_id=tool_call["id"]
                                )
                            )
                            status_box.write(f"✔ Tool `{t_name}` execution completed")
                        else:
                            messages.append(
                                ToolMessage(
                                    content=f"Error: Tool '{t_name}' is not registered.",
                                    tool_call_id=tool_call["id"]
                                )
                            )
                else:
                    final_answer = response.content
                    status_box.write("✔ Final answer generated")
                    break
            else:
                status_box.write("⚡ Synthesizing final response...")
                final_response = llm.invoke(messages)
                final_answer = final_response.content
                
            elapsed_time = round(time.time() - start_time, 2)
            status_box.update(label="✔ Execution Completed Successfully", state="complete", expanded=False)
            
            # Celebration effect on completion
            st.balloons()
            
            # Update Metrics
            st.session_state["tasks_completed"] += 1
            st.session_state["tools_used_count"] += len(tools_called_set)
            st.session_state["last_run_time"] = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Display Result Output
            st.markdown("### 📋 Agent Response Output")
            st.markdown(final_answer)
            st.markdown("---")
            
            # Metrics Summary Row
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Execution Time", f"{elapsed_time}s")
            m_col2.metric("Tools Used", len(tools_called_set))
            m_col3.metric("Steps Taken", step_count)
            
        except Exception as e:
            status_box.update(label="❌ Execution Error", state="error")
            st.error(f"An error occurred: {str(e)}")
else:
    st.markdown("""
    <div class="ready-box">
        ✔ <b>System ready.</b> Enter a goal above and press execute to begin autonomous task analysis.
    </div>
    """, unsafe_allow_html=True)