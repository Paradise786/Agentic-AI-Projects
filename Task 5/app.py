import os
import time
import json
import re
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Intelligent Communication Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATES -----------------
if "comm_history" not in st.session_state:
    st.session_state["comm_history"] = []
if "input_query" not in st.session_state:
    st.session_state["input_query"] = ""
if "latest_decision" not in st.session_state:
    st.session_state["latest_decision"] = {
        "intent": "Awaiting execution...",
        "priority": "Normal",
        "audience": "General",
        "channel": "None",
        "reason": "Awaiting prompt analysis."
    }
if "latest_logs" not in st.session_state:
    st.session_state["latest_logs"] = ["✓ System initialized", "✓ Awaiting user instruction..."]
if "latest_preview" not in st.session_state:
    st.session_state["latest_preview"] = {
        "email_subject": "N/A",
        "email_to": "N/A",
        "email_body": "No email generated yet.",
        "notif_title": "N/A",
        "notif_msg": "No notification generated yet."
    }
if "tool_statuses" not in st.session_state:
    st.session_state["tool_statuses"] = {
        "Message Generator": "Idle",
        "Email Tool": "Idle",
        "Push Notification": "Idle",
        "Validation Engine": "Idle"
    }
if "validation_results" not in st.session_state:
    st.session_state["validation_results"] = []
if "clear_confirm" not in st.session_state:
    st.session_state["clear_confirm"] = False

# ----------------- DYNAMIC METRICS FROM HISTORY -----------------
def get_metrics_from_history():
    history = st.session_state.get("comm_history", [])
    total = len(history)
    emails = 0
    notifications = 0
    alerts = 0
    for h in history:
        channel = h.get("Channel", "")
        priority = h.get("Priority", "")
        if "Email" in channel:
            emails += 1
        if "Push" in channel:
            notifications += 1
        if "High" in priority or "Urgent" in priority or "🔴" in priority or "🟠" in priority:
            alerts += 1
    return {"total": total, "emails": emails, "notifications": notifications, "alerts": alerts}

# ----------------- HIGH-LEVEL ADVANCED PASTEL SAGE THEME -----------------
st.html("""
<style>
    /* ---- Global Page ---- */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAF9FC !important;
        color: #1E1B4B !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }
    
    /* Hide default Streamlit header bar completely to prevent cutting off at top */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* ---- Collapse Streamlit default gaps globally ---- */
    .block-container {
        padding-top: 2rem !important; /* Safe padding now that header is hidden */
        padding-bottom: 2rem !important;
    }
    [data-testid="stVerticalBlock"] > div {
        gap: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 12px !important;
        align-items: stretch !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    /* Kill extra padding Streamlit injects around st.html blocks */
    [data-testid="stHtml"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Collapse space between info banner and KPI row */
    [data-testid="stAlert"] {
        margin-bottom: 10px !important;
        margin-top: 0 !important;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: #ECEAF2 !important; /* Soft lavender-gray sidebar */
        color: #1E1B4B !important;
        border-right: 1px solid #DFDBE5 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: #1E1B4B !important;
    }
    section[data-testid="stSidebar"] .stExpander {
        background-color: #F5F3FF !important; /* Light lavender box */
        border: 1px solid #DDD6FE !important;
        border-radius: 12px !important;
    }

    /* ---- Cards: fixed height-match, zero stray margin ---- */
    .custom-card {
        background: #FFFFFF;
        border: 1px solid #EAE6F0;
        border-radius: 14px;
        padding: 18px 20px;
        margin: 0;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.04);
        height: 100%;
        box-sizing: border-box;
    }
    .custom-card h4 {
        color: #1E1B4B;
        font-weight: 700;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 12px;
        border-bottom: 1px solid #F3F1F7;
        padding-bottom: 8px;
    }

    /* ---- Hero Header with Cyan, Pink and Indigo Gradient ---- */
    .hero-header {
        background: linear-gradient(135deg, #818CF8 0%, #EC4899 50%, #38BDF8 100%);
        border: 1px solid #A5B4FC;
        border-radius: 16px;
        padding: 22px 28px;
        color: #FFFFFF;
        margin-bottom: 12px;
        box-shadow: 0 10px 25px rgba(236, 72, 153, 0.15);
    }
    .hero-header h1 {
        color: #FFFFFF;
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    }
    .hero-header p {
        color: #FDF2F8;
        margin: 6px 0 12px 0;
        font-size: 0.93rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    .badge-container { display: flex; gap: 8px; flex-wrap: wrap; }
    .header-badge {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: 0.04em;
    }

    /* ---- KPI Grid: uniform height ---- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 0 0 8px 0;
    }
    @media (max-width: 768px) {
        .kpi-container { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #EAE6F0;
        border-radius: 14px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.04);
    }
    .kpi-card-1 { border-top: 3px solid #38BDF8; } /* Cyan */
    .kpi-card-2 { border-top: 3px solid #F472B6; } /* Pink */
    .kpi-card-3 { border-top: 3px solid #818CF8; } /* Indigo */
    .kpi-card-4 { border-top: 3px solid #EC4899; } /* Magenta */
    .kpi-title {
        font-size: 0.7rem;
        color: #6B6885;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.7rem;
        color: #1E1B4B;
        font-weight: 800;
    }

    /* ---- Section Titles ---- */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E1B4B;
        margin: 14px 0 8px 0;
        display: flex;
        align-items: center;
        gap: 7px;
    }

    /* ---- Tools status ---- */
    .tool-registry-item {
        background: #F5F3FF;
        border: 1px solid #DDD6FE;
        border-radius: 12px;
        padding: 9px 12px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .tool-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #1E1B4B;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .tool-desc {
        font-size: 0.7rem;
        color: #6B6885;
        margin-top: 1px;
    }

    /* ---- Badges ---- */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-align: center;
    }
    .badge-urgent { background-color: #FCE7F3; color: #9D174D; border: 1px solid #FBCFE8; }
    .badge-high { background-color: #F5F3FF; color: #5B21B6; border: 1px solid #DDD6FE; }
    .badge-normal { background-color: #E0F2FE; color: #075985; border: 1px solid #BAE6FD; }
    .badge-low { background-color: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }

    /* ---- Stepper ---- */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 8px 0;
        padding: 14px 16px;
        background: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #EAE6F0;
        overflow-x: auto;
    }
    .step-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        text-align: center;
        min-width: 80px;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #F3F1F7;
        color: #6B6885;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 6px;
        border: 2px solid #EAE6F0;
        transition: all 0.3s ease;
    }
    .step-node.completed .step-circle {
        background: linear-gradient(135deg, #818CF8 0%, #38BDF8 100%);
        color: #FFFFFF;
        border-color: #818CF8;
    }
    .step-node.active .step-circle {
        background: linear-gradient(135deg, #EC4899 0%, #F472B6 100%);
        color: #FFFFFF;
        border-color: #EC4899;
        box-shadow: 0 0 10px rgba(236, 72, 153, 0.4);
    }
    .step-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #6B6885;
    }
    .step-node.completed .step-label {
        color: #818CF8;
    }
    .step-node.active .step-label {
        color: #EC4899;
    }
    .step-connector {
        flex: 1;
        height: 2px;
        background-color: #EAE6F0;
        margin: 0 8px;
        margin-bottom: 20px;
    }
    .step-connector.completed {
        background: linear-gradient(90deg, #818CF8 0%, #38BDF8 100%);
    }

    /* ---- Buttons ---- */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Make templates look clean */
    div.stButton > button:first-child {
        background-color: #FFFFFF !important;
        border: 1px solid #EAE6F0 !important;
        color: #1E1B4B !important;
    }
    div.stButton > button:hover {
        border-color: #818CF8 !important;
        background-color: #F5F3FF !important;
        color: #4F46E5 !important;
    }
</style>
""")

# ----------------- TOOLS DEFINITION -----------------
@tool
def send_email_tool(recipient: str, subject: str, body: str) -> str:
    """Send an email notification to the target recipient."""
    return f"Email successfully dispatched to {recipient} with subject '{subject}'."

@tool
def send_push_notification(target_user: str, message: str) -> str:
    """Send a push notification to target user or group."""
    return f"Push notification transmitted to {target_user}."

tools = [send_email_tool, send_push_notification]

# ----------------- SIDEBAR SETUP -----------------
with st.sidebar:
    st.markdown("### 🤖 AGENT SYSTEM HUB")
    st.markdown("---")
    
    # Compact API Credentials in expander
    with st.expander("🔑 LLM Credentials", expanded=False):
        env_key = os.getenv("GROQ_API_KEY", "")
        groq_api_key = st.text_input("Groq API Key", type="password", value=env_key, placeholder="gsk_...")
        if groq_api_key and groq_api_key.startswith("gsk_"):
            st.markdown("<span style='color: #0D9488; font-weight: 700; font-size:0.8rem;'>● Groq API Connected</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #E11D48; font-weight: 700; font-size:0.8rem;'>● Local Simulator Active</span>", unsafe_allow_html=True)

    st.markdown("#### ⚙️ Control Panel")
    selected_model = st.selectbox("LLM Model", ["llama-3.1-8b-instant", "llama3-70b-8192"])
    comm_mode = st.selectbox("Execution Mode", ["🟢 Simulation Mode (Demo)", "🔵 Live External API"])

    st.markdown("---")
    st.markdown("#### 🛠️ Active Tools Registry")
    tool_status_msg = st.session_state["tool_statuses"]
    
    for tool_name, desc, icon in [
        ("Message Generator", "Formulates context-aware copy", "📝"),
        ("Email Tool", "Dispatches structured emails", "📧"),
        ("Push Notification", "Sends device notifications", "🔔"),
        ("Validation Engine", "Validates output criteria", "✅")
    ]:
        status_val = tool_status_msg.get(tool_name, "Idle")
        badge_color = "#E5EFEA"
        text_color = "#4B6E60"
        if "Completed" in status_val:
            badge_color = "#CCFBF1"
            text_color = "#0F766E"
        elif "Running" in status_val:
            badge_color = "#E0E7FF"
            text_color = "#4338CA"
        elif "Pending" in status_val:
            badge_color = "#FEF3C7"
            text_color = "#92400E"
        elif "Skipped" in status_val:
            badge_color = "#F1F5F9"
            text_color = "#64748B"
            
        st.html(f"""
            <div class="tool-registry-item">
                <div>
                    <div class="tool-name">{icon} {tool_name}</div>
                    <div class="tool-desc">{desc}</div>
                </div>
                <div style="font-size: 0.68rem; font-weight: 700; padding: 3px 8px; border-radius: 12px; background: {badge_color}; color: {text_color};">
                    {status_val}
                </div>
            </div>
        """)

    st.markdown("---")
    st.markdown("System Status: **Online 🟢**")

    st.markdown("---")
    if not st.session_state["clear_confirm"]:
        if st.button("🗑️ Clear Dashboard History", use_container_width=True):
            st.session_state["clear_confirm"] = True
            st.rerun()
    else:
        st.warning("Confirm clearing all history & stats?")
        col_y, col_n = st.columns(2)
        if col_y.button("Yes"):
            st.session_state["comm_history"] = []
            st.session_state["latest_decision"] = {
                "intent": "Awaiting execution...",
                "priority": "Normal",
                "audience": "General",
                "channel": "None",
                "reason": "Awaiting prompt analysis."
            }
            st.session_state["latest_logs"] = ["✓ System initialized", "✓ Awaiting user instruction..."]
            st.session_state["latest_preview"] = {
                "email_subject": "N/A",
                "email_to": "N/A",
                "email_body": "No email generated yet.",
                "notif_title": "N/A",
                "notif_msg": "No notification generated yet."
            }
            st.session_state["tool_statuses"] = {
                "Message Generator": "Idle",
                "Email Tool": "Idle",
                "Push Notification": "Idle",
                "Validation Engine": "Idle"
            }
            st.session_state["validation_results"] = []
            st.session_state["clear_confirm"] = False
            st.success("Cleared!")
            st.rerun()
        if col_n.button("No"):
            st.session_state["clear_confirm"] = False
            st.rerun()

# ----------------- HEADER -----------------
st.html("""
<div class="hero-header">
    <h1>🤖 Intelligent Communication Assistant</h1>
    <p><b>Autonomous AI Agent for context-aware notifications, routing analysis, and validation controls.</b></p>
    <div class="badge-container">
        <div class="header-badge">AGENTIC WORKFLOW</div>
        <div class="header-badge">STRUCTURED DECISION GATE</div>
        <div class="header-badge">QA VALIDATION</div>
    </div>
</div>
""")

# Simulation Mode Honest Notice
if "Simulation" in comm_mode:
    st.info("ℹ️ **SIMULATION MODE ACTIVE:** Communication flows are generated and executed locally. No live emails are dispatched.")

# ----------------- STATISTICS CARDS -----------------
metrics = get_metrics_from_history()
st.html(f"""
<div class="kpi-container">
    <div class="kpi-card kpi-card-1">
        <div class="kpi-title">Total Communications</div>
        <div class="kpi-value">{metrics['total']:02d}</div>
    </div>
    <div class="kpi-card kpi-card-2">
        <div class="kpi-title">Emails Generated</div>
        <div class="kpi-value">{metrics['emails']:02d}</div>
    </div>
    <div class="kpi-card kpi-card-3">
        <div class="kpi-title">Notifications Sent</div>
        <div class="kpi-value">{metrics['notifications']:02d}</div>
    </div>
    <div class="kpi-card kpi-card-4">
        <div class="kpi-title">Alert Escalations</div>
        <div class="kpi-value" style="color: #F43F5E;">{metrics['alerts']:02d}</div>
    </div>
</div>
""")

# ----------------- QUICK COMMUNICATION TEMPLATES -----------------
st.markdown('<div class="section-title">⚡ Quick Communication Scenarios</div>', unsafe_allow_html=True)
t_col_row1 = st.columns(4)
t_col_row2 = st.columns(4)

templates = [
    ("📝 Exam Announcement", "Send a announcement to students about the rescheduled Midterm Exam of CS-301 to August 24th at 10:00 AM in Room 402.", t_col_row1[0]),
    ("⏰ Deadline Reminder", "Send a deadline reminder to the Project Teams that the Milestone 3 deliverables submission closes tomorrow at 11:59 PM. Make sure to upload the PDF.", t_col_row1[1]),
    ("👥 Meeting Notice", "Draft a meeting notice for the Faculty Members regarding the syllabus review discussion on Friday at 2:00 PM in the Main Boardroom.", t_col_row1[2]),
    ("🚨 Emergency Alert", "🚨 CRITICAL: Send an urgent warning to all Campus Students & Staff that campus will remain closed tomorrow due to heavy rain and urban flooding warnings.", t_col_row1[3]),
    ("🛠️ Maintenance Alert", "Notify System Administrators that the student enrollment portal will go offline for database maintenance on Saturday from 2:00 AM to 6:00 AM.", t_col_row2[0]),
    ("📁 Project Submission", "Please send a submission notification to Senior Project Groups to upload their final year project source code and demonstration video links by next Monday at 5:00 PM.", t_col_row2[1]),
    ("🏛️ Admin Notice", "Send an administrative notice to All Students regarding course enrollment registration for the Fall semester, reminding them to clear outstanding dues before Friday.", t_col_row2[2]),
    ("📢 General Announcement", "Send a general announcement to Faculty and Students inviting them to a guest lecture on 'Future of Agentic AI' by Dr. Asim this Wednesday at 11:00 AM in the Main Auditorium.", t_col_row2[3])
]

for label, text, col in templates:
    if col.button(label, use_container_width=True):
        st.session_state["input_query"] = text
        st.rerun()

# ----------------- COMMUNICATION REQUEST FORM -----------------
st.markdown('<div class="section-title">💬 Communication Request Input</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 0.85rem; color: #3B5E50; margin-bottom: 8px;'><b>Describe what message the agent should analyze, structure, and dispatch:</b></p>", unsafe_allow_html=True)

user_request = st.text_area(
    "Request Description",
    value=st.session_state["input_query"],
    height=90,
    placeholder="e.g., Send a high-priority announcement to students about the rescheduled Midterm Exam of CS-301 to August 24th at 10:00 AM in Room 402.",
    label_visibility="collapsed"
)

st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
col_run, col_clear = st.columns([4, 1], gap="small")

with col_clear:
    if st.button("🗑️ Clear Input", use_container_width=True):
        st.session_state["input_query"] = ""
        st.rerun()

# ----------------- LOCAL SIMULATION ENGINE (HEURISTIC) -----------------
def simulate_agent_decision(query: str) -> dict:
    query_lower = query.lower()
    
    # 1. Determine Intent
    intent = "General Announcement"
    if any(x in query_lower for x in ["exam", "paper", "midterm", "final", "test", "quiz"]):
        intent = "Exam Announcement"
    elif any(x in query_lower for x in ["deadline", "due date", "until"]):
        intent = "Deadline Reminder"
    elif any(x in query_lower for x in ["meeting", "sync", "discussion", "catchup", "discuss"]):
        intent = "Meeting"
    elif any(x in query_lower for x in ["urgent", "emergency", "outage", "fire", "critical", "incident", "flooding", "weather", "closed"]):
        intent = "Emergency"
    elif any(x in query_lower for x in ["maintenance", "downtime", "offline", "server", "repair", "cleanup"]):
        intent = "Maintenance"
    elif any(x in query_lower for x in ["submission", "submit", "upload", "deliverable"]):
        intent = "Project Submission"
    elif any(x in query_lower for x in ["admin", "office", "registrar", "fee", "dues", "enrollment", "registration"]):
        intent = "Administrative Notice"
    
    # 2. Determine Priority
    priority = "Normal"
    if any(x in query_lower for x in ["critical", "outage", "fire", "disaster", "emergency", "flooding", "closed"]):
        priority = "Urgent"
    elif any(x in query_lower for x in ["urgent", "immediately", "asap", "exam", "maintenance"]):
        priority = "High"
    elif any(x in query_lower for x in ["low", "newsletter", "gala", "sports"]):
        priority = "Low"
        
    # 3. Determine Audience
    audience = "General Users"
    if "student" in query_lower:
        audience = "Students"
    elif "admin" in query_lower or "registrar" in query_lower or "desk" in query_lower:
        audience = "Administrators"
    elif "faculty" in query_lower or "teacher" in query_lower or "professor" in query_lower:
        audience = "Faculty"
    elif "team" in query_lower or "group" in query_lower or "member" in query_lower:
        audience = "Project Teams"
    elif "staff" in query_lower:
        audience = "Staff Members"
        
    # 4. Determine Channels
    channels = ["Email"]
    if priority in ["High", "Urgent"] or intent in ["Exam Announcement", "Emergency", "Maintenance", "Project Submission"]:
        channels = ["Email", "Push Notification"]
    elif "push" in query_lower or "notification" in query_lower:
        channels = ["Push Notification"]
        
    # 5. Extract dates, times, venues or details to insert
    date_match = re.search(r'(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2})', query_lower)
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)|\d{1,2}\s*(?:am|pm|AM|PM))', query_lower)
    
    date_str = date_match.group(1).title() if date_match else "Upcoming Date"
    time_str = time_match.group(1).upper() if time_match else "Scheduled Time"
    
    # 6. Generate Reasoning
    reasoning = f"The query contains elements of a {intent.lower()} directed at {audience.lower()}. Routing priority was escalated to {priority} due to context urgency, selecting channels: {', '.join(channels)}."
    
    # 7. Generate content based on intent
    email_subject = f"Official Notice: {intent}"
    email_to = f"{audience.lower().replace(' ', '')}@university.edu.pk"
    
    # Custom message bodies based on intent
    if intent == "Exam Announcement":
        email_subject = f"Official Schedule: Midterm & Final Exams - {date_str}"
        email_body = f"Dear {audience},\n\nThis is to officially announce the exam schedule details as requested. The examinations are scheduled to take place on {date_str} at {time_str}.\n\nContext details: {query}\n\nPlease check your student portal to verify examination hall seat planning. Keep your registration slips and student cards with you.\n\nBest regards,\nOffice of Controller of Examinations"
        push_title = "Exam Schedule Released"
        push_body = f"Exams scheduled on {date_str} at {time_str}. Please verify seat plan in your student portal."
    elif intent == "Deadline Reminder":
        email_subject = f"Urgent Reminder: Submission Deadline on {date_str}"
        email_body = f"Dear {audience},\n\nWe would like to remind you that the submission deadline for your task is set for {date_str} at {time_str}.\n\nRequest Context: {query}\n\nPlease submit all deliverables before the portal closes. Late submissions will face grading deductions.\n\nBest regards,\nAcademic Operations Team"
        push_title = "Submission Deadline Alert"
        push_body = f"Submission portal closes on {date_str} at {time_str}. Ensure all files are uploaded on time."
    elif intent == "Meeting":
        email_subject = f"Meeting Notice: Discussion on {date_str}"
        email_body = f"Dear {audience},\n\nYou are requested to attend a sync meeting scheduled on {date_str} at {time_str}.\n\nAgenda Context: {query}\n\nPlease join promptly using the MS Teams meeting link or at the designated venue.\n\nRegards,\nManagement Office"
        push_title = "Upcoming Meeting Scheduled"
        push_body = f"Meeting scheduled on {date_str} at {time_str}. Check your email calendar for the details."
    elif intent == "Emergency":
        email_subject = f"EMERGENCY ALERT: Important Security Notice"
        email_body = f"Dear {audience},\n\nThis is an urgent emergency alert. Please be aware of the following situation: {query}.\n\nAction requested: Please comply with safety instructions immediately and monitor official channels for updates.\n\nStay safe,\nEmergency Response Committee"
        push_title = "🚨 EMERGENCY ALERT"
        push_body = f"Emergency Alert: {query[:80]}... Stay tuned for updates."
    elif intent == "Maintenance":
        email_subject = f"Infrastructure Notice: Scheduled Downtime on {date_str}"
        email_body = f"Dear {audience},\n\nPlease be advised that server systems will undergo maintenance on {date_str} starting at {time_str}.\n\nScope of Work: {query}\n\nDuring this time, online services might be temporarily unavailable. We apologize for any inconvenience.\n\nBest regards,\nIT Infrastructure Desk"
        push_title = "🛠 Server Maintenance Alert"
        push_body = f"Scheduled maintenance on {date_str} ({time_str}). Services will be offline."
    elif intent == "Project Submission":
        email_subject = f"Final Project Submission Portal Open"
        email_body = f"Dear {audience},\n\nThis is to notify you that the final project submission portal is now open. The deadline is {date_str} at {time_str}.\n\nDetails: {query}\n\nMake sure to upload your GitHub repositories, documentation files, and demo links. No submissions will be accepted after the cutoff.\n\nRegards,\nEvaluation Panel"
        push_title = "Project Submission Active"
        push_body = f"Final project submission portal is open. Deadline is {date_str} at {time_str}."
    elif intent == "Administrative Notice":
        email_subject = f"Administrative Notification - Action Required"
        email_body = f"Dear {audience},\n\nPlease find the administrative update below:\n\nDetails: {query}\n\nEnsure compliance by the deadline to prevent service disruption or hold on portals.\n\nBest regards,\nRegistrar Office Desk"
        push_title = "Administrative Alert"
        push_body = f"Important administrative update: {query[:80]}."
    else: # General Announcement
        email_subject = f"General Announcement: Important Updates"
        email_body = f"Dear {audience},\n\nPlease read the following general announcement:\n\n{query}\n\nWe encourage everyone to stay informed and attend the relevant sessions where applicable.\n\nBest regards,\nAdministrative Officer"
        push_title = "New General Announcement"
        push_body = f"Announcement: {query[:80]}."

    return {
        "intent": intent,
        "priority": priority,
        "audience": audience,
        "channels": channels,
        "reasoning": reasoning,
        "email": {
            "subject": email_subject,
            "to": email_to,
            "body": email_body
        },
        "push_notification": {
            "title": push_title,
            "recipient": audience.lower().replace(" ", "_"),
            "body": push_body
        }
    }

# ----------------- PARSE LLM response -----------------
def parse_llm_json(response_text: str) -> dict:
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    cleaned = cleaned.strip()
    return json.loads(cleaned)

def sanitize_decision(decision_dict: dict) -> dict:
    sanitized = {}
    sanitized["intent"] = decision_dict.get("intent", "General Announcement").title()
    sanitized["priority"] = decision_dict.get("priority", "Normal").title()
    if sanitized["priority"] not in ["Low", "Normal", "High", "Urgent"]:
        sanitized["priority"] = "Normal"
        
    sanitized["audience"] = decision_dict.get("audience", "General Users")
    
    raw_channels = decision_dict.get("channels", decision_dict.get("channel", []))
    if isinstance(raw_channels, str):
        raw_channels = [raw_channels]
    sanitized["channels"] = []
    for c in raw_channels:
        if "email" in c.lower():
            sanitized["channels"].append("Email")
        if "push" in c.lower() or "notification" in c.lower():
            sanitized["channels"].append("Push Notification")
    if not sanitized["channels"]:
        sanitized["channels"] = ["Email"]
        
    sanitized["reasoning"] = decision_dict.get("reasoning", "Autonomous decision based on content.")
    
    email_raw = decision_dict.get("email", {})
    if not isinstance(email_raw, dict):
        email_raw = {}
    sanitized["email"] = {
        "subject": email_raw.get("subject", f"Notice: {sanitized['intent']}"),
        "to": email_raw.get("to", f"{sanitized['audience'].lower().replace(' ', '')}@university.edu.pk"),
        "body": email_raw.get("body", "No email body content generated.")
    }
    
    push_raw = decision_dict.get("push_notification", decision_dict.get("push", {}))
    if not isinstance(push_raw, dict):
        push_raw = {}
    sanitized["push_notification"] = {
        "title": push_raw.get("title", f"Notice: {sanitized['intent']}"),
        "recipient": push_raw.get("recipient", sanitized["audience"].lower().replace(' ', '_')),
        "body": push_raw.get("body", "No notification body content generated.")
    }
    
    return sanitized

# ----------------- QUALITY VALIDATION ENGINE -----------------
def run_validation_checks(intent, priority, audience, channels, email_data, push_data, query) -> list:
    results = []
    
    # 1. Recipient check
    if "Email" in channels:
        to_email = email_data.get("to", "")
        if not to_email:
            results.append({"check": "Recipient Email Present", "status": "Failed ❌", "details": "No recipient email address specified."})
        elif "@" not in to_email or "." not in to_email:
            results.append({"check": "Recipient Email Format", "status": "Warning ⚠️", "details": f"Email address '{to_email}' may be invalidly formatted."})
        else:
            results.append({"check": "Recipient Email Validated", "status": "Passed ✅", "details": f"Valid recipient target address: '{to_email}'."})
    if "Push Notification" in channels:
        push_recip = push_data.get("recipient", "")
        if not push_recip:
            results.append({"check": "Push Target Username Present", "status": "Failed ❌", "details": "No push notification recipient specified."})
        else:
            results.append({"check": "Push Target Validated", "status": "Passed ✅", "details": f"Push channel set to: '{push_recip}'."})

    # 2. Content check
    if "Email" in channels:
        body = email_data.get("body", "")
        subject = email_data.get("subject", "")
        if len(body) < 50:
            results.append({"check": "Email Body Depth", "status": "Warning ⚠️", "details": "Email body content is very short (under 50 characters)."})
        elif len(subject) < 5:
            results.append({"check": "Email Subject Clarity", "status": "Warning ⚠️", "details": "Subject line is extremely short."})
        else:
            results.append({"check": "Email Content Length", "status": "Passed ✅", "details": f"Email generated successfully ({len(body)} chars, subject: '{subject}')."})

    # 3. Priority check
    query_lower = query.lower()
    is_urgent_query = any(w in query_lower for w in ["critical", "outage", "fire", "emergency", "flooding", "closure", "closed"])
    if is_urgent_query and priority not in ["High", "Urgent"]:
        results.append({"check": "Priority Alignment", "status": "Failed ❌", "details": f"Query indicates high urgency, but agent routed with '{priority}' priority."})
    elif priority == "Urgent" and not is_urgent_query:
        results.append({"check": "Priority Alignment", "status": "Warning ⚠️", "details": "Priority set to 'Urgent' for a standard operational request."})
    else:
        results.append({"check": "Priority Alignment", "status": "Passed ✅", "details": f"Priority level '{priority}' is consistent with request context."})

    # 4. Channel Safety check
    if "Push Notification" in channels:
        notif_msg = push_data.get("body", "")
        if len(notif_msg) > 120:
            results.append({"check": "Push Message Length Limit", "status": "Warning ⚠️", "details": f"Push notifications should be brief. Length is {len(notif_msg)} chars (target is <120)."})
        else:
            results.append({"check": "Push Message Length Limit", "status": "Passed ✅", "details": f"Push notification length is optimized ({len(notif_msg)} chars)."})
            
    # 5. Required Information check (Dates / Times / Placeholders)
    body_text = email_data.get("body", "") + " " + push_data.get("body", "")
    if "[" in body_text or "]" in body_text or "insert" in body_text.lower():
        results.append({"check": "Placeholder Verification", "status": "Failed ❌", "details": "Unresolved variables or brackets (e.g. '[date]') detected in message."})
    else:
        results.append({"check": "Placeholder Verification", "status": "Passed ✅", "details": "No unresolved placeholder brackets detected in generated message."})
        
    if intent in ["Exam Announcement", "Meeting", "Deadline Reminder", "Maintenance"]:
        has_time = any(w in body_text.lower() for w in ["am", "pm", "o'clock", "time", "scheduled", "at"])
        has_date = any(w in body_text.lower() for w in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "tomorrow", "today", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "2025", "2026"])
        if not has_date or not has_time:
            results.append({"check": "Time-Sensitive Info Presence", "status": "Warning ⚠️", "details": f"Intent is '{intent}' but could not verify presence of both specific date and time details."})
        else:
            results.append({"check": "Time-Sensitive Info Presence", "status": "Passed ✅", "details": "Verified presence of scheduling date and time parameters in output."})
            
    return results

def get_validation_html(val_checks):
    if not val_checks:
        return "<p style='color: #64748B; font-size: 0.88rem; font-style: italic;'>Awaiting communication execution to run checks...</p>"
    
    html = '<div style="display: flex; flex-direction: column; gap: 8px;">'
    for c in val_checks:
        badge_style = ""
        if "Passed" in c["status"]:
            badge_style = "background-color: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0;"
        elif "Warning" in c["status"]:
            badge_style = "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE;"
        else: # Failed
            badge_style = "background-color: #FFF1F2; color: #9F1239; border: 1px solid #FECDD3;"
            
        html += f"""
        <div style="padding: 10px 14px; border-radius: 12px; font-size: 0.82rem; display: flex; flex-direction: column; gap: 2px; {badge_style}">
            <div style="display: flex; justify-content: space-between; font-weight: 700;">
                <span>🛡️ {c['check']}</span>
                <span>{c['status']}</span>
            </div>
            <div style="font-size: 0.76rem; opacity: 0.9;">{c['details']}</div>
        </div>
        """
    html += "</div>"
    return html

# Helper to render stepper steps
steps = [
    "Receiving Request",
    "AI Cognitive Analysis",
    "Decision & Routing",
    "Message Synthesis",
    "Quality Gate Check",
    "Tool Execution",
    "Finalization"
]

def render_stepper(active_index):
    html = '<div class="stepper-container">'
    for i, step in enumerate(steps):
        status_class = ""
        if i < active_index:
            status_class = "completed"
        elif i == active_index:
            status_class = "active"
        
        circle_content = "✓" if i < active_index else str(i + 1)
        
        html += f"""
        <div class="step-node {status_class}">
            <div class="step-circle">{circle_content}</div>
            <div class="step-label">{step}</div>
        </div>
        """
        if i < len(steps) - 1:
            conn_class = "completed" if i < active_index else ""
            html += f'<div class="step-connector {conn_class}"></div>'
    html += '</div>'
    return html

# ----------------- RUN WORKFLOW -----------------
with col_run:
    run_pressed = st.button("🚀 Run Communication Agent", use_container_width=True)

if run_pressed:
    if not user_request.strip():
        st.error("⚠️ Please enter a communication request.")
    elif len(user_request.strip()) < 5:
        st.warning("⚠️ Insufficient information. Please provide a more detailed communication request.")
    elif comm_mode == "🔵 Live External API" and (not groq_api_key or not groq_api_key.startswith("gsk_")):
        st.error("❌ API Key unavailable or invalid. Please check your Groq API key in the Credentials tab.")
    else:
        stepper_placeholder = st.empty()
        
        st.session_state["tool_statuses"] = {
            "Message Generator": "Pending ⏳",
            "Email Tool": "Pending ⏳",
            "Push Notification": "Pending ⏳",
            "Validation Engine": "Pending ⏳"
        }
        
        # Step 1: Request Received
        stepper_placeholder.html(render_stepper(0))
        logs = ["✓ Request received by Intelligent Communication Agent."]
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        # Step 2: AI Cognitive Analysis
        stepper_placeholder.html(render_stepper(1))
        logs.append("✓ Dispatching cognitive analyzer pipeline...")
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        decision = {}
        if comm_mode == "🔵 Live External API":
            try:
                llm = ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=0.1)
                
                system_message = """
                You are an intelligent communication assistant agent. Your task is to analyze the user's request and structure the decision into a formal JSON response.
                
                Classify the request into:
                1. Intent: One of ["Exam Announcement", "Deadline Reminder", "Meeting", "Emergency", "Maintenance", "Project Submission", "Administrative Notice", "General Announcement"]
                2. Priority: One of ["Low", "Normal", "High", "Urgent"]
                3. Audience: Clear description of target group (e.g. "All Students", "Project Team A", "Faculty Members", "System Administrators", "General Public")
                4. Channels: List containing either or both of ["Email", "Push Notification"]. Use "Push Notification" for short urgent alerts, "Email" for detailed messages, or both if highly critical/urgent.
                5. Reasoning: Concise explanation of why you made these choices.
                
                Then generate the content for the selected channels:
                - Email: { "subject": "A formal, concise email subject", "to": "suggested_recipient_email", "body": "A complete, beautifully formatted email body. Must look professional and address the target audience." }
                - Push Notification: { "title": "A short catchy title (< 40 chars)", "recipient": "suggested_recipient_username", "body": "A short, concise notification message (< 120 chars)." }
                
                Ensure that the generated messages do not contain placeholder brackets like [insert date] or [Your Name]. Instead, generate logical, realistic placeholder details (e.g., date, time, contact info) appropriate for the scenario.
                
                You must respond ONLY with a raw JSON object matching this schema:
                {
                  "intent": "Intent string",
                  "priority": "Low/Normal/High/Urgent",
                  "audience": "Audience string",
                  "channels": ["Email", "Push Notification"],
                  "reasoning": "Reasoning string",
                  "email": {
                    "subject": "Subject",
                    "to": "email@domain.com",
                    "body": "Email body content"
                  },
                  "push_notification": {
                    "title": "Title",
                    "recipient": "username",
                    "body": "Notification body"
                  }
                }
                """
                
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_request)
                ]
                
                response = llm.invoke(messages)
                raw_json = parse_llm_json(response.content)
                decision = sanitize_decision(raw_json)
                logs.append("✓ Connected to Groq API. Parsed structured JSON decisions successfully.")
            except Exception as e:
                logs.append(f"⚠️ Groq LLM parsing failed ({e}). Falling back to local simulated rules.")
                decision = simulate_agent_decision(user_request)
        else:
            decision = simulate_agent_decision(user_request)
            logs.append("✓ Local simulation parser processed the user request successfully.")
            
        time.sleep(0.4)
        
        # Step 3: Decision & Routing
        stepper_placeholder.html(render_stepper(2))
        intent = decision["intent"]
        priority = decision["priority"]
        audience = decision["audience"]
        channels = decision["channels"]
        reason = decision["reasoning"]
        channel_str = " + ".join(channels)
        
        st.session_state["latest_decision"] = {
            "intent": intent,
            "priority": priority,
            "audience": audience,
            "channel": channel_str,
            "reason": reason
        }
        
        logs.append(f"✓ Decision: Intent={intent} | Priority={priority} | Audience={audience}")
        logs.append(f"✓ Channel Routing: selected channels [{channel_str}]")
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        # Step 4: Message Synthesis
        stepper_placeholder.html(render_stepper(3))
        st.session_state["tool_statuses"]["Message Generator"] = "Running... 🔄"
        email_data = decision["email"]
        push_data = decision["push_notification"]
        
        st.session_state["latest_preview"] = {
            "email_subject": email_data["subject"],
            "email_to": email_data["to"],
            "email_body": email_data["body"],
            "notif_title": push_data["title"],
            "notif_msg": push_data["body"]
        }
        
        st.session_state["tool_statuses"]["Message Generator"] = "Completed ✅"
        logs.append("✓ Message Synthesizer generated context-aware contents.")
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        # Step 5: Quality Gate Check (Validation Engine)
        stepper_placeholder.html(render_stepper(4))
        st.session_state["tool_statuses"]["Validation Engine"] = "Running... 🔄"
        
        val_checks = run_validation_checks(intent, priority, audience, channels, email_data, push_data, user_request)
        st.session_state["validation_results"] = val_checks
        
        has_failed = any("Failed" in c["status"] for c in val_checks)
        has_warning = any("Warning" in c["status"] for c in val_checks)
        val_status_msg = "Passed ✅"
        if has_failed:
            val_status_msg = "Failed ❌"
        elif has_warning:
            val_status_msg = "Warnings ⚠️"
            
        st.session_state["tool_statuses"]["Validation Engine"] = "Completed ✅"
        logs.append(f"✓ Validation Engine check completed with status: {val_status_msg}")
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        # Step 6: Tool Execution
        stepper_placeholder.html(render_stepper(5))
        
        if "Email" in channels:
            st.session_state["tool_statuses"]["Email Tool"] = "Running... 🔄"
            time.sleep(0.3)
            res = send_email_tool.invoke({"recipient": email_data["to"], "subject": email_data["subject"], "body": email_data["body"]})
            logs.append(f"✓ [Tool Call] send_email_tool: {res}")
            st.session_state["tool_statuses"]["Email Tool"] = "Completed ✅"
        else:
            st.session_state["tool_statuses"]["Email Tool"] = "Skipped ⚪"
            
        if "Push Notification" in channels:
            st.session_state["tool_statuses"]["Push Notification"] = "Running... 🔄"
            time.sleep(0.3)
            res = send_push_notification.invoke({"target_user": push_data["recipient"], "message": push_data["body"]})
            logs.append(f"✓ [Tool Call] send_push_notification: {res}")
            st.session_state["tool_statuses"]["Push Notification"] = "Completed ✅"
        else:
            st.session_state["tool_statuses"]["Push Notification"] = "Skipped ⚪"
            
        st.session_state["latest_logs"] = logs
        time.sleep(0.4)
        
        # Step 7: Finalization
        stepper_placeholder.html(render_stepper(6))
        logs.append("✓ Execution logged. Refreshing dashboard workspace.")
        st.session_state["latest_logs"] = logs
        
        st.session_state["comm_history"].insert(0, {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Request": user_request,
            "Intent": intent,
            "Priority": priority,
            "Audience": audience,
            "Channel": channel_str,
            "Validation": val_status_msg,
            "Status": "Executed ✓" if comm_mode == "🔵 Live External API" else "Simulated ✓"
        })
        
        time.sleep(0.2)
        stepper_placeholder.empty()
        st.success("Communication Agent completed the workflow successfully!")
        st.rerun()

# ----------------- AGENT DECISION PANEL & EXECUTION MONITOR -----------------
dec = st.session_state["latest_decision"]
logs = st.session_state["latest_logs"]

pri = dec.get("priority", "Normal").strip()
if "Urgent" in pri:
    pri_badge = '<span class="badge badge-urgent">🚨 Urgent</span>'
elif "High" in pri:
    pri_badge = '<span class="badge badge-high">🟣 High</span>'
elif "Low" in pri:
    pri_badge = '<span class="badge badge-low">🟢 Low</span>'
else:
    pri_badge = '<span class="badge badge-normal">🔵 Normal</span>'

channel_val = dec.get("channel", "None")
channel_html = ""
if "Email" in channel_val:
    channel_html += '<span style="background:#F5F3FF;color:#4F46E5;padding:3px 9px;border-radius:20px;font-size:0.75rem;font-weight:700;margin-right:5px;border:1px solid #C7D2FE;">📧 Email</span>'
if "Push" in channel_val:
    channel_html += '<span style="background:#F5F3FF;color:#4F46E5;padding:3px 9px;border-radius:20px;font-size:0.75rem;font-weight:700;border:1px solid #C7D2FE;">🔔 Push Notification</span>'
if not channel_html:
    channel_html = f'<span style="color:#6B6885;">{channel_val}</span>'

logs_html = ""
for log in logs:
    text_color = "#334155"
    log_display = log
    if "✓" in log:
        log_display = log.replace("✓", "<span style='color:#818CF8;font-weight:bold;'>✓</span>")
    elif "⚠️" in log:
        log_display = log.replace("⚠️", "<span style='color:#D97706;font-weight:bold;'>⚠️</span>")
        text_color = "#92400E"
    elif "❌" in log:
        log_display = log.replace("❌", "<span style='color:#E11D48;font-weight:bold;'>❌</span>")
        text_color = "#9F1239"
    logs_html += f"<div style='font-family:monospace;font-size:0.76rem;color:{text_color};margin-bottom:5px;line-height:1.4;'>{log_display}</div>"

st.html(f"""
<div style="margin:10px 0 8px 0; font-size:1.1rem; font-weight:700; color:#1E1B4B; display:flex; align-items:center; gap:7px;">
    ⭐ Agent Intelligence &amp; Execution Monitor
</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; align-items:stretch;">

  <div class="custom-card">
    <h4>⭐ Agent Decision Panel</h4>
    <div style="display:flex; flex-direction:column; gap:10px;">
      <div>
        <div style="font-size:0.72rem; color:#6B6885; font-weight:700; margin-bottom:2px; letter-spacing:0.05em;">DETECTED INTENT</div>
        <div style="font-size:0.92rem; font-weight:700; color:#1E1B4B;">🎯 {dec.get('intent')}</div>
      </div>
      <div style="display:flex; gap:16px;">
        <div style="flex:1;">
          <div style="font-size:0.72rem; color:#6B6885; font-weight:700; margin-bottom:4px; letter-spacing:0.05em;">PRIORITY</div>
          {pri_badge}
        </div>
        <div style="flex:1;">
          <div style="font-size:0.72rem; color:#6B6885; font-weight:700; margin-bottom:2px; letter-spacing:0.05em;">AUDIENCE</div>
          <div style="font-size:0.87rem; font-weight:600; color:#1E1B4B;">👥 {dec.get('audience')}</div>
        </div>
      </div>
      <div>
        <div style="font-size:0.72rem; color:#6B6885; font-weight:700; margin-bottom:4px; letter-spacing:0.05em;">ROUTED CHANNELS</div>
        {channel_html}
      </div>
      <div>
        <div style="font-size:0.72rem; color:#6B6885; font-weight:700; margin-bottom:4px; letter-spacing:0.05em;">DECISION REASONING</div>
        <div style="font-size:0.79rem; color:#1E1B4B; line-height:1.45; background:#F5F3FF; padding:9px 11px; border-radius:9px; border:1px solid #EAE6F0; border-left:3px solid #818CF8;">
          {dec.get('reason')}
        </div>
      </div>
    </div>
  </div>

  <div class="custom-card">
    <h4>🔄 Execution Monitor (Trace Logs)</h4>
    <div style="padding:12px 14px; background:#F8FAFC; border-radius:10px; border:1px solid #EAE6F0; min-height:180px; max-height:220px; overflow-y:auto; box-sizing:border-box;">
      {logs_html}
    </div>
  </div>

</div>
""")

# ----------------- TOOL EXECUTION & VALIDATION -----------------
tool_stat = st.session_state["tool_statuses"]
tool_table_rows = ""
for t_name, icon in [
    ("Message Generator", "📝"),
    ("Email Tool", "📧"),
    ("Push Notification", "🔔"),
    ("Validation Engine", "✅")
]:
    stat = tool_stat.get(t_name, "Idle")
    badge_style = "color:#6B6885; background:#F3F1F7;"
    if "Completed" in stat:
        badge_style = "color:#4F46E5; background:#EEF2FF; font-weight:bold; border:1px solid #C7D2FE;"
    elif "Running" in stat:
        badge_style = "color:#4F46E5; background:#EEF2FF; font-weight:bold; border:1px solid #C7D2FE;"
    elif "Skipped" in stat:
        badge_style = "color:#64748B; background:#F8FAFC; border:1px dashed #E2E8F0;"
    elif "Pending" in stat:
        badge_style = "color:#92400E; background:#FEF3C7; border:1px solid #FDE68A;"
    tool_table_rows += f"""
    <tr style="border-bottom:1px solid #F3F1F7;">
      <td style="padding:9px 8px; font-size:0.81rem; font-weight:600; color:#1E1B4B;">{icon} {t_name}</td>
      <td style="padding:9px 8px; font-size:0.81rem;">
        <span style="padding:2px 9px; border-radius:12px; {badge_style}">{stat}</span>
      </td>
    </tr>"""

val_res = st.session_state["validation_results"]
val_html_content = get_validation_html(val_res)
val_status_footer = ""
if val_res:
    has_failed = any("Failed" in c["status"] for c in val_res)
    has_warning = any("Warning" in c["status"] for c in val_res)
    if has_failed:
        val_status_footer = '<div style="margin-top:10px; font-weight:700; color:#9F1239; font-size:0.81rem;">❌ Validation Gate: Rejected</div>'
    elif has_warning:
        val_status_footer = '<div style="margin-top:10px; font-weight:700; color:#1E40AF; font-size:0.81rem;">⚠️ Validation Gate: Conditional Pass</div>'
    else:
        val_status_footer = '<div style="margin-top:10px; font-weight:700; color:#059669; font-size:0.81rem;">✅ Validation Gate: All Checks Passed</div>'

st.html(f"""
<div style="margin:14px 0 8px 0; font-size:1.1rem; font-weight:700; color:#1E1B4B; display:flex; align-items:center; gap:7px;">
    🛠️ Tool Call Execution &amp; Quality Validation
</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; align-items:stretch;">

  <div class="custom-card">
    <h4>🛠️ Tool Call Dispatcher</h4>
    <table style="width:100%; border-collapse:collapse; margin-top:2px;">
      <thead>
        <tr style="border-bottom:2px solid #EAE6F0; text-align:left;">
          <th style="padding:7px 8px; font-size:0.78rem; color:#6B6885; font-weight:700;">TOOL NAME</th>
          <th style="padding:7px 8px; font-size:0.78rem; color:#6B6885; font-weight:700;">STATUS</th>
        </tr>
      </thead>
      <tbody>{tool_table_rows}</tbody>
    </table>
  </div>

  <div class="custom-card">
    <h4>🛡️ Quality Assurance (Validation Engine)</h4>
    {val_html_content}
    {val_status_footer}
  </div>

</div>
""")

# ----------------- GENERATED COMMUNICATION PREVIEW -----------------
prev = st.session_state["latest_preview"]
email_subject = prev.get("email_subject", "N/A")
email_to = prev.get("email_to", "N/A")
email_body = prev.get("email_body", "No email generated yet.")
notif_title = prev.get("notif_title", "N/A")
notif_msg = prev.get("notif_msg", "No notification generated yet.")

dec_channels = dec.get("channel", "")
is_email_active = "Email" in dec_channels
is_push_active = "Push" in dec_channels

if is_email_active:
    email_inner = f"""
    <div style="background:#F8FAFC; border:1px solid #EAE6F0; border-radius:10px; overflow:hidden; font-family:sans-serif;">
      <div style="background:#F3F1F7; padding:10px 14px; border-bottom:1px solid #EAE6F0;">
        <div style="font-size:0.8rem; color:#6B6885; margin-bottom:3px;"><b style="width:56px;display:inline-block;">From:</b> assistant@university.edu.pk</div>
        <div style="font-size:0.8rem; color:#6B6885; margin-bottom:3px;"><b style="width:56px;display:inline-block;">To:</b> <code style="color:#1E1B4B;">{email_to}</code></div>
        <div style="font-size:0.8rem; color:#6B6885;"><b style="width:56px;display:inline-block;">Subject:</b> <b style="color:#1E1B4B;">{email_subject}</b></div>
      </div>
      <div style="padding:14px 16px; background:#FFFFFF; font-size:0.82rem; color:#1E1B4B; line-height:1.55; white-space:pre-line; min-height:120px;">{email_body}</div>
      <div style="background:#F3F1F7; padding:6px 14px; border-top:1px solid #EAE6F0; font-size:0.7rem; color:#6B6885; text-align:center;">Sent via University Intelligent Communication Assistant</div>
    </div>"""
else:
    email_inner = """
    <div style="background:#F8FAFC; border:1px dashed #DFDBE5; border-radius:10px; padding:40px 20px; text-align:center; color:#94A3B8; display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:180px;">
      <div style="font-size:2rem; margin-bottom:8px;">📧</div>
      <div style="font-size:0.84rem; font-weight:600; color:#64748B;">Email Channel Deactivated</div>
      <div style="font-size:0.74rem; margin-top:4px; opacity:0.8;">Agent did not route this notice via email.</div>
    </div>"""

if is_push_active:
    push_inner = f"""
    <div style="background:rgba(30,27,75,0.95); border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:14px 16px; color:#FFFFFF; box-shadow:0 8px 24px rgba(0,0,0,0.25); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; max-width:320px; width:100%;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size:0.68rem; color:#94A3B8;">
        <span>🤖 &nbsp;<b style="letter-spacing:0.5px;">CAMPUS NOTIFY</b></span>
        <span>now</span>
      </div>
      <div style="font-size:0.83rem; font-weight:700; color:#FFFFFF; margin-bottom:3px;">{notif_title}</div>
      <div style="font-size:0.77rem; color:#CBD5E1; line-height:1.4;">{notif_msg}</div>
    </div>"""
else:
    push_inner = """
    <div style="background:#F8FAFC; border:1px dashed #DFDBE5; border-radius:14px; padding:36px 16px; text-align:center; color:#94A3B8; max-width:320px; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:120px;">
      <div style="font-size:1.8rem; margin-bottom:8px;">🔔</div>
      <div style="font-size:0.82rem; font-weight:600; color:#64748B;">Push Channel Deactivated</div>
      <div style="font-size:0.72rem; margin-top:3px; opacity:0.8;">Agent did not route this notice via push notification.</div>
    </div>"""

st.html(f"""
<div style="margin:14px 0 8px 0; font-size:1.1rem; font-weight:700; color:#1E1B4B; display:flex; align-items:center; gap:7px;">
    📧 Generated Communication Previews
</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; align-items:stretch;">

  <div class="custom-card">
    <h4>✉️ Email Preview Mockup</h4>
    {email_inner}
  </div>

  <div class="custom-card" style="display:flex; flex-direction:column;">
    <h4>📱 Push Notification Mockup</h4>
    <div style="display:flex; align-items:center; justify-content:center; flex:1; padding:16px 0;">
      {push_inner}
    </div>
  </div>

</div>
""")

# ----------------- EXECUTION HISTORY -----------------
st.markdown('<div class="section-title">📋 Execution History Logs</div>', unsafe_allow_html=True)

if st.session_state["comm_history"]:
    df = pd.DataFrame(st.session_state["comm_history"])
    
    st.dataframe(
        df,
        column_config={
            "Timestamp": st.column_config.TextColumn("Time", width="medium"),
            "Request": st.column_config.TextColumn("Original Prompt", width="large"),
            "Intent": st.column_config.TextColumn("Detected Intent"),
            "Priority": st.column_config.TextColumn("Priority"),
            "Audience": st.column_config.TextColumn("Audience"),
            "Channel": st.column_config.TextColumn("Channels"),
            "Validation": st.column_config.TextColumn("Validation Gate"),
            "Status": st.column_config.TextColumn("Status")
        },
        use_container_width=True,
        hide_index=True
    )
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Execution History (CSV)",
        data=csv,
        file_name=f"agent_execution_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
else:
    st.info("No communication history recorded yet. Use the prompt templates or enter a custom request to see agent logs.")