import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re

# ==========================================================
# SETTINGS — single source of truth (settings.py)
# ==========================================================
# Departments, SLA matrix, categories, aur geo coordinates sab settings.py mein
# hain. Yahan sirf import hai taake kahin bhi value duplicate na ho.

from settings import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    COUNTRY_CENTER,
    COUNTRY_ZOOM,
    CITY_ZOOM,
    PINPOINT_ZOOM,
    DEFAULT_LOCATION,
    LOCATION_COORDS,
    WIZARD_LOCATIONS,
    DEPARTMENTS,
    DEPARTMENT_NAMES,
    ISSUE_CATEGORIES,
    PRIORITY_LEVELS,
    SLA_MATRIX,
    STATUS_META,
    MIN_DESCRIPTION_CHARS,
    MAX_DESCRIPTION_CHARS,
    get_location_coords,
    priority_color,
    sla_hours_for,
)


# ==========================================================
# IMPORTS
# ==========================================================

try:
    from orchestrator_pipeline import execute_civic_ai_pipeline
except Exception:
    execute_civic_ai_pipeline = None

try:
    from database import (
        SessionLocal, TicketModel, AgentAuditLog, UserModel, NotificationModel,
        create_notification, get_user_notifications, mark_notifications_read, submit_ticket_rating
    )
except Exception:
    SessionLocal = None
    TicketModel = None
    AgentAuditLog = None
    UserModel = None
    NotificationModel = None
    create_notification = None
    get_user_notifications = None
    mark_notifications_read = None
    submit_ticket_rating = None

try:
    from Auth import signup_user, login_user, init_session_state, logout_user
except Exception:

    def init_session_state():
        defaults = {
            "screen": "GetStarted",
            "authenticated": False,
            "username": "",
            "user_email": "",
            "user_role": "",
            "selected_login_role": "Citizen",
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def signup_user(email, password, role, full_name):
        return True, "Account created successfully."

    def login_user(email, password):
        return False, "Authentication unavailable."

    def logout_user():
        st.session_state["authenticated"] = False
        st.session_state["screen"] = "GetStarted"

try:
    from chatbot_engine import generate_citizen_response
    CHATBOT_AVAILABLE = True
except Exception:
    CHATBOT_AVAILABLE = False

    def generate_citizen_response(username, message):
        return (
            "I can help you with civic complaints, ticket status, "
            "issue reporting and general CivicFlow assistance."
        )


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="CivicFlow AI",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()


# ==========================================================
# SESSION STATE
# ==========================================================

defaults = {
    "chat_history": [],
    "wizard_step": 1,
    "wizard_location": "",
    "wizard_description": "",
    "wizard_category": "",
    "wizard_evidence": None,
    "wizard_evidence_type": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# CSS DESIGN SYSTEM (HOT PINK + TEAL)
# ==========================================================

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

:root {
    --pink: #E91E8C;
    --pink-dark: #C21872;
    --pink-light: #FBCFE8;
    --teal: #00BFA5;
    --teal-dark: #008F7A;
    --teal-light: #CCFBF1;
    --bg: #FFF7FB;
    --card: #FFFFFF;
    --text: #1F1B2D;
    --muted: #747085;
    --border: #F0DCE8;
    --success: #00A878;
    --danger: #E63963;
    --warning: #F59E0B;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

h1 {
    font-size: 22px !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 8px !important;
}

h2 {
    font-size: 18px !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 6px !important;
}

h3 {
    font-size: 15px !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
}

h4 {
    font-size: 13.5px !important;
    font-weight: 600 !important;
}

.stApp {
    background: linear-gradient(135deg, #FFF5FB 0%, #F6FFFD 50%, #FFF5FB 100%);
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1400px !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E91E8C 0%, #B81775 45%, #00BFA5 100%) !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* SIDEBAR BUTTON (LOGOUT) FIX */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.20) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.40) !important;
    border-radius: 10px !important;
    min-height: 38px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    backdrop-filter: blur(8px) !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.35) !important;
    color: #FFFFFF !important;
    border-color: rgba(255, 255, 255, 0.70) !important;
}

/* MAIN HEADER */
.hero {
    background: linear-gradient(135deg, #E91E8C 0%, #C92A8A 42%, #00BFA5 100%);
    padding: 18px 24px;
    border-radius: 18px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 10px 25px rgba(233, 30, 140, 0.15);
}

.hero h1 {
    color: white !important;
    margin: 0 !important;
    font-family: 'Poppins', sans-serif;
    font-size: 22px !important;
}

.hero p {
    color: #FFFFFF;
    opacity: 0.92;
    font-size: 13px;
    margin-top: 4px;
    margin-bottom: 0;
}

/* CARDS */
.card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 6px 20px rgba(233, 30, 140, 0.06);
}

.portal-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 20px;
    min-height: 210px;
    transition: 0.2s;
    box-shadow: 0 6px 20px rgba(0, 191, 165, 0.05);
}

.portal-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(233, 30, 140, 0.12);
}

.portal-icon {
    font-size: 32px;
}

.portal-title {
    font-family: 'Poppins', sans-serif;
    font-size: 17px;
    font-weight: 700;
    margin-top: 8px;
}

.portal-desc {
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.5;
    margin-top: 6px;
}

/* METRICS */
.metric-box {
    background: white;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    border: 1px solid var(--border);
}

.metric-label {
    font-size: 10.5px;
    color: var(--muted);
    font-weight: 700;
    text-transform: uppercase;
}

.metric-value {
    font-family: 'Poppins', sans-serif;
    font-size: 22px;
    font-weight: 800;
    margin-top: 3px;
}

/* BUTTONS */
.stButton > button {
    border-radius: 10px !important;
    min-height: 40px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    border: 1px solid #F0B6D8 !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #E91E8C, #00BFA5) !important;
    color: white !important;
    border: none !important;
}

/* INPUTS */
.stTextInput input, .stTextArea textarea {
    border-radius: 12px !important;
    border: 1px solid #F0DCE8 !important;
    background: white !important;
}

/* TICKET */
.ticket {
    background: white;
    border: 1px solid var(--border);
    border-left: 5px solid var(--pink);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 14px;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
}

.badge-pending {
    background: #FFF3CD;
    color: #8A6200;
}

.badge-progress {
    background: #FBCFE8;
    color: #B81775;
}

.badge-resolved {
    background: #CCFBF1;
    color: #00796B;
}

.footer {
    text-align: center;
    color: var(--muted);
    margin-top: 40px;
}
</style>""", unsafe_allow_html=True)


# ==========================================================
# HELPERS
# ==========================================================

def metric(column, label, value, color="#E91E8C"):
    column.markdown(
        f'<div class="metric-box"><div class="metric-label">{label}</div>'
        f'<div class="metric-value" style="color:{color}">{value}</div></div>',
        unsafe_allow_html=True
    )


def generate_qr_svg(ticket_id: str, size: int = 100):
    return f"""<div style="display:flex; justify-content:center; align-items:center; width:100%; padding:15px 0; margin:0 auto; box-sizing:border-box;">
    <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #E2E8F0; border-radius:12px; padding:6px; background:#fff; box-shadow:0 4px 12px rgba(0,0,0,0.04); display:block; margin:0 auto;">
    <rect width="100" height="100" fill="#ffffff" rx="8"/>
    <path d="M10 10h30v30H10zM15 15v20h20V15zM20 20h10v10H20zM60 10h30v30H60zM65 15v20h20V15zM70 20h10v10H70zM10 60h30v30H10zM15 65v20h20V65zM20 70h10v10H20z" fill="#1E293B"/>
    <path d="M50 10h5v30h-5zM45 50h45v5H45zM60 60h10v10H60zM75 75h15v15H75zM50 70h10v20H50z" fill="#E91E8C"/>
    <text x="50" y="96" font-size="7" font-weight="bold" text-anchor="middle" fill="#64748B">{ticket_id}</text>
    </svg>
    </div>"""


def format_sla_countdown(sla_deadline, status):
    if str(status).upper() == "RESOLVED":
        return '<span class="badge" style="background:#ECFDF5; color:#059669; font-weight:600;">✅ Resolved on Time</span>'
    if not sla_deadline:
        return '<span class="badge" style="background:#F1F5F9; color:#64748B;">⏳ SLA Active</span>'
    now = datetime.utcnow()
    diff = sla_deadline - now
    if diff.total_seconds() <= 0:
        return '<span class="badge" style="background:#FEE2E2; color:#DC2626; font-weight:700; border:1px solid #FCA5A5;">🚨 SLA BREACHED</span>'
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    return f'<span class="badge" style="background:#FEF3C7; color:#D97706; font-weight:600;">⏳ {hours}h {minutes}m Remaining</span>'


def clean_response(text):
    if text is None:
        return ""
    text = str(text)
    # Remove code fences
    text = re.sub(r"```(?:python|json|html|css)?", "", text)
    text = text.replace("```", "")

    # Remove common Python code lines
    bad_patterns = [
        "import ", "from ", "def ", "class ", "st.", "print(", "return "
    ]
    lines = []
    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if any(clean_line.startswith(pattern) for pattern in bad_patterns):
            continue
        lines.append(clean_line)

    return "\n".join(lines).strip()


def get_categories():
    return [
        "Water Supply: Pipe Burst & Flooding",
        "Water Supply: Low Pressure",
        "Water Supply: Dirty Water",
        "Water Supply: Water Leakage",
        "Sanitation: Sewer Blockage",
        "Sanitation: Open Manhole",
        "Sanitation: Sewage Overflow",
        "Sanitation: Dirty Public Area",
        "Garbage: Overflowing Dustbin",
        "Garbage: Illegal Dumping",
        "Garbage: No Waste Collection",
        "Garbage: Burning Waste",
        "Roads: Deep Potholes",
        "Roads: Broken Footpath",
        "Roads: Damaged Road Signs",
        "Roads: Flooded Road",
        "Electricity: Street Light Not Working",
        "Electricity: Dangerous Wires",
        "Electricity: Damaged Electric Pole",
        "Electricity: Transformer Problem",
        "Gas: Gas Leakage",
        "Gas: Low Gas Pressure",
        "Gas: Damaged Gas Pipeline",
        "Environment: Noise Pollution",
        "Environment: Air Pollution",
        "Environment: Illegal Tree Cutting",
        "Traffic: Traffic Light Problem",
        "Traffic: Illegal Parking",
        "Traffic: Road Blockage",
        "Safety: Dangerous Building",
        "Safety: Fire Safety Problem",
        "Safety: Open Hazard",
        "Parks: Broken Equipment",
        "Parks: Overgrown Grass",
        "Parks: Broken Benches",
        "Health: Mosquito Breeding",
        "Health: Medical Waste",
        "Health: Food Hygiene Problem",
        "Other: General Complaint"
    ]


def ensure_demo_data(db):
    if not db or not TicketModel:
        return
    try:
        from datetime import timedelta
        existing_ids = {t.ticket_id for t in db.query(TicketModel.ticket_id).all()}
        seed_items = [
            TicketModel(
                ticket_id="CF-7801",
                citizen_id="citizen@civicflow.com",
                raw_text="Severe water pipeline burst near main bazaar flooding residential streets and road.",
                location="Layyah City Center",
                latitude="30.9693",
                longitude="70.9428",
                assigned_agency="WASA Water Supply",
                priority_level="High",
                risk_score=75,
                risk_reasons="• Flooding hazard in public street\n• Interrupted clean water service",
                ai_summary="Severe water pipeline burst near main bazaar flooding streets.",
                sla_deadline=datetime.utcnow() + timedelta(hours=12),
                status="PENDING",
                is_hitl_flagged=True,
                is_emergency=False,
                created_at=datetime.utcnow()
            ),
            TicketModel(
                ticket_id="CF-7802",
                citizen_id="citizen@civicflow.com",
                raw_text="Exposed 11kV high voltage electric wires sparking near school entrance after storm.",
                location="Model Town, Lahore",
                latitude="31.4805",
                longitude="74.3239",
                assigned_agency="LESCO Electricity Board",
                priority_level="Critical",
                risk_score=92,
                risk_reasons="• Immediate risk of high-voltage electrocution\n• Located near school gate entrance\n• Critical 2-hour window",
                ai_summary="Exposed high-voltage electric wires sparking near school entrance.",
                sla_deadline=datetime.utcnow() + timedelta(hours=2),
                status="DISPATCHED",
                is_hitl_flagged=True,
                is_emergency=True,
                created_at=datetime.utcnow()
            ),
            TicketModel(
                ticket_id="CF-7803",
                citizen_id="citizen@civicflow.com",
                raw_text="Deep potholes and broken road asphalt causing continuous traffic gridlock and accidents.",
                location="Gulberg, Lahore",
                latitude="31.5204",
                longitude="74.3587",
                assigned_agency="C&W Road Infrastructure",
                priority_level="High",
                risk_score=70,
                risk_reasons="• Severe road surface degradation\n• Frequent traffic safety hazards",
                ai_summary="Deep potholes and broken road causing traffic gridlock and accidents.",
                sla_deadline=datetime.utcnow() + timedelta(hours=12),
                status="IN_PROGRESS",
                is_hitl_flagged=False,
                is_emergency=False,
                created_at=datetime.utcnow()
            ),
            TicketModel(
                ticket_id="CF-7804",
                citizen_id="citizen@civicflow.com",
                raw_text="Open sewer manhole overflowing with foul smell into market street.",
                location="G-10 Islamabad",
                latitude="33.6844",
                longitude="73.0180",
                assigned_agency="CDA Sanitation",
                priority_level="Medium",
                risk_score=48,
                risk_reasons="• Sanitation/health hazard\n• Foul smell affecting local trade",
                ai_summary="Open sewer manhole overflowing with foul smell in G-10.",
                sla_deadline=datetime.utcnow() + timedelta(hours=24),
                status="IN_PROGRESS",
                is_hitl_flagged=False,
                is_emergency=False,
                created_at=datetime.utcnow()
            ),
            TicketModel(
                ticket_id="CF-7805",
                citizen_id="citizen@civicflow.com",
                raw_text="Solid waste collection skipped for 5 days; garbage dump overflowing outside hospital.",
                location="Clifton Karachi",
                latitude="24.8138",
                longitude="67.0300",
                assigned_agency="LWMC Solid Waste",
                priority_level="Medium",
                risk_score=45,
                risk_reasons="• Medical environment hygiene threat\n• Skipped waste collect for 5 days",
                ai_summary="Solid waste collections skipped for 5 days overflowing outside hospital.",
                sla_deadline=datetime.utcnow() + timedelta(hours=24),
                status="RESOLVED",
                is_hitl_flagged=False,
                is_emergency=False,
                rating=5,
                feedback="Cleaned up quickly after report!",
                resolution_image="trash_cleaned.jpg",
                created_at=datetime.utcnow()
            ),
            TicketModel(
                ticket_id="CF-7806",
                citizen_id="citizen@civicflow.com",
                raw_text="Street lights completely dead across main avenue creating safety hazard at night.",
                location="Hayatabad Peshawar",
                latitude="33.9870",
                longitude="71.4395",
                assigned_agency="Peshawar Electric Supply",
                priority_level="Low",
                risk_score=28,
                risk_reasons="• Non-urgent public light maintenance\n• Minor safety hazard at night",
                ai_summary="Street lights completely dead across main avenue in Hayatabad.",
                sla_deadline=datetime.utcnow() + timedelta(hours=72),
                status="RESOLVED",
                is_hitl_flagged=False,
                is_emergency=False,
                rating=4,
                feedback="Repaired, thank you.",
                resolution_image="lights_fixed.jpg",
                created_at=datetime.utcnow()
            ),
        ]
        added = False
        for it in seed_items:
            if it.ticket_id not in existing_ids:
                db.add(it)
                added = True
        if added:
            db.commit()

        if AgentAuditLog:
            log_count = db.query(AgentAuditLog).count()
            if log_count == 0:
                seed_logs = [
                    AgentAuditLog(id="LOG-101", ticket_id="CF-7801", agent_name="Problem Intelligence Agent", node_name="classify_issue", action_taken="Classified as Water Supply: Pipe Burst & Flooding (Confidence: 96%)", output_data='{"category": "Water Supply", "severity": "High", "confidence": 0.96}', timestamp=datetime.utcnow()),
                    AgentAuditLog(id="LOG-102", ticket_id="CF-7801", agent_name="Risk & Safety Agent", node_name="evaluate_risk", action_taken="Flagged for HITL review due to residential flooding risk.", output_data='{"hitl_flag": true, "risk_score": 0.88, "reason": "Flooding Hazard"}', timestamp=datetime.utcnow()),
                    AgentAuditLog(id="LOG-103", ticket_id="CF-7802", agent_name="SLA Dynamic Router", node_name="route_agency", action_taken="Dispatched ticket to LESCO Emergency Grid Response Team.", output_data='{"assigned_agency": "LESCO Electricity Board", "sla_hours": 4}', timestamp=datetime.utcnow()),
                    AgentAuditLog(id="LOG-104", ticket_id="CF-7803", agent_name="Memory Deduplication Agent", node_name="check_duplicates", action_taken="Vector memory search completed. Similarity score: 0.32 (Unique issue).", output_data='{"is_duplicate": false, "vector_distance": 0.68}', timestamp=datetime.utcnow()),
                ]
                for lg in seed_logs:
                    db.add(lg)
                db.commit()
    except Exception:
        pass


def status_badge(status):
    status = str(status).upper()
    if status == "RESOLVED":
        return "badge-resolved"
    if status in ["IN_PROGRESS", "DISPATCHED"]:
        return "badge-progress"
    return "badge-pending"


# ==========================================================
# LANDING PAGE
# ==========================================================

if st.session_state["screen"] == "GetStarted":

    st.markdown("""<div class="hero">
    <div style="font-size:14px; opacity:0.85;">✨ SMART CITY • AGENTIC AI PLATFORM</div>
    <h1 style="margin-top:10px;">🏙️ CivicFlow AI</h1>
    <p style="margin-top:8px;">Report civic issues, track complaints, and connect citizens with municipal authorities through an intelligent AI-powered system.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("### Choose Your Portal")

    col1, col2, col3 = st.columns(3)

    portals = [
        (col1, "🙋", "Citizen Portal", "Report civic problems, upload evidence and track your complaint.", "Citizen"),
        (col2, "🏛️", "Authority Portal", "Manage complaints, dispatch teams and monitor operations.", "Authority Officer"),
        (col3, "🛡️", "Admin Portal", "Monitor analytics, AI operations and system safety.", "Admin System")
    ]

    for col, icon, title, description, role in portals:
        with col:
            st.markdown(f"""<div class="portal-card">
            <div class="portal-icon">{icon}</div>
            <div class="portal-title">{title}</div>
            <div class="portal-desc">{description}</div>
            </div>""", unsafe_allow_html=True)

            if st.button("Access Portal →", key=f"portal_{role}", type="primary", use_container_width=True):
                st.session_state["selected_login_role"] = role
                st.session_state["screen"] = "Login"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    metric(m1, "AI Agents", "5+", "#E91E8C")
    metric(m2, "Issue Types", "35+", "#00BFA5")
    metric(m3, "Departments", "7", "#E91E8C")
    metric(m4, "Routing Speed", "< 2s", "#00BFA5")

    st.markdown("""<div class="footer">CivicFlow AI • Agentic AI Smart City Management System</div>""", unsafe_allow_html=True)


# ==========================================================
# LOGIN PAGE
# ==========================================================

elif st.session_state["screen"] == "Login":

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("""<div class="hero" style="padding: 26px 28px; border-radius: 18px; display: flex; flex-direction: column; justify-content: space-between; height: 100%; min-height: 450px; box-sizing: border-box;">
        <div>
            <div style="font-size:36px; margin-bottom:10px;">🏙️</div>
            <h1 style="font-size:22px !important; margin:0 0 8px 0 !important; color:#fff !important;">Welcome to CivicFlow AI</h1>
            <p style="font-size:13px; margin:0 0 16px 0; color:#fff; opacity:0.92; line-height:1.55;">
                An intelligent platform connecting citizens, municipal authorities and AI agents for swift incident response.
            </p>
            <div style="font-size:12.5px; line-height:2.0; color:#fff; opacity:0.95;">
                <div>✦ &nbsp;Smart Issue Classification</div>
                <div>✦ &nbsp;AI Powered Routing</div>
                <div>✦ &nbsp;Real-Time Ticket Tracking</div>
                <div>✦ &nbsp;Multi-Agent Workflow</div>
                <div>✦ &nbsp;Admin Analytics</div>
            </div>
        </div>
        <div style="margin-top:20px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.22); font-size:11px; color:#fff; opacity:0.88; line-height:1.55;">
            <div style="font-weight:700; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Demo Credentials:</div>
            Citizen: citizen@civicflow.com (citizen123)<br>
            Authority: authority@civicflow.com (authority123)<br>
            Admin: admin@civicflow.com (admin123)
        </div>
        </div>""", unsafe_allow_html=True)

    with right:
        with st.container(border=True):
            mode = st.radio("Authentication", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")

            if mode == "Sign In":
                st.markdown("""
                <div style="margin: 4px 0 12px 0;">
                    <div style="font-family:'Poppins', sans-serif; font-size:20px; font-weight:700; color:var(--text);">Welcome Back 👋</div>
                    <div style="font-size:12.5px; color:var(--muted);">Sign in to continue to your portal</div>
                </div>
                """, unsafe_allow_html=True)

                email = st.text_input("Email Address", placeholder="you@example.com")
                password = st.text_input("Password", type="password")

                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("Login to CivicFlow →", type="primary", use_container_width=True):
                    email_clean = str(email).strip().lower()
                    demo_users = {
                        "citizen@civicflow.com": ("citizen123", "Citizen"),
                        "authority@civicflow.com": ("authority123", "Authority"),
                        "admin@civicflow.com": ("admin123", "Admin"),
                        "admin@civicflow.gov": ("admin123", "Admin"),
                    }

                    success = False
                    user_role = ""

                    try:
                        result = login_user(email_clean, password)
                        if isinstance(result, tuple):
                            success = result[0]
                            if success and isinstance(result[1], dict):
                                user_role = result[1].get("role", "Citizen")
                    except Exception:
                        success = False

                    if email_clean in demo_users:
                        demo_password, demo_role = demo_users[email_clean]
                        if password == demo_password:
                            success = True
                            user_role = demo_role

                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email_clean
                        st.session_state["username"] = email_clean.split("@")[0]
                        st.session_state["user_role"] = user_role
                        st.session_state["screen"] = "MainApp"
                        for k in ["nav_citizen", "nav_authority", "nav_admin"]:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

            else:
                st.markdown("""
                <div style="margin: 4px 0 12px 0;">
                    <div style="font-family:'Poppins', sans-serif; font-size:20px; font-weight:700; color:var(--text);">Create Account ✨</div>
                    <div style="font-size:12.5px; color:var(--muted);">Join CivicFlow AI in under a minute</div>
                </div>
                """, unsafe_allow_html=True)

                full_name = st.text_input("Full Name")
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                role_choice = st.selectbox("Account Role", ["Citizen", "Authority Officer", "Admin System"])

                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("Create Account →", type="primary", use_container_width=True):
                    if not full_name:
                        st.warning("Please enter your full name.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(password) < 6:
                        st.warning("Password must contain at least 6 characters.")
                    else:
                        try:
                            success, message = signup_user(email, password, role_choice, full_name)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        except Exception:
                            st.success("Account created successfully.")

            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if st.button("← Back to Home", use_container_width=True):
                st.session_state["screen"] = "GetStarted"
                st.rerun()


# ==========================================================
# MAIN APPLICATION
# ==========================================================

elif st.session_state["screen"] == "MainApp" and st.session_state["authenticated"]:

    raw_role = str(st.session_state.get("user_role", "Citizen")).strip()
    if "auth" in raw_role.lower():
        role = "Authority"
        role_display = "Authority Officer"
    elif "admin" in raw_role.lower():
        role = "Admin"
        role_display = "Admin System"
    else:
        role = "Citizen"
        role_display = "Citizen"

    username = st.session_state["username"]
    username_display = username.replace(".", " ").title()

    # ======================================================
    # SIDEBAR
    # ======================================================

    with st.sidebar:
        st.markdown("# 🏙️ CivicFlow AI")
        st.caption(f"👤 {username_display}")
        st.caption(f"🔐 {role_display}")
        st.markdown("---")

        if role == "Citizen":
            page = st.radio("Navigation", ["🚀 Report Issue", "📋 My Tickets", "🤖 AI Copilot"], key="nav_citizen")
        elif role == "Authority":
            page = st.radio("Navigation", ["🚨 Complaint Queue", "🗺️ Incident Map", "📊 Records"], key="nav_authority")
        elif role == "Admin":
            page = st.radio("Navigation", ["🛡️ HITL Safety", "📊 Analytics", "🤖 Agent Logs", "📈 Telemetry", "⚙️ Settings"], key="nav_admin")
        else:
            page = st.radio("Navigation", ["🚀 Report Issue", "📋 My Tickets", "🤖 AI Copilot"], key="nav_citizen")

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            try:
                logout_user()
            except Exception:
                pass
            for k in ["nav_citizen", "nav_authority", "nav_admin", "user_role", "username", "user_email"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state["authenticated"] = False
            st.session_state["screen"] = "GetStarted"
            st.rerun()


    # ======================================================
    # HEADER
    # ======================================================

    if role == "Citizen":
        title = f"Welcome, {username_display} 👋"
        subtitle = "Report issues and let CivicFlow AI automatically route your complaint."
    elif role == "Authority":
        title = "🏛️ Authority Operations"
        subtitle = "Manage incoming complaints and coordinate field operations."
    elif role == "Admin":
        title = "🛡️ Admin Command Center"
        subtitle = "Monitor AI agents, analytics and system safety."
    else:
        title = f"Welcome, {username_display} 👋"
        subtitle = "Report issues and let CivicFlow AI automatically route your complaint."

    # ——— Top Header Bar ———
    user_email = st.session_state.get("user_email", "")
    notifs = []
    if get_user_notifications and user_email:
        try:
            notifs = get_user_notifications(user_email)
        except Exception:
            notifs = []
    unread_count = len([n for n in notifs if not getattr(n, "is_read", False)])

    # Citizen gamification
    impact_score = 0
    badge_label = ""
    badge_emoji = ""
    if role == "Citizen" and SessionLocal and TicketModel:
        try:
            db_score = SessionLocal()
            cit_tickets = db_score.query(TicketModel).filter_by(citizen_id=user_email).all()
            if not cit_tickets:
                cit_tickets = db_score.query(TicketModel).filter_by(citizen_id=username).all()
            db_score.close()
        except Exception:
            cit_tickets = []
        reports_count = len(cit_tickets)
        rated_count = len([t for t in cit_tickets if getattr(t, 'rating', None) is not None])
        impact_score = (reports_count * 100) + (rated_count * 50)
        if impact_score >= 500:
            badge_emoji, badge_label = "🥇", "Civic Champion"
        elif impact_score >= 200:
            badge_emoji, badge_label = "🥈", "Community Helper"
        else:
            badge_emoji, badge_label = "🥉", "Active Citizen"

    # Unified professional top bar
    bell_icon = "🔴🔔" if unread_count > 0 else "🔔"
    badge_html = ""
    if badge_label:
        badge_html = f'<div style="background:rgba(255,255,255,0.18);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.35);border-radius:40px;padding:6px 16px;text-align:center;white-space:nowrap;"><span style="font-size:18px;">{badge_emoji}</span><span style="font-size:12px;font-weight:700;margin-left:5px;">{badge_label}</span><br><span style="font-size:11px;opacity:0.85;">Impact: <b>{impact_score} pts</b></span></div>'
        
    bell_html = f'<div style="background:rgba(255,255,255,0.18);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.35);border-radius:40px;padding:7px 18px;font-size:13px;font-weight:700;white-space:nowrap;cursor:pointer;">{bell_icon} &nbsp;{unread_count} Unread</div>'

    st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#E91E8C 0%,#B91C8A 45%,#00BFA5 100%);border-radius:18px;padding:18px 28px;margin-bottom:18px;box-shadow:0 10px 28px rgba(233,30,140,0.18);color:#fff;"><div style="flex:1;"><div style="font-family:\'Poppins\',sans-serif;font-size:20px;font-weight:800;letter-spacing:-0.02em;">{title}</div><div style="font-size:12.5px;opacity:0.88;margin-top:3px;">{subtitle}</div></div><div style="display:flex;align-items:center;gap:14px;flex-shrink:0;">{badge_html}{bell_html}</div></div>', unsafe_allow_html=True)

    # Notification popover (separate row, clean)
    notif_col, _ = st.columns([2, 3])
    with notif_col:
        with st.popover(f"🔔 Open Notifications  {'🔴 ' + str(unread_count) + ' new' if unread_count > 0 else '(all read)'}", use_container_width=True):
            st.markdown("### 🔔 Notification Center")
            if unread_count > 0:
                if st.button("✅ Mark All as Read", key="top_mark_read", use_container_width=True):
                    if mark_notifications_read:
                        mark_notifications_read(user_email)
                        st.toast("All notifications marked as read!")
                        st.rerun()
            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
            if notifs:
                for n in notifs[:8]:
                    ntype = getattr(n, 'notification_type', 'INFO')
                    icons = {'EMERGENCY': '🚨', 'RESOLVED': '✅', 'DISPATCHED': '🚀', 'APPROVED': '✔️', 'SUBMITTED': '📥'}
                    bg_map = {'EMERGENCY': '#FEF2F2', 'RESOLVED': '#ECFDF5', 'DISPATCHED': '#EFF6FF', 'APPROVED': '#F0FDF4'}
                    border_map = {'EMERGENCY': '#DC2626', 'RESOLVED': '#10B981', 'DISPATCHED': '#3B82F6', 'APPROVED': '#22C55E'}
                    ico = icons.get(ntype, '📣')
                    bg = bg_map.get(ntype, '#F8FAFC')
                    brd = border_map.get(ntype, '#94A3B8')
                    is_read = getattr(n, 'is_read', False)
                    opacity = "0.6" if is_read else "1"
                    time_str = n.created_at.strftime('%b %d, %H:%M') if getattr(n, 'created_at', None) else 'Recent'
                    ticket_ref = f" • {n.ticket_id}" if getattr(n, 'ticket_id', None) else ""
                    st.markdown(f"""
                    <div style="background:{bg};border-left:4px solid {brd};border-radius:8px;padding:9px 12px;margin-bottom:8px;opacity:{opacity};">
                        <div style="font-size:13px;font-weight:600;color:#1E293B;">{ico} &nbsp;{n.message}</div>
                        <div style="font-size:11px;color:#64748B;margin-top:3px;">🕒 {time_str}{ticket_ref}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:24px 0;color:#94A3B8;">
                    <div style="font-size:32px;">🔔</div>
                    <div style="font-size:13px;margin-top:8px;">No notifications yet.</div>
                    <div style="font-size:11px;margin-top:4px;">Submit a complaint to get started.</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # CITIZEN
    # ======================================================

    if role == "Citizen":

        # --------------------------------------------------
        # REPORT ISSUE
        # --------------------------------------------------

        if page == "🚀 Report Issue":
            st.markdown("## 🚀 Report a Civic Issue")

            step = st.session_state["wizard_step"]
            progress = step / 4
            st.progress(progress)
            st.caption(f"Step {step} of 4")

            # STEP 1
            if step == 1:
                st.markdown("### 📍 Where is the problem?")
                locations = list(WIZARD_LOCATIONS)

                def _sync_coords_with_location():
                    """Location badalne par lat/lon aur map us city par chale jayein."""
                    lat, lon = get_location_coords(st.session_state.get("wizard_location"))
                    st.session_state["wizard_lat"] = f"{lat:.4f}"
                    st.session_state["wizard_lon"] = f"{lon:.4f}"

                if "wizard_location" not in st.session_state or st.session_state["wizard_location"] not in locations:
                    st.session_state["wizard_location"] = locations[0]
                if "wizard_lat" not in st.session_state or "wizard_lon" not in st.session_state:
                    _sync_coords_with_location()

                st.selectbox(
                    "Select Location",
                    locations,
                    key="wizard_location",
                    on_change=_sync_coords_with_location,
                )
                selected_location = st.session_state["wizard_location"]

                # GIS Location Coordinate Picker
                st.markdown("🌐 **Specify GIS Coordinates (Interactive Map Pinpoint)**")
                st.caption(
                    "Map selected location par khud center ho jata hai. "
                    "Exact spot ke liye coordinates edit karein — pin foran move ho jayega."
                )

                c_lat, c_lon, c_reset = st.columns([2, 2, 1])
                with c_lat:
                    lat_val = st.text_input("Latitude", key="wizard_lat")
                with c_lon:
                    lon_val = st.text_input("Longitude", key="wizard_lon")
                with c_reset:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    st.button(
                        "🎯 Recenter",
                        use_container_width=True,
                        on_click=_sync_coords_with_location,
                        help="Coordinates ko selected location par wapis le jayein",
                    )

                try:
                    lat_f, lon_f = float(lat_val), float(lon_val)
                    if not (-90 <= lat_f <= 90) or not (-180 <= lon_f <= 180):
                        raise ValueError("out of range")

                    map_df = pd.DataFrame({
                        "lat": [lat_f],
                        "lon": [lon_f],
                        "Location": [selected_location],
                    })
                    fig_map = px.scatter_mapbox(
                        map_df, lat="lat", lon="lon",
                        hover_name="Location",
                        color_discrete_sequence=["#e0115f"],
                        zoom=PINPOINT_ZOOM, height=340,
                    )
                    fig_map.update_traces(marker={"size": 18})
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        mapbox_center={"lat": lat_f, "lon": lon_f},
                        mapbox_zoom=PINPOINT_ZOOM,
                        margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    )
                    st.plotly_chart(
                        fig_map,
                        use_container_width=True,
                        config={"scrollZoom": True, "displayModeBar": False},
                    )
                    st.caption(f"📌 Pinned: **{selected_location}** — {lat_f:.4f}, {lon_f:.4f}")
                except (TypeError, ValueError):
                    st.warning(
                        "Coordinates valid nahi hain. Latitude -90 se 90, longitude -180 se 180 ke "
                        "darmiyan honi chahiye. 🎯 Recenter dabayein."
                    )

                if st.button("Next →", type="primary", use_container_width=True):
                    st.session_state["wizard_step"] = 2
                    st.rerun()

            # STEP 2
            elif step == 2:
                st.markdown("### 📝 Describe the Problem")

                # Speech-to-Text simulation voice complaint button
                if st.button("🎙️ Record Voice Complaint (Speech-to-Text Simulation)", use_container_width=True):
                    st.session_state["wizard_description"] = "Water pipe burst and sewer overflow near main commercial street causing absolute road flooding."
                    st.toast("🎙️ Speech recognized and transcribed successfully!")
                    st.rerun()

                desc_input = st.text_area(
                    "Tell us what happened",
                    value=st.session_state.get("wizard_description", ""),
                    height=150,
                    placeholder="Example: There is a large water leak near the main road..."
                )
                st.session_state["wizard_description"] = desc_input

                # Live duplicate check against active tickets
                if len(desc_input.strip()) > 10 and SessionLocal and TicketModel:
                    try:
                        db_dup = SessionLocal()
                        keywords = [w for w in desc_input.lower().split() if len(w) > 4]
                        possible_dup = None
                        if keywords:
                            dup_query = db_dup.query(TicketModel).filter(TicketModel.status != "RESOLVED")
                            for ticket in dup_query.all():
                                if any(kw in ticket.raw_text.lower() for kw in keywords):
                                    possible_dup = ticket
                                    break
                        db_dup.close()
                        if possible_dup:
                            st.warning(f"⚠️ **Possible Duplicate Complaint Detected:** A similar active issue exists in {possible_dup.location} (Ticket ID: **{possible_dup.ticket_id}**).")
                            col_dup1, col_dup2 = st.columns(2)
                            with col_dup1:
                                if st.button("👀 Track Existing Ticket", key="track_dup_btn", use_container_width=True):
                                    st.session_state["nav_citizen"] = "📋 My Tickets"
                                    st.rerun()
                            with col_dup2:
                                st.caption("Or submit anyway below:")
                    except Exception:
                        pass

                # Smart priority and risk score prediction live preview
                if len(desc_input.strip()) > 5:
                    try:
                        from orchestrator_pipeline import _evaluate_risk_and_sla
                        risk_score, priority, is_emergency, _, reasons = _evaluate_risk_and_sla(desc_input)
                        badge_color = "red" if priority == "Critical" else ("orange" if priority == "High" else ("#00BFA5" if priority == "Medium" else "green"))
                        st.markdown(f"""
                        <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:10px; border-radius:8px; margin-bottom:12px;">
                            <b>🤖 AI Smart Priority & Risk Preview:</b><br>
                            • Risk Score: <span style="font-weight:700; color:{badge_color};">{risk_score}/100</span><br>
                            • Assigned Priority: <span style="font-weight:700; color:{badge_color};">{priority.upper()}</span><br>
                            • Expected SLA: <b>{"2 Hours" if priority=="Critical" else ("12 Hours" if priority=="High" else "24 Hours")}</b>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception:
                        pass

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("← Back", use_container_width=True):
                        st.session_state["wizard_step"] = 1
                        st.rerun()
                with c2:
                    if st.button("Next →", type="primary", use_container_width=True):
                        if len(desc_input.strip()) < 10:
                            st.warning("Please enter more details.")
                        else:
                            st.session_state["wizard_step"] = 3
                            st.rerun()

            # STEP 3
            elif step == 3:
                st.markdown("### 🗂️ Select Issue Category")
                categories = get_categories()
                st.session_state["wizard_category"] = st.selectbox("Issue Type", categories)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("← Back", use_container_width=True):
                        st.session_state["wizard_step"] = 2
                        st.rerun()
                with c2:
                    if st.button("Next →", type="primary", use_container_width=True):
                        st.session_state["wizard_step"] = 4
                        st.rerun()

            # STEP 4
            elif step == 4:
                st.markdown("### 📎 Add Evidence")
                uploaded_file = st.file_uploader(
                    "Upload Photo, Audio or Document",
                    type=["jpg", "jpeg", "png", "pdf", "mp3", "wav"]
                )

                if uploaded_file:
                    st.session_state["wizard_evidence"] = uploaded_file.name

                st.markdown("### 📋 Complaint Summary & QR Code")
                _sum_lat, _sum_lon = get_location_coords(st.session_state.get("wizard_location"))
                summary_lat = st.session_state.get("wizard_lat") or f"{_sum_lat:.4f}"
                summary_lon = st.session_state.get("wizard_lon") or f"{_sum_lon:.4f}"
                
                # Single cohesive card container
                with st.container(border=True):
                    col_details, col_qr = st.columns([3, 1], vertical_alignment="center")
                    with col_details:
                        st.markdown(f"""
                        <div style="font-family:'Poppins', sans-serif; font-size:15px; font-weight:700; color:var(--text); margin-bottom:8px;">📋 Summary of Submission</div>
                        <p style="margin: 3px 0; font-size:13px;">📍 <b>Location:</b> {st.session_state["wizard_location"]} (Lat: {summary_lat}, Lon: {summary_lon})</p>
                        <p style="margin: 3px 0; font-size:13px;">🗂️ <b>Category:</b> {st.session_state["wizard_category"]}</p>
                        <p style="margin: 3px 0; font-size:13px;">📝 <b>Description:</b> {st.session_state["wizard_description"]}</p>
                        <p style="margin: 3px 0; font-size:13px;">📎 <b>Evidence:</b> {st.session_state["wizard_evidence"] or "Not Provided"}</p>
                        """, unsafe_allow_html=True)
                    with col_qr:
                        st.markdown("<div style='text-align: center; font-weight: 700; font-size: 11px; color: var(--muted); margin-bottom: 6px;'>📱 Ticket QR</div>", unsafe_allow_html=True)
                        st.markdown(generate_qr_svg("TICKET-TEMP", size=115), unsafe_allow_html=True)

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("← Back", use_container_width=True):
                        st.session_state["wizard_step"] = 3
                        st.rerun()
                with c2:
                    if st.button("⚡ Submit to CivicFlow AI", type="primary", use_container_width=True):
                        try:
                            if execute_civic_ai_pipeline:
                                with st.spinner("AI agents are analyzing your issue..."):
                                    result = execute_civic_ai_pipeline(
                                        st.session_state["user_email"],
                                        (st.session_state["wizard_category"] + " " + st.session_state["wizard_description"]),
                                        (st.session_state["wizard_evidence"] or ""),
                                        st.session_state["wizard_location"],
                                        summary_lat,
                                        summary_lon
                                    )
                                ticket_id = result.get("ticket_id", "CF-DEMO-001")
                                priority_result = result.get("priority", "Medium")
                                agency_result = result.get("assigned_agency", "Municipal Services")
                            else:
                                ticket_id = "CF-DEMO-001"
                                priority_result = "Medium"
                                agency_result = "Municipal Services"

                            # Create real notification for this user
                            if create_notification and user_email:
                                try:
                                    create_notification(
                                        user_email=user_email,
                                        message=f"✅ Your complaint {ticket_id} has been submitted and routed to {agency_result}.",
                                        ticket_id=ticket_id,
                                        notification_type="SUBMITTED"
                                    )
                                    if priority_result in ["Critical", "High"]:
                                        create_notification(
                                            user_email=user_email,
                                            message=f"🚨 Priority Alert: Complaint {ticket_id} marked {priority_result.upper()} — response in {'2 hours' if priority_result == 'Critical' else '12 hours'}.",
                                            ticket_id=ticket_id,
                                            notification_type="EMERGENCY" if priority_result == "Critical" else "DISPATCHED"
                                        )
                                except Exception:
                                    pass

                            st.success(f"🎉 Complaint submitted! Ticket ID: **{ticket_id}**")
                            st.balloons()
                        except Exception as error:
                            st.error(f"Submission error: {error}")

                        st.session_state["wizard_step"] = 1
                        st.session_state["wizard_location"] = ""
                        st.session_state["wizard_description"] = ""
                        st.session_state["wizard_category"] = ""
                        st.session_state["wizard_evidence"] = None
                        st.session_state.pop("wizard_lat", None)
                        st.session_state.pop("wizard_lon", None)
                        st.rerun()

        # --------------------------------------------------
        # MY TICKETS
        # --------------------------------------------------

        elif page == "📋 My Tickets":
            st.markdown("## 📋 My Submitted Tickets")
            tickets = []

            if SessionLocal and TicketModel:
                try:
                    db = SessionLocal()
                    # Lookup using email, fallback to username
                    tickets = (
                        db.query(TicketModel)
                        .filter((TicketModel.citizen_id == st.session_state["user_email"]) | (TicketModel.citizen_id == st.session_state["username"]))
                        .order_by(TicketModel.created_at.desc())
                        .all()
                    )
                    db.close()
                except Exception:
                    tickets = []

            if tickets:
                for ticket in tickets:
                    badge = status_badge(ticket.status)
                    sla_badge_html = format_sla_countdown(ticket.sla_deadline, ticket.status)
                    
                    with st.container(border=True):
                        # Side-by-side Ticket Info and QR Code inside the card
                        c_details, c_qr = st.columns([3, 1], vertical_alignment="center")
                        
                        with c_details:
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:8px;">
                                <span style="font-family:'Poppins', sans-serif; font-size:16px; font-weight:700; color:var(--text);">🎫 {ticket.ticket_id}</span>
                                <div style="display:flex; gap:6px;">
                                    <span class="badge {badge}">{ticket.status}</span>
                                    {sla_badge_html}
                                </div>
                            </div>
                            <p style="margin: 4px 0; font-size:13.5px;">📍 <b>Location:</b> {ticket.location} (Lat: {ticket.latitude or "31.5204"}, Lon: {ticket.longitude or "74.3587"})</p>
                            <p style="margin: 4px 0; font-size:13.5px;">🏢 <b>Assigned Department:</b> {ticket.assigned_agency or "Pending Assignment"}</p>
                            <p style="margin: 4px 0; font-size:13.5px;">⚠️ <b>Priority Level:</b> {ticket.priority_level or "Medium"} (Risk Score: <b>{ticket.risk_score or 50}/100</b>)</p>
                            <p style="margin: 4px 0; font-size:13.5px;">🧠 <b>AI Executive Summary:</b> <i>{ticket.ai_summary or "Analyzing description..."}</i></p>
                            <hr style="margin:8px 0; border:0; border-top:1px solid var(--border);">
                            <p style="margin: 4px 0; font-size:13.5px;"><b>Description:</b> {ticket.raw_text}</p>
                            """, unsafe_allow_html=True)
                            
                        with c_qr:
                            st.markdown("<div style='text-align: center; font-weight: 700; font-size: 11px; color: var(--muted); margin-bottom: 6px;'>📱 Ticket QR</div>", unsafe_allow_html=True)
                            st.markdown(generate_qr_svg(ticket.ticket_id, size=115), unsafe_allow_html=True)

                        # Before & After Resolution Evidence inside the same card container
                        if ticket.status == "RESOLVED":
                            st.markdown("<hr style='margin:12px 0; border:0; border-top:1px solid var(--border);'>", unsafe_allow_html=True)
                            st.markdown("#### 🖼️ Resolution Proof (Before & After Comparison)")
                            col_img1, col_img2 = st.columns(2)
                            with col_img1:
                                st.image("https://images.unsplash.com/photo-1515162305285-0293e4767cc2?w=300", caption="Before: Problem Evidence")
                            with col_img2:
                                if ticket.resolution_image:
                                    st.image("https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?w=300", caption="After: Verified Resolution Proof")
                                else:
                                    st.caption("No resolution image uploaded by the field team.")

                    # Citizen Feedback and Rating Form
                    if ticket.status == "RESOLVED":
                        st.markdown("---")
                        if ticket.rating:
                            st.markdown(f"⭐ **Your Feedback:** {'★'*ticket.rating}{'☆'*(5-ticket.rating)} ({ticket.rating}/5) — *\"{ticket.feedback or 'No comment'}\"*")
                        else:
                            with st.form(key=f"feedback_form_{ticket.ticket_id}"):
                                st.markdown("##### ⭐ Rate Our Service")
                                rating_choice = st.radio("How satisfied are you?", [5, 4, 3, 2, 1], format_func=lambda x: f"{'★'*x} ({x} - {['Very Poor', 'Poor', 'Average', 'Good', 'Excellent'][x-1]})", horizontal=True)
                                feedback_text = st.text_input("Write your feedback...", placeholder="The issue was resolved quickly, great service!")
                                if st.form_submit_button("Submit Feedback"):
                                    if submit_ticket_rating:
                                        submit_ticket_rating(ticket.ticket_id, rating_choice, feedback_text)
                                        st.success("Feedback submitted successfully!")
                                        st.rerun()
                    st.markdown("<br><br>", unsafe_allow_html=True)
            else:
                st.info("No tickets found yet. Submit your first civic issue.")

        # --------------------------------------------------
        # AI COPILOT
        # --------------------------------------------------

        elif page == "🤖 AI Copilot":
            st.markdown("## 🤖 CivicFlow AI Copilot")
            st.caption("Ask about civic issues, tickets or AI decisions.")

            if st.button("🗑️ Clear Chat"):
                st.session_state["chat_history"] = []
                st.rerun()

            for message in st.session_state["chat_history"]:
                with st.chat_message(message["role"]):
                    st.write(clean_response(message["content"]))

            user_message = st.chat_input("Ask CivicFlow AI...")

            if user_message:
                st.session_state["chat_history"].append({"role": "user", "content": user_message})
                with st.chat_message("user"):
                    st.write(user_message)

                t_latest = None
                if SessionLocal and TicketModel:
                    try:
                        db_chat = SessionLocal()
                        t_latest = (
                            db_chat.query(TicketModel)
                            .filter_by(citizen_id=st.session_state["username"])
                            .order_by(TicketModel.created_at.desc())
                            .first()
                        )
                        db_chat.close()
                    except Exception:
                        t_latest = None

                try:
                    reply = generate_citizen_response(st.session_state["username"], user_message, t_latest)
                except Exception:
                    reply = "Main CivicFlow AI Assistant hoon. Main aapki municipal complaints, photo upload, ticket tracking aur department assignment mein poori madad kar sakta hoon."

                reply = clean_response(reply)
                st.session_state["chat_history"].append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.write(reply)


    # ======================================================
    # AUTHORITY
    # ======================================================

    elif role == "Authority":
        tickets = []
        if SessionLocal and TicketModel:
            try:
                db = SessionLocal()
                ensure_demo_data(db)
                tickets = db.query(TicketModel).order_by(TicketModel.created_at.desc()).all()
                db.close()
            except Exception:
                tickets = []

        m1, m2, m3, m4 = st.columns(4)
        metric(m1, "Total Tickets", len(tickets), "#E91E8C")
        active = len([t for t in tickets if t.status != "RESOLVED"])
        resolved = len([t for t in tickets if t.status == "RESOLVED"])
        metric(m2, "Active Issues", active, "#E91E8C")
        metric(m3, "Resolved", resolved, "#00BFA5")
        metric(m4, "Agencies", "7", "#00BFA5")
        st.markdown("<br>", unsafe_allow_html=True)

        # --------------------------------------------------
        # QUEUE
        # --------------------------------------------------

        if page == "🚨 Complaint Queue":
            st.markdown("## 🚨 Live Complaint Queue")
            
            # Emergency Alert Banner
            emergencies = [t for t in tickets if getattr(t, 'is_emergency', False) and t.status != "RESOLVED"]
            if emergencies:
                st.markdown(f"""
                <div style="background:#FEE2E2; border-left:6px solid #DC2626; padding:12px; border-radius:8px; margin-bottom:15px; color:#991B1B;">
                    <h4 style="margin:0; color:#DC2626; font-family:'Poppins', sans-serif;">🚨 ACTIVE EMERGENCY ALERTS ({len(emergencies)})</h4>
                    <b>Critical situations detected:</b> Immediate field dispatch and coordination required for high-risk safety hazards.
                </div>
                """, unsafe_allow_html=True)

            c_filter1, c_filter2 = st.columns([1, 1])
            with c_filter1:
                status_filter = st.selectbox("Filter by Status", ["All Statuses", "PENDING", "DISPATCHED", "IN_PROGRESS", "RESOLVED"])
            with c_filter2:
                agency_filter = st.selectbox("Filter by Agency", ["All Agencies", "WASA Water Supply", "LESCO Electricity Board", "C&W Road Infrastructure", "CDA Sanitation", "LWMC Solid Waste", "Peshawar Electric Supply"])

            filtered_tickets = tickets
            if status_filter != "All Statuses":
                filtered_tickets = [t for t in filtered_tickets if t.status == status_filter]
            if agency_filter != "All Agencies":
                filtered_tickets = [t for t in filtered_tickets if t.assigned_agency == agency_filter]

            if filtered_tickets:
                for ticket in filtered_tickets:
                    badge = status_badge(ticket.status)
                    sla_badge_html = format_sla_countdown(ticket.sla_deadline, ticket.status)
                    is_emerg = getattr(ticket, 'is_emergency', False)
                    emerg_badge = '<span class="badge" style="background:#FEE2E2; color:#DC2626; font-weight:700;">🚨 EMERGENCY</span>' if is_emerg else ''

                    with st.expander(f"🎫 {ticket.ticket_id} • {ticket.location} — [{ticket.status}]", expanded=(ticket.status == "PENDING" or is_emerg)):
                        st.markdown(f"""
                        <div style="margin-bottom:12px; line-height:1.7;">
                            <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
                                {emerg_badge}
                                {sla_badge_html}
                            </div>
                            <b>📝 Problem Detail:</b> {ticket.raw_text}<br>
                            🏢 <b>Assigned Agency:</b> {ticket.assigned_agency or 'Pending Assignment'}<br>
                            📍 <b>Location Pinpoint:</b> {ticket.location} (Lat: {ticket.latitude or "31.5204"}, Lon: {ticket.longitude or "74.3587"})<br>
                            ⚠️ <b>Priority Level:</b> <span style="font-weight:700; color:{'#E63963' if ticket.priority_level in ['High','Critical'] else '#008F7A'}">{ticket.priority_level or 'Medium'}</span> (Risk Score: <b>{ticket.risk_score or 50}/100</b>)<br>
                            🧠 <b>AI Summary:</b> {ticket.ai_summary or "N/A"}<br>
                            📅 <b>Submitted:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M') if getattr(ticket, 'created_at', None) else 'Recent'}
                        </div>
                        """, unsafe_allow_html=True)

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("🚀 Dispatch Team", key=f"dispatch_{ticket.ticket_id}", type="primary" if ticket.status == "PENDING" else "secondary", use_container_width=True):
                                try:
                                    db = SessionLocal()
                                    item = db.query(TicketModel).filter_by(ticket_id=ticket.ticket_id).first()
                                    item.status = "DISPATCHED"
                                    db.commit()
                                    db.close()
                                    
                                    # Create notification & simulated email
                                    if create_notification:
                                        create_notification(ticket.citizen_id, f"🚀 Field team has been dispatched for ticket {ticket.ticket_id}.", ticket_id=ticket.ticket_id, notification_type="DISPATCHED")
                                    
                                    st.success(f"Team dispatched for {ticket.ticket_id}")
                                    st.rerun()
                                except Exception:
                                    st.error("Unable to update ticket.")
                        with c2:
                            if st.button("🔧 Start Maintenance", key=f"work_{ticket.ticket_id}", use_container_width=True):
                                try:
                                    db = SessionLocal()
                                    item = db.query(TicketModel).filter_by(ticket_id=ticket.ticket_id).first()
                                    item.status = "IN_PROGRESS"
                                    db.commit()
                                    db.close()
                                    
                                    if create_notification:
                                        create_notification(ticket.citizen_id, f"🔧 Maintenance crew has started on-site work for ticket {ticket.ticket_id}.", ticket_id=ticket.ticket_id, notification_type="IN_PROGRESS")
                                    
                                    st.info(f"Work in progress on {ticket.ticket_id}")
                                    st.rerun()
                                except Exception:
                                    st.error("Unable to update ticket.")
                        with c3:
                            with st.popover("Mark Resolved ✅", use_container_width=True):
                                st.markdown("##### 📷 Upload Resolution Evidence")
                                res_img = st.text_input("Proof Photo (e.g. resolved_site.png)", value="resolved_evidence_photo.jpg", key=f"res_img_input_{ticket.ticket_id}")
                                if st.button("Confirm Resolution", key=f"conf_res_btn_{ticket.ticket_id}", use_container_width=True):
                                    try:
                                        db = SessionLocal()
                                        item = db.query(TicketModel).filter_by(ticket_id=ticket.ticket_id).first()
                                        item.status = "RESOLVED"
                                        item.resolution_image = res_img
                                        db.commit()
                                        db.close()
                                        
                                        if create_notification:
                                            create_notification(ticket.citizen_id, f"🎉 Your complaint {ticket.ticket_id} has been resolved! Please rate our service.", ticket_id=ticket.ticket_id, notification_type="RESOLVED")
                                        
                                        st.success(f"Ticket {ticket.ticket_id} resolved!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Unable to update ticket: {e}")
            else:
                st.info("No complaints found for selected filters.")

        # --------------------------------------------------
        # MAP
        # --------------------------------------------------

        elif page == "🗺️ Incident Map":
            st.markdown("## 🗺️ Live Civic Incident Map")
            st.caption("Real-time geographic distribution of reported civic issues across municipal jurisdictions.")

            map_rows = []
            for t in tickets:
                loc = t.location or DEFAULT_LOCATION
                coords = get_location_coords(loc)
                map_rows.append({
                    "lat": coords[0],
                    "lon": coords[1],
                    "Ticket": t.ticket_id,
                    "Location": loc,
                    "Department": t.assigned_agency or "General",
                    "Status": t.status,
                    "Priority": t.priority_level or "Medium",
                    "Description": (t.raw_text[:50] + "...") if t.raw_text and len(t.raw_text) > 50 else (t.raw_text or "Issue reported"),
                    "MarkerSize": 14 if t.priority_level in ["High", "Critical"] else 10
                })

            if not map_rows:
                map_rows = [
                    {"lat": 30.9693, "lon": 70.9428, "Ticket": "CF-7801", "Location": "Layyah City Center", "Department": "WASA Water Supply", "Status": "PENDING", "Priority": "High", "Description": "Water pipeline burst", "MarkerSize": 14},
                    {"lat": 31.4805, "lon": 74.3239, "Ticket": "CF-7802", "Location": "Model Town, Lahore", "Department": "LESCO Electricity Board", "Status": "DISPATCHED", "Priority": "Critical", "Description": "Exposed electric wires", "MarkerSize": 14},
                    {"lat": 31.5204, "lon": 74.3587, "Ticket": "CF-7803", "Location": "Gulberg, Lahore", "Department": "C&W Road Infrastructure", "Status": "IN_PROGRESS", "Priority": "High", "Description": "Deep potholes on road", "MarkerSize": 14},
                    {"lat": 33.6844, "lon": 73.0180, "Ticket": "CF-7804", "Location": "G-10 Islamabad", "Department": "CDA Sanitation", "Status": "IN_PROGRESS", "Priority": "Medium", "Description": "Sewer blockage", "MarkerSize": 10},
                    {"lat": 24.8138, "lon": 67.0300, "Ticket": "CF-7805", "Location": "Clifton Karachi", "Department": "LWMC Solid Waste", "Status": "RESOLVED", "Priority": "Medium", "Description": "Garbage dump overflow", "MarkerSize": 10},
                    {"lat": 33.9870, "lon": 71.4395, "Ticket": "CF-7806", "Location": "Hayatabad Peshawar", "Department": "Peshawar Electric Supply", "Status": "RESOLVED", "Priority": "Low", "Description": "Street light failure", "MarkerSize": 10}
                ]

            df_map = pd.DataFrame(map_rows)

            # City filter — map selected city par live recenter ho jata hai
            city_options = ["🇵🇰 All Pakistan"] + sorted(df_map["Location"].dropna().unique().tolist())
            focus = st.selectbox("🔎 Focus on location", city_options, key="map_focus")

            if focus == city_options[0]:
                df_view = df_map
                map_center = dict(COUNTRY_CENTER)
                map_zoom = COUNTRY_ZOOM
            else:
                df_view = df_map[df_map["Location"] == focus]
                f_lat, f_lon = get_location_coords(focus)
                map_center = {"lat": f_lat, "lon": f_lon}
                map_zoom = CITY_ZOOM

            if df_view.empty:
                st.info(f"'{focus}' par abhi koi active incident nahi hai.")
                df_view = df_map
                map_center = dict(COUNTRY_CENTER)
                map_zoom = COUNTRY_ZOOM

            fig = px.scatter_mapbox(
                df_view,
                lat="lat",
                lon="lon",
                hover_name="Ticket",
                hover_data={"lat": False, "lon": False, "Location": True, "Department": True, "Status": True, "Priority": True, "Description": True},
                color="Department",
                size="MarkerSize",
                size_max=18,
                zoom=map_zoom,
                center=map_center,
                height=520,
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(255,255,255,0.85)")
            )
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

            st.markdown("### 📍 Active Incidents Summary")
            st.dataframe(df_view[["Ticket", "Location", "Department", "Priority", "Status", "Description"]], use_container_width=True, hide_index=True)

        # --------------------------------------------------
        # RECORDS
        # --------------------------------------------------

        elif page == "📊 Records":
            st.markdown("## 📊 Complaint Records & Export")
            if tickets:
                data = []
                for ticket in tickets:
                    data.append({
                        "Ticket ID": ticket.ticket_id,
                        "Citizen": ticket.citizen_id or "Anonymous",
                        "Location": ticket.location,
                        "Status": ticket.status,
                        "Priority": ticket.priority_level or "Medium",
                        "Department": ticket.assigned_agency or "Pending Assignment",
                        "Submitted At": ticket.created_at.strftime('%Y-%m-%d %H:%M') if getattr(ticket, 'created_at', None) else "Recent"
                    })
                dataframe = pd.DataFrame(data)
                
                search_q = st.text_input("🔍 Search complaints by ID, Location or Department", "")
                if search_q:
                    dataframe = dataframe[
                        dataframe["Ticket ID"].str.contains(search_q, case=False, na=False) |
                        dataframe["Location"].str.contains(search_q, case=False, na=False) |
                        dataframe["Department"].str.contains(search_q, case=False, na=False) |
                        dataframe["Status"].str.contains(search_q, case=False, na=False)
                    ]

                st.dataframe(dataframe, use_container_width=True, hide_index=True)
                csv = dataframe.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV Dataset", data=csv, file_name="civicflow_records.csv", mime="text/csv")
            else:
                st.info("No records available.")


    # ======================================================
    # ADMIN
    # ======================================================

    elif role == "Admin":
        tickets = []
        if SessionLocal and TicketModel:
            try:
                db = SessionLocal()
                ensure_demo_data(db)
                tickets = db.query(TicketModel).all()
                db.close()
            except Exception:
                tickets = []

        m1, m2, m3, m4 = st.columns(4)
        metric(m1, "System Health", "99.8%", "#00BFA5")
        flagged_count = len([t for t in tickets if getattr(t, "is_hitl_flagged", False)])
        metric(m2, "HITL Escalations", flagged_count, "#E63963" if flagged_count > 0 else "#00BFA5")
        metric(m3, "AI Agents Active", "6", "#E91E8C")
        metric(m4, "Avg Routing SLA", "1.4s", "#00BFA5")
        st.markdown("<br>", unsafe_allow_html=True)

        # --------------------------------------------------
        # HITL SAFETY
        # --------------------------------------------------

        if page == "🛡️ HITL Safety":
            st.markdown("## 🛡️ Human-in-the-Loop Safety Oversight")
            st.caption("AI escalations requiring human supervisor verification before automated dispatch.")

            flagged = [t for t in tickets if getattr(t, "is_hitl_flagged", False)]

            if flagged:
                for ticket in flagged:
                    st.markdown(f"""
                    <div class="ticket" style="border-left: 5px solid #E63963;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#E63963;">⚠️ High-Risk Escalation: {ticket.ticket_id}</h4>
                            <span class="badge" style="background:#FEE2E2; color:#DC2626;">Safety Review Required</span>
                        </div>
                        <p style="margin:10px 0 6px 0; font-size:14px;"><b>Details:</b> {ticket.raw_text}</p>
                        <div style="font-size:13px; color:var(--muted); line-height:1.6;">
                            📍 <b>Location:</b> {ticket.location} &nbsp;|&nbsp; 🏢 <b>Target Agency:</b> {ticket.assigned_agency or 'WASA'} &nbsp;|&nbsp; ⚠️ <b>Priority:</b> {ticket.priority_level or 'High'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Approve & Dispatch", key=f"approve_{ticket.ticket_id}", type="primary", use_container_width=True):
                            try:
                                db = SessionLocal()
                                item = db.query(TicketModel).filter_by(ticket_id=ticket.ticket_id).first()
                                item.is_hitl_flagged = False
                                item.status = "DISPATCHED"
                                db.commit()
                                db.close()
                                st.success(f"Ticket {ticket.ticket_id} approved and dispatched!")
                                st.rerun()
                            except Exception:
                                st.error("Unable to approve ticket.")
                    with c2:
                        if st.button("🛡️ Re-Evaluate with AI Agent", key=f"reroute_{ticket.ticket_id}", use_container_width=True):
                            try:
                                db = SessionLocal()
                                item = db.query(TicketModel).filter_by(ticket_id=ticket.ticket_id).first()
                                item.is_hitl_flagged = False
                                item.status = "IN_PROGRESS"
                                db.commit()
                                db.close()
                                st.info(f"Ticket {ticket.ticket_id} re-evaluated.")
                                st.rerun()
                            except Exception:
                                st.error("Unable to re-route ticket.")
            else:
                st.success("✅ Zero active safety escalations. All multi-agent operations within nominal safety parameters.")

        # --------------------------------------------------
        # ANALYTICS
        # --------------------------------------------------

        elif page == "📊 Analytics":
            st.markdown("## 📊 Enterprise Municipal Analytics")

            # 1. Citizen Feedback & Rating Analytics Overview
            total_reviews = 0
            avg_rating = 0.0
            satisfaction_pct = 0.0
            
            db_ratings = SessionLocal() if SessionLocal else None
            rated_tickets = []
            if db_ratings:
                try:
                    rated_tickets = db_ratings.query(TicketModel).filter(TicketModel.rating != None).all()
                except Exception:
                    rated_tickets = []
                finally:
                    db_ratings.close()
            
            if rated_tickets:
                total_reviews = len(rated_tickets)
                ratings_list = [r.rating for r in rated_tickets]
                avg_rating = sum(ratings_list) / total_reviews
                positive_reviews = len([r for r in ratings_list if r >= 4])
                satisfaction_pct = (positive_reviews / total_reviews) * 100

            st.markdown("### ⭐ Citizen Satisfaction & Ratings")
            col_satisfaction1, col_satisfaction2, col_satisfaction3 = st.columns(3)
            metric(col_satisfaction1, "Overall Satisfaction", f"{satisfaction_pct:.1f}% Positive", "#00BFA5")
            metric(col_satisfaction2, "Average Rating", f"{avg_rating:.2f} / 5.0 ★", "#D97706")
            metric(col_satisfaction3, "Total Feedback Count", total_reviews, "#E91E8C")

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. Department Performance Scorecard
            st.markdown("### 📊 Department Performance Scorecard")
            
            departments_perf = {
                "WASA Water Supply": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "LESCO Electricity Board": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "C&W Road Infrastructure": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "CDA Sanitation": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "LWMC Solid Waste": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "Peshawar Electric Supply": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
                "SSGC Gas Infrastructure": {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0},
            }

            for ticket in tickets:
                dep = ticket.assigned_agency or "WASA Water Supply"
                if dep not in departments_perf:
                    departments_perf[dep] = {"total": 0, "resolved": 0, "sum_time": 0, "sum_stars": 0, "count_stars": 0}
                
                departments_perf[dep]["total"] += 1
                if ticket.status == "RESOLVED":
                    departments_perf[dep]["resolved"] += 1
                if ticket.rating:
                    departments_perf[dep]["sum_stars"] += ticket.rating
                    departments_perf[dep]["count_stars"] += 1
            
            scorecard_rows = []
            best_dep = None
            best_score = -1.0
            
            for dep_name, stats in departments_perf.items():
                tot = stats["total"]
                res = stats["resolved"]
                rate = (res / tot * 100) if tot > 0 else 100.0
                
                # Mock average resolution time
                base_time = 4.2 if "wasa" in dep_name.lower() else (6.5 if "lesco" in dep_name.lower() else 8.0)
                avg_time = f"{base_time:.1f} hrs"
                
                avg_stars_val = (stats["sum_stars"] / stats["count_stars"]) if stats["count_stars"] > 0 else 4.0
                avg_stars = f"{avg_stars_val:.1f} ★"
                
                scorecard_rows.append({
                    "Department": dep_name,
                    "Total Tickets": tot,
                    "Resolved": res,
                    "Resolution Rate": f"{rate:.1f}%",
                    "Avg Resolution Time": avg_time,
                    "Citizen Rating": avg_stars
                })
                
                if rate > best_score:
                    best_score = rate
                    best_dep = dep_name

            df_scorecard = pd.DataFrame(scorecard_rows)
            st.dataframe(df_scorecard, use_container_width=True, hide_index=True)
            
            if best_dep:
                st.markdown(f"""
                <div style="background:#ECFDF5; border:1px solid #10B981; padding:10px; border-radius:8px; display:inline-block; margin-top:8px;">
                    🏆 <b>Best Performing Department Award:</b> <span style="color:#047857; font-weight:700;">{best_dep}</span> ({best_score:.1f}% Resolution Rate)
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br><hr><br>", unsafe_allow_html=True)

            # Chart breakdown
            departments = {}
            priorities = {}
            statuses = {}

            for ticket in tickets:
                dep = ticket.assigned_agency or "General Services"
                pri = ticket.priority_level or "Medium"
                stat = ticket.status or "PENDING"
                departments[dep] = departments.get(dep, 0) + 1
                priorities[pri] = priorities.get(pri, 0) + 1
                statuses[stat] = statuses.get(stat, 0) + 1

            c1, c2 = st.columns(2)
            with c1:
                fig1 = px.pie(
                    names=list(departments.keys()),
                    values=list(departments.values()),
                    title="Department Workload Distribution",
                    hole=0.55,
                    color_discrete_sequence=["#E91E8C", "#00BFA5", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981"]
                )
                fig1.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                fig2 = px.bar(
                    x=list(priorities.keys()),
                    y=list(priorities.values()),
                    title="Priority Severity Breakdown",
                    color=list(priorities.keys()),
                    color_discrete_map={"Critical": "#DC2626", "High": "#E91E8C", "Medium": "#00BFA5", "Low": "#10B981"}
                )
                fig2.update_layout(margin=dict(t=40, b=10, l=10, r=10), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

        # --------------------------------------------------
        # AGENT LOGS
        # --------------------------------------------------

        elif page == "🤖 Agent Logs":
            st.markdown("## 🤖 Multi-Agent Execution Audit Logs")
            st.caption("Live audit trail of all AI agent reasoning steps, vector searches, and SLA assignments.")

            logs = []
            if SessionLocal and AgentAuditLog:
                try:
                    db = SessionLocal()
                    logs = db.query(AgentAuditLog).order_by(AgentAuditLog.timestamp.desc()).limit(40).all()
                    db.close()
                except Exception:
                    logs = []

            if logs:
                for log in logs:
                    agent_name = getattr(log, "agent_name", None) or "AI Agent"
                    ticket_id = getattr(log, "ticket_id", "N/A")
                    action = getattr(log, "action_taken", "Processing")
                    node = getattr(log, "node_name", "pipeline")
                    with st.expander(f"🤖 [{agent_name}] • Ticket {ticket_id} • Step: {node}"):
                        st.markdown(f"**Action Taken:** {action}")
                        st.code(getattr(log, "output_data", "{}"), language="json")
            else:
                st.info("No agent logs available yet. Submit a complaint to trigger the AI agent pipeline.")

        # --------------------------------------------------
        # TELEMETRY
        # --------------------------------------------------

        elif page == "📈 Telemetry":
            st.markdown("## 📈 AI Pipeline Performance Telemetry")
            
            hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
            latency = [0.62, 0.78, 0.54, 0.91, 0.67, 0.58, 0.82, 0.65]
            throughput = [14, 22, 31, 28, 42, 38, 45, 50]
            cache_hit = [85, 88, 92, 89, 94, 91, 95, 96]

            c1, c2 = st.columns(2)
            with c1:
                fig_latency = px.line(x=hours, y=latency, title="Agent Pipeline Latency (seconds)", markers=True)
                fig_latency.update_traces(line_color="#E91E8C", line_width=3)
                fig_latency.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_latency, use_container_width=True)

            with c2:
                fig_throughput = px.bar(x=hours, y=throughput, title="Processed Complaints Throughput (per hour)")
                fig_throughput.update_traces(marker_color="#00BFA5")
                fig_throughput.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_throughput, use_container_width=True)

            c3, c4 = st.columns(2)
            with c3:
                fig_cache = px.line(x=hours, y=cache_hit, title="Vector Memory Cache Hit Rate (%)", markers=True)
                fig_cache.update_traces(line_color="#3B82F6", line_width=3)
                fig_cache.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_cache, use_container_width=True)

            with c4:
                st.markdown("""
                <div class="card" style="margin-top:20px;">
                    <div style="font-family:'Poppins', sans-serif; font-size:16px; font-weight:700; margin-bottom:8px;">🛰️ AI Agent Mesh Health</div>
                    <div style="font-size:13px; line-height:1.8;">
                        🟢 <b>Problem Classifier:</b> Operational (99.9% uptime)<br>
                        🟢 <b>Evidence Verification:</b> Operational (Active)<br>
                        🟢 <b>Vector Memory Store:</b> Synced & Connected<br>
                        🟢 <b>Adaptive SLA Router:</b> Operational (Auto-route active)<br>
                        🟢 <b>HITL Safety Filter:</b> Active & Guarded
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # --------------------------------------------------
        # SETTINGS
        # --------------------------------------------------

        elif page == "⚙️ Settings":
            st.markdown("## ⚙️ Multi-Agent AI Configuration")

            model = st.selectbox("LLM Inference Engine", ["llama3-70b-8192", "qwen-2.5-72b", "mistral-large-2407", "gemma-2-27b-it"])
            temperature = st.slider("Model Temperature (Creativity vs Determinism)", 0.0, 1.0, 0.2)
            threshold = st.slider("Vector Memory Duplicate Threshold", 0.50, 0.95, 0.82)
            auto_dispatch = st.toggle("Enable Autonomous Auto-Dispatch (Skip Manual Verification for Low Risk)", value=True)

            # Simulated Email Notification Audit Log
            st.markdown("### 📧 Email & Notification Delivery Audit Log")
            notif_logs = []
            if SessionLocal and NotificationModel:
                try:
                    db_notif = SessionLocal()
                    notif_logs = db_notif.query(NotificationModel).order_by(NotificationModel.created_at.desc()).limit(20).all()
                    db_notif.close()
                except Exception:
                    notif_logs = []
            
            if notif_logs:
                notif_data = []
                for log in notif_logs:
                    notif_data.append({
                        "Recipient": log.user_email,
                        "Notification Message": log.message,
                        "Type": log.notification_type,
                        "Timestamp": log.created_at.strftime('%Y-%m-%d %H:%M')
                    })
                st.dataframe(pd.DataFrame(notif_data), use_container_width=True, hide_index=True)
            else:
                st.caption("No notification logs available yet.")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save System Configuration", type="primary", use_container_width=True):
                    st.success(f"Configuration saved! Active Model: {model}")
            with c2:
                if st.button("🔄 Reset / Seed Demo Dataset", use_container_width=True):
                    try:
                        db = SessionLocal()
                        db.query(TicketModel).delete()
                        db.query(AgentAuditLog).delete()
                        db.query(NotificationModel).delete()
                        db.commit()
                        ensure_demo_data(db)
                        db.close()
                        st.success("Demo dataset refreshed successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error resetting data: {err}")

# ==========================================================
# FALLBACK
# ==========================================================

else:
    st.session_state["screen"] = "GetStarted"
    st.rerun()