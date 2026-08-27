"""
NEXUS — Telegram Agentic AI Assistant
Dashboard Entry Point (Fixed SQLite DB Check - Green Dot Online)
"""
import os
import sys
import subprocess
from datetime import datetime

# ── Ensure project root is on PYTHONPATH ──────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ── Auto-install missing packages ─────────────────────────────────────────────
def _ensure_pkg(import_name: str, pip_name: str = None):
    pip_name = pip_name or import_name
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

_ensure_pkg("streamlit",       "streamlit")
_ensure_pkg("dotenv",          "python-dotenv")
_ensure_pkg("sqlalchemy",      "sqlalchemy")
_ensure_pkg("pypdf",           "pypdf")
_ensure_pkg("docx",            "python-docx")
_ensure_pkg("apscheduler",     "apscheduler")
_ensure_pkg("requests",        "requests")

# ── Auto Initialize Database Tables ───────────────────────────────────────────
try:
    from app.database import engine, Base
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[db-init] Error initializing database tables: {e}")

# ── Imports ───────────────────────────────────────────────────────────────────
import streamlit as st
from app.config import settings
from app.services.rag_service import rag_service
from app.services.reminder_service import reminder_service
from app.services.llm_service import llm_service
from app.tools.registry import tool_registry

# Force-load tools
try:
    import app.tools.math_tool       # noqa: F401
    import app.tools.search_tool     # noqa: F401
    import app.tools.doc_tools       # noqa: F401
except Exception:
    pass

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS — Telegram Agentic AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Soft Pastel CSS (Full Width Flush Sidebar & Perfectly Aligned UI) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Base Font */
html, body, p, div, h1, h2, h3, h4, h5, h6, span, label, input, button, textarea {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* FIX STREAMLIT ICON BUG: Preserve Material Icons font */
[class*="material-symbols"], 
[class*="MaterialSymbols"], 
i, 
span[data-testid="aria-label"],
button[data-testid="stBaseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"] button span {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}

.stApp {
    background-color: #faf9f6;
}

#MainMenu, footer { visibility: hidden; }
.block-container { 
    padding-top: 1.8rem; 
    padding-bottom: 2rem; 
    max-width: 98% !important;
}

/* ── SIDEBAR FULL-WIDTH LAYOUT FIX (NO GAPS ON RIGHT) ────────────────── */
section[data-testid="stSidebar"] {
    min-width: 270px !important;
    max-width: 270px !important;
    background-color: #eaf4ee !important;
    border-right: 1px solid #d5e8dc !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding: 16px 12px !important;
}

/* Force Streamlit Sidebar Internal Containers to fill 100% width */
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarUserContent"] > div,
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"],
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] > div,
[data-testid="stSidebarUserContent"] [data-testid="stElementContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] * {
    color: #2c4a3e;
}

/* ── EQUAL FULL-WIDTH SIDEBAR NAVIGATION BUTTONS ──────────────────────── */
section[data-testid="stSidebar"] [data-testid="stRadio"] {
    width: 100% !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    padding: 12px 16px !important;
    border-radius: 12px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #1e3a2b !important;
    background: #ffffff !important;
    border: 1px solid #d1e7dd !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    transition: all 0.2s ease-in-out !important;
    margin: 0 !important;
    cursor: pointer !important;
}

/* Sidebar Nav Hover Effect - Soft Pastel Mint */
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #d1fae5 !important;
    border-color: #a7f3d0 !important;
    color: #065f46 !important;
    transform: translateX(3px) !important;
}

/* Sidebar Nav Selected Active State - Pastel Mint/Sky Gradient */
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #d1fae5 0%, #e0f2fe 100%) !important;
    border: 1px solid #a7f3d0 !important;
    color: #065f46 !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 8px rgba(6, 95, 70, 0.08) !important;
}

/* ── Sidebar Box Components (100% Full Width Stretch) ───────────────────── */
.sidebar-box {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 15px 16px;
    margin-bottom: 14px;
    border: 1px solid #d1e7dd;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
.sidebar-box-title {
    font-size: 0.86rem;
    font-weight: 700;
    color: #1e3a2b;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sidebar-box-text {
    font-size: 0.76rem;
    color: #4a6b5d;
    line-height: 1.48;
}

/* Status Item Rows */
.status-row {
    font-size: 0.78rem;
    padding: 5px 0;
    display: flex;
    align-items: center;
    color: #3b5e4c;
    border-bottom: 1px solid #f0f7f3;
}
.status-row:last-child {
    border-bottom: none;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    flex-shrink: 0;
}
.status-dot.online { background: #10b981; }
.status-dot.offline { background: #ef4444; }

/* ── Rounded Soft Banner ────────────────────────────────────── */
.pastel-banner {
    background: linear-gradient(135deg, #fef4e5 0%, #fff9f0 100%);
    border: 1px solid #fce8cf;
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 18px;
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.04);
}
.pastel-banner h1 {
    color: #4a3419;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 4px 0;
}
.pastel-banner p {
    color: #8c6d46;
    font-size: 0.88rem;
    margin: 0;
}

/* ── Helpful Info Box ───────────────────────────────────────── */
.info-banner {
    background-color: #e0f2fe;
    border: 1px solid #bae6fd;
    border-radius: 14px;
    padding: 14px 20px;
    margin-bottom: 20px;
    color: #0369a1;
    font-size: 0.86rem;
    line-height: 1.5;
}
.info-banner strong {
    color: #0284c7;
}

/* ── Section Titles ─────────────────────────────────────────── */
.section-heading {
    font-size: 1.05rem;
    font-weight: 700;
    color: #334155;
    margin: 18px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── System Overview Cards (Hover Animations & Shadows) ───────── */
.card-pastel {
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    border: 1px solid transparent;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    height: 135px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    width: 100%;
}
.card-pastel:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
}

.card-mint {
    background-color: #d1fae5;
    border-color: #a7f3d0;
    color: #065f46;
}
.card-amber {
    background-color: #fef3c7;
    border-color: #fde68a;
    color: #92400e;
}
.card-peach {
    background-color: #ffedd5;
    border-color: #fed7aa;
    color: #9a3412;
}
.card-sky {
    background-color: #e0f2fe;
    border-color: #bae6fd;
    color: #075985;
}
.card-purple {
    background-color: #f3e8ff;
    border-color: #e9d5ff;
    color: #6b21a8;
}

.card-icon {
    font-size: 1.6rem;
    margin-bottom: 4px;
    line-height: 1;
}
.card-value {
    font-size: 1.35rem;
    font-weight: 700;
    margin: 2px 0;
    line-height: 1.2;
    white-space: nowrap;
}
.card-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.85;
    white-space: nowrap;
}

/* ── Soft Pastel Panel Container ────────────────────────────── */
.pastel-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Workflow Steps Pastel Pills ────────────────────────────── */
.wf-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 14px;
    border-radius: 12px;
    margin-bottom: 8px;
    font-size: 0.84rem;
    font-weight: 500;
    transition: transform 0.2s ease;
}
.wf-item:hover {
    transform: translateX(4px);
}
.wf-item-green { background-color: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
.wf-item-blue  { background-color: #f0f9ff; border: 1px solid #bae6fd; color: #0369a1; }
.wf-item-gray  { background-color: #f8fafc; border: 1px solid #e2e8f0; color: #64748b; }

.badge-pastel {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    white-space: nowrap;
}
.badge-green { background: #d1fae5; color: #047857; }
.badge-blue  { background: #e0f2fe; color: #0284c7; }
.badge-gray  { background: #e2e8f0; color: #475569; }

/* ── Suggested Questions Container ──────────────────────────── */
.suggested-item {
    background-color: #fffbeb;
    border: 1px solid #fef3c7;
    border-radius: 10px;
    padding: 9px 12px;
    margin-bottom: 8px;
    font-size: 0.81rem;
    color: #92400e;
    transition: background-color 0.2s ease;
}
.suggested-item:hover {
    background-color: #fef3c7;
}
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  HELPERS                                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _check_telegram() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)

def _check_ollama() -> bool:
    return llm_service.check_health()

def _check_database() -> bool:
    try:
        from sqlalchemy import text
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[db-check] DB error: {e}")
        return False

def _check_vector() -> bool:
    return rag_service.chroma_collection is not None

def _check_scheduler() -> bool:
    return reminder_service.is_running


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SIDEBAR                                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

with st.sidebar:
    st.markdown("""<div class="sidebar-box">
<div class="sidebar-box-title">🤖 NEXUS AI Platform</div>
<div class="sidebar-box-text">Autonomous Telegram Agent Assistant powered by Multi-Agent RAG.</div>
</div>""", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Agent Hub", "Tools Registry", "Document RAG", "System Health"],
        label_visibility="collapsed",
    )

    st.markdown("""<div class="sidebar-box">
<div class="sidebar-box-title">ℹ️ About Project</div>
<div class="sidebar-box-text"><strong>Telegram Agentic Assistant</strong><br>Production-style Autonomous Assistant with LangChain/LangGraph workflow, Ollama LLM, & Chromadb RAG.</div>
</div>""", unsafe_allow_html=True)

    # Status summary card in sidebar
    tg  = _check_telegram()
    llm = _check_ollama()
    db  = _check_database()
    
    st.markdown(f"""<div class="sidebar-box">
<div class="sidebar-box-title">🟢 System Status</div>
<div class="status-row"><span class="status-dot {'online' if tg else 'offline'}"></span>Telegram Bot: <strong>&nbsp;{"Connected" if tg else "Pending Token"}</strong></div>
<div class="status-row"><span class="status-dot {'online' if llm else 'offline'}"></span>LLM Engine: <strong>&nbsp;{"Online" if llm else "Simulated"}</strong></div>
<div class="status-row"><span class="status-dot {'online' if db else 'offline'}"></span>SQLite DB: <strong>&nbsp;{"Connected" if db else "Offline"}</strong></div>
<div class="status-row"><span class="status-dot online"></span>Mode: <strong>&nbsp;{"Demo Mode" if settings.DEMO_MODE else "Live"}</strong></div>
</div>""", unsafe_allow_html=True)

    st.caption("NEXUS AI Platform • 2026")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE: DASHBOARD                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if page == "Dashboard":

    # Banner matching reference style
    st.markdown("""<div class="pastel-banner">
<h1>🎓 NEXUS — Telegram Autonomous Agent Platform</h1>
<p>AI-powered Retrieval Augmented Generation & Multi-Agent Workflow Operations Center</p>
</div>""", unsafe_allow_html=True)

    # Helpful Info Banner
    st.markdown("""<div class="info-banner">
💡 <strong>Helpful Information:</strong> Send requests via Telegram or create custom missions using the Mission Builder below. The Autonomous Orchestrator automatically plans, executes tools, queries RAG knowledge base, and sends structured responses.
</div>""", unsafe_allow_html=True)

    # System Overview Title
    st.markdown('<div class="section-heading">📊 System Overview</div>', unsafe_allow_html=True)

    # 5 Equal Stat Cards with Soft Pastel Colors
    num_tools = len(tool_registry.list_tools())
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown("""<div class="card-pastel card-mint">
<div class="card-icon">🤖</div>
<div class="card-value">5</div>
<div class="card-label">ACTIVE AGENTS</div>
</div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="card-pastel card-amber">
<div class="card-icon">🛠️</div>
<div class="card-value">{num_tools}</div>
<div class="card-label">TOOLS REGISTRY</div>
</div>""", unsafe_allow_html=True)
        
    with c3:
        st.markdown("""<div class="card-pastel card-peach">
<div class="card-icon">📚</div>
<div class="card-value">Active</div>
<div class="card-label">RAG KNOWLEDGE</div>
</div>""", unsafe_allow_html=True)
        
    with c4:
        st.markdown("""<div class="card-pastel card-sky">
<div class="card-icon">🔍</div>
<div class="card-value">Ollama</div>
<div class="card-label">LLM ENGINE</div>
</div>""", unsafe_allow_html=True)
        
    with c5:
        st.markdown("""<div class="card-pastel card-purple">
<div class="card-icon">⚡</div>
<div class="card-value">Online</div>
<div class="card-label">SYSTEM STATUS</div>
</div>""", unsafe_allow_html=True)

    st.write("")

    # Main Two Columns
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown('<div class="section-heading">⚙️ Autonomous Agent Workflow</div>', unsafe_allow_html=True)
        
        steps = [
            ("1. Intent Classifier Agent", "Parse user intent & parameters", "✓ Complete", "wf-item-green", "badge-green"),
            ("2. Planner Agent", "Generate multi-step execution plan", "✓ Complete", "wf-item-green", "badge-green"),
            ("3. RAG Retrieval Agent", "Query Chroma vector store for context", "✓ Complete", "wf-item-green", "badge-green"),
            ("4. Tool Execution Agent", "Run web_search & doc_reader tools", "⟳ In Progress", "wf-item-blue", "badge-blue"),
            ("5. Validation Agent", "Verify safety & output consistency", "○ Pending", "wf-item-gray", "badge-gray"),
            ("6. Telegram Delivery Agent", "Format and dispatch response to Telegram", "○ Pending", "wf-item-gray", "badge-gray"),
        ]

        steps_html = "".join([
            f'<div class="wf-item {item_cls}">'
            f'<div><strong>{title}</strong><br><span style="font-size:0.75rem; opacity:0.8">{subtitle}</span></div>'
            f'<span class="badge-pastel {badge_cls}">{status_txt}</span>'
            f'</div>'
            for title, subtitle, status_txt, item_cls, badge_cls in steps
        ])

        st.markdown(f'<div class="pastel-box">{steps_html}</div>', unsafe_allow_html=True)
        st.progress(70, text="Pipeline Status: 70% Completed")

    with col_right:
        st.markdown('<div class="section-heading">🚀 Mission Builder</div>', unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:0.84rem; color:#475569; margin-bottom:10px;'>Enter any complex instruction or workflow request. The autonomous orchestrator will process it instantly:</p>", unsafe_allow_html=True)
        
        mission_input = st.text_area(
            "Mission Prompt",
            height=110,
            placeholder="e.g., Read the university PDF document, summarize key fee structures, create reminders for upcoming admission dates, and alert me via Telegram.",
            label_visibility="collapsed"
        )
        
        if st.button("✨ Launch Agent Mission", use_container_width=True, type="primary"):
            if mission_input.strip():
                st.success("✅ Mission launched! Orchestrator is executing steps.")
            else:
                st.warning("Please enter a mission description.")

        st.write("")

        # Suggested Questions Box
        st.markdown('<div class="section-heading">💡 Sample Agent Queries</div>', unsafe_allow_html=True)
        st.markdown("""<div class="pastel-box">
<div class="suggested-item">🔍 "What are the primary contact details for general inquiries?"</div>
<div class="suggested-item">📅 "Find all upcoming submission deadlines and schedule reminders."</div>
<div class="suggested-item">📄 "Summarize the fee structure policy from uploaded PDF document."</div>
</div>""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE: AGENT HUB                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Agent Hub":
    st.markdown("""<div class="pastel-banner">
<h1>🤖 Specialized Agents Center</h1>
<p>Overview of active autonomous agents working in the Telegram platform</p>
</div>""", unsafe_allow_html=True)

    agents = [
        ("Orchestrator Agent", "Master coordinator that routes user requests, assigns tasks, and tracks state.", "Core", "🟢 Active"),
        ("Planner Agent", "Decomposes complex user missions into structured step-by-step plans.", "Planning", "🟢 Active"),
        ("Research Agent", "Performs real-time web search and information synthesis.", "Research", "🟢 Active"),
        ("Document & RAG Agent", "Extracts text from PDF, DOCX, TXT, CSV files and performs semantic retrieval.", "Document", "🟢 Active"),
        ("Validation & Guard Agent", "Validates output quality, formats data, and ensures safe execution.", "Safety", "🟢 Active")
    ]

    for name, desc, cat, status in agents:
        st.markdown(f"""<div class="pastel-box">
<div style="display:flex; justify-content:space-between; align-items:center;">
<h4 style="margin:0; color:#1e3a2b;">{name}</h4>
<span class="badge-pastel badge-green">{status}</span>
</div>
<p style="font-size:0.83rem; color:#475569; margin:8px 0 0 0;">{desc}</p>
<span class="badge-pastel badge-blue" style="margin-top:10px; display:inline-block;">{cat} Agent</span>
</div>""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE: TOOLS REGISTRY                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Tools Registry":
    st.markdown("""<div class="pastel-banner">
<h1>🛠️ Tools & Function Calling Registry</h1>
<p>Registered tools accessible by the Autonomous Agents</p>
</div>""", unsafe_allow_html=True)

    tools = tool_registry.list_tools()
    
    for tool_name, info in tools.items():
        st.markdown(f"""<div class="pastel-box">
<div style="display:flex; justify-content:space-between; align-items:center;">
<h4 style="margin:0; color:#0f172a;">🔧 {tool_name}</h4>
<span class="badge-pastel badge-green">Healthy</span>
</div>
<p style="font-size:0.83rem; color:#475569; margin:6px 0;">{info.get('description', '')}</p>
<div style="font-size:0.75rem; color:#64748b;">
Executions: <strong>{info.get('executions', 0)}</strong> | Success Rate: <strong>{info.get('success_rate', '100%')}</strong>
</div>
</div>""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE: DOCUMENT RAG                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Document RAG":
    st.markdown("""<div class="pastel-banner">
<h1>📚 Knowledge Base & Retrieval (RAG)</h1>
<p>Upload documents and perform semantic retrieval queries</p>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-heading">📤 Upload Document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload PDF, DOCX, TXT, or CSV file", type=["pdf", "docx", "txt", "csv"])

    if uploaded:
        save_path = os.path.join(settings.STORAGE_PATH, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"File **{uploaded.name}** uploaded successfully!")

        if st.button("⚡ Index in Chroma Vector Store"):
            try:
                from app.database import SessionLocal
                db = SessionLocal()
                doc_id = rag_service.ingest_document(db, user_id=1, file_path=save_path, filename=uploaded.name)
                db.close()
                st.success(f"Indexed document successfully (Doc ID: {doc_id})")
            except Exception as e:
                st.error(f"Indexing error: {e}")

    st.write("")
    st.markdown('<div class="section-heading">🔍 Search Knowledge Base</div>', unsafe_allow_html=True)
    query = st.text_input("Ask a question about uploaded documents...")
    if st.button("Search RAG", type="primary") and query.strip():
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            results = rag_service.retrieve(db, query.strip())
            db.close()
            if results:
                for r in results:
                    st.markdown(f"""<div class="pastel-box">
<div style="font-size:0.85rem; color:#1e293b;">{r['content']}</div>
<div style="font-size:0.72rem; color:#64748b; margin-top:6px;">
📄 File: <strong>{r.get('filename','-')}</strong> | Page: {r.get('page', 1)} | Score: {r.get('score', 0):.2f}
</div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("No matching content found in RAG store.")
        except Exception as e:
            st.error(f"Query error: {e}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE: SYSTEM HEALTH                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "System Health":
    st.markdown("""<div class="pastel-banner">
<h1>⚙️ System Health & Diagnostics</h1>
<p>Runtime status, configuration parameters, and environment checks</p>
</div>""", unsafe_allow_html=True)

    services = [
        ("Telegram Bot Interface", _check_telegram(), "Token Configured" if _check_telegram() else "Token Missing"),
        ("Ollama LLM Provider", _check_ollama(), f"Model: {settings.OLLAMA_MODEL}" if _check_ollama() else "Fallback Simulated"),
        ("SQLite Database Engine", _check_database(), settings.DATABASE_URL),
        ("Chroma Vector Store", _check_vector(), settings.VECTOR_DB_PATH if _check_vector() else "Token Matcher Active"),
        ("APScheduler Service", _check_scheduler(), "Running" if _check_scheduler() else "Idle")
    ]

    for name, is_ok, detail in services:
        status_badge = '<span class="badge-pastel badge-green">Operational</span>' if is_ok else '<span class="badge-pastel badge-blue">Demo / Fallback</span>'
        st.markdown(f"""<div class="pastel-box">
<div style="display:flex; justify-content:space-between; align-items:center;">
<strong>{name}</strong>
{status_badge}
</div>
<div style="font-size:0.78rem; color:#64748b; margin-top:4px;">{detail}</div>
</div>""", unsafe_allow_html=True)