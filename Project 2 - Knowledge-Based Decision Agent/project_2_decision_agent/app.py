import os
import time
import json
import tempfile
import gc
import shutil
import base64
import streamlit as st
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any

# LangChain & LangGraph Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from langgraph.graph import StateGraph, END

load_dotenv()

# ----------------- PATH & PAGE CONFIG -----------------
CHROMA_PATH = "./chroma_db"

st.set_page_config(
    page_title="Academic Advisor Decision Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- EMBEDDINGS CACHING -----------------
@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = get_embeddings()

# ----------------- DEFAULT ACADEMIC KNOWLEDGE SEED -----------------
DEFAULT_CATALOG_TEXT = """
UNIVERSITY ACADEMIC POLICY & COURSE CATALOG (2025-2026)

Section 1: General Academic Rules & Credit Limits
1.1 Maximum credit load per semester is 18 credit hours. Students with GPA >= 3.5 may request an overload up to 21 credit hours.
1.2 Minimum credit load for full-time status is 12 credit hours.
1.3 Good Academic Standing requires a minimum cumulative GPA of 2.0.
1.4 Academic Warning occurs if cumulative GPA drops below 2.0. Students on warning cannot register for more than 14 credit hours.
1.5 Graduation Requirement: Minimum 130 credit hours completed with cumulative GPA >= 2.0 and major GPA >= 2.25.

Section 2: Computer Science (BS CS) Core Course Sequences & Prerequisites
2.1 CS101: Introduction to Programming (3 Credits) - No prerequisite. Corequisite for CS101L.
2.2 CS102: Data Structures & Algorithms (4 Credits) - Prerequisite: CS101 with minimum grade C.
2.3 CS201: Object-Oriented Programming (3 Credits) - Prerequisite: CS101.
2.4 CS301: Database Management Systems (4 Credits) - Prerequisite: CS102.
2.5 CS305: Operating Systems (4 Credits) - Prerequisite: CS102 and CS201.
2.6 CS401: Artificial Intelligence & Machine Learning (3 Credits) - Prerequisite: CS102 and MATH201.
2.7 CS490: Senior Capstone Project I (3 Credits) - Prerequisite: Senior Standing (90+ completed credits) and CS301.
2.8 CS491: Senior Capstone Project II (3 Credits) - Prerequisite: CS490 passed.

Section 3: Mathematics & Basic Sciences Requirements
3.1 MATH101: Calculus I (3 Credits) - No prerequisite.
3.2 MATH102: Calculus II (3 Credits) - Prerequisite: MATH101.
3.3 MATH201: Linear Algebra & Probability (3 Credits) - Prerequisite: MATH102.
3.4 PHYS101: University Physics I (4 Credits) - Prerequisite: MATH101.

Section 4: GPA Recovery & Retake Policy
4.1 Course Repeat Policy: Courses with grade D or F can be repeated once for grade replacement in GPA calculation.
4.2 Grade Replacement Cap: Maximum 4 courses can be replaced.
4.3 Recommended Strategy for Low GPA (<2.5): Retake 1-2 core courses where grade was D or F before taking advanced 400-level electives. Limit total workload to 14 credits.

Section 5: Career Path & Specialization Electives
5.1 AI & Data Science Track: Requires CS401, CS405 (Deep Learning), CS410 (Natural Language Processing). Recommended MATH201 grade >= B.
5.2 Software Engineering Track: Requires CS310 (Software Architecture), CS320 (Web Development), CS420 (Cloud Computing).
5.3 Cybersecurity Track: Requires CS350 (Computer Networks), CS450 (Information Security), CS455 (Ethical Hacking).
"""

# Initialize Default Knowledge if DB empty
def seed_default_knowledge_if_needed():
    if not os.path.exists(CHROMA_PATH) or not os.listdir(CHROMA_PATH):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        chunks = text_splitter.create_documents(
            texts=[DEFAULT_CATALOG_TEXT], 
            metadatas=[{"source": "University_Academic_Catalog_Default.pdf", "page": 1}]
        )
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        return vector_store, 1, len(chunks)
    else:
        try:
            vs = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
            return vs, 1, vs._collection.count()
        except Exception:
            return None, 0, 0

# ----------------- SESSION STATES -----------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "uploaded_doc_list" not in st.session_state:
    st.session_state["uploaded_doc_list"] = [{"Document Name": "University_Academic_Catalog_Default.pdf", "Pages": 3, "Chunks": 8, "Status": "Seeded"}]

if "vector_store" not in st.session_state:
    vs, dc, cc = seed_default_knowledge_if_needed()
    st.session_state["vector_store"] = vs
    st.session_state["doc_count"] = dc
    st.session_state["chunk_count"] = cc
else:
    if "doc_count" not in st.session_state:
        st.session_state["doc_count"] = 1
    if "chunk_count" not in st.session_state:
        st.session_state["chunk_count"] = 8

# ----------------- THEME & CSS STYLING -----------------
st.markdown("""
<style>
    /* Main Layout Styling (Cyan, Navy & Crisp White) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-family: 'Inter', system-ui, sans-serif !important;
    }
    
    /* Sidebar Styling (Light Blue / Soft Slate Theme) */
    section[data-testid="stSidebar"], [data-testid="stSidebarUserContent"] {
        background-color: #F0F4F8 !important;
        color: #0F172A !important;
        border-right: 1px solid #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4 {
        color: #0F172A !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] p {
        color: #475569 !important;
    }

    /* Expander Box & Header styling in Sidebar (Light White Cards with Cyan Border) */
    div[data-testid="stSidebar"] details,
    div[data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1.5px solid #0EA5E9 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.08) !important;
    }

    /* Expander Header Bar */
    div[data-testid="stSidebar"] summary,
    div[data-testid="stSidebar"] .streamlit-expanderHeader,
    div[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    div[data-testid="stSidebar"] details summary {
        background-color: #FFFFFF !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 14px !important;
    }

    /* Force ALL text, paragraphs, spans, icons inside Sidebar Expander Header to Dark Navy */
    div[data-testid="stSidebar"] summary *,
    div[data-testid="stSidebar"] .streamlit-expanderHeader *,
    div[data-testid="stSidebar"] [data-testid="stExpander"] summary *,
    div[data-testid="stSidebar"] details summary *,
    div[data-testid="stSidebar"] summary p,
    div[data-testid="stSidebar"] summary span,
    div[data-testid="stSidebar"] summary div {
        color: #0F172A !important;
        fill: #0F172A !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }

    /* Body Inside Expander */
    div[data-testid="stSidebar"] [data-testid="stExpanderDetails"],
    div[data-testid="stSidebar"] details[open] > div {
        background-color: #F8FAFC !important;
        padding: 14px !important;
        border-top: 1px solid #BAE6FD !important;
    }

    /* Sidebar Widget Labels readability (Groq API Key, Model Engine, Sliders, etc) */
    div[data-testid="stSidebar"] label,
    div[data-testid="stSidebar"] label *,
    div[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
    div[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    div[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }

    div[data-testid="stSidebar"] input,
    div[data-testid="stSidebar"] textarea {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    
    /* Hero Header Container */
    .hero-header {
        background: linear-gradient(135deg, #0F172A 0%, #0E7490 50%, #06B6D4 100%) !important;
        border-radius: 14px !important;
        padding: 24px 28px !important;
        color: #FFFFFF !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 24px -6px rgba(14, 116, 144, 0.3) !important;
    }
    .hero-header h1 {
        color: #FFFFFF !important;
        margin: 0 !important;
        font-size: 1.75rem !important;
        font-weight: 800 !important;
    }
    .hero-header p {
        color: #E0F2FE !important;
        margin: 6px 0 0 0 !important;
        font-size: 0.95rem !important;
    }
    
    /* Pixel-Perfect Equal Stat / Analytics Cards */
    .stat-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
        border-top: 3px solid #0891B2 !important;
        height: 84px !important;
        min-height: 84px !important;
        max-height: 84px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        box-sizing: border-box !important;
    }
    .stat-label {
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #0E7490 !important;
        margin-bottom: 2px !important;
    }
    .stat-num {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Content & Result Cards */
    .content-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 20px 22px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 3px 12px rgba(0,0,0,0.02) !important;
    }
    .card-title {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 10px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    /* LangGraph Flow Pipeline Cards */
    .graph-node-card {
        background: #F0F9FF !important;
        border: 1px solid #BAE6FD !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        color: #0369A1 !important;
        font-weight: 600 !important;
        height: 48px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Primary Buttons & Preset Buttons Styling (Force Bold Crisp White Text) */
    .stButton>button,
    section[data-testid="stSidebar"] .stButton>button,
    div[data-testid="column"] .stButton>button {
        background: linear-gradient(135deg, #0E7490 0%, #0891B2 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 12px rgba(14, 116, 144, 0.25) !important;
    }

    /* Force ALL inner text/spans/paragraphs/divs on buttons to solid white */
    .stButton>button *,
    section[data-testid="stSidebar"] .stButton>button *,
    div[data-testid="column"] .stButton>button *,
    .stButton>button p,
    .stButton>button span,
    .stButton>button div {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 700 !important;
    }

    .stButton>button:hover,
    section[data-testid="stSidebar"] .stButton>button:hover,
    div[data-testid="column"] .stButton>button:hover {
        background: linear-gradient(135deg, #155E75 0%, #0E7490 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 14px rgba(14, 116, 144, 0.35) !important;
    }

    /* Preset Chip Buttons Sizing */
    div[data-testid="column"] .stButton>button {
        height: 54px !important;
        min-height: 54px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: 0.84rem !important;
        width: 100% !important;
    }

    /* Source Citation Badges */
    .source-badge {
        background: #F1F5F9 !important;
        border-left: 3px solid #0EA5E9 !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
        font-size: 0.82rem !important;
        margin-top: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- LANGGRAPH WORKFLOW DEFINITION -----------------

class AdvisorState(TypedDict):
    query: str
    profile: Dict[str, Any]
    retrieved_context: str
    retrieved_docs: List[Any]
    analysis: str
    recommendations: str
    validation: str
    final_decision: str

def build_langgraph_workflow(vector_store, groq_api_key, model_name, top_k, min_relevance):
    
    # 1. Knowledge Retriever Node
    def retrieve_knowledge_node(state: AdvisorState) -> AdvisorState:
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": top_k, "score_threshold": min_relevance}
        )
        query = state["query"]
        profile_str = f"Major: {state['profile'].get('major')}, Semester: {state['profile'].get('semester')}, Current GPA: {state['profile'].get('gpa')}"
        augmented_query = f"{query} {profile_str}"
        
        try:
            docs = retriever.invoke(augmented_query)
        except Exception:
            docs = []
            
        context_str = "\n\n".join([f"[Source: {d.metadata.get('source', 'Rules')}, Page: {d.metadata.get('page', 1)}] {d.page_content}" for d in docs]) if docs else "No specific catalog policy retrieved."
        state["retrieved_docs"] = docs
        state["retrieved_context"] = context_str
        return state

    # 2. Academic Situation Analyzer Node
    def analyze_profile_node(state: AdvisorState) -> AdvisorState:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name, temperature=0.1)
        prompt = ChatPromptTemplate.from_template(
            "You are an expert Academic Advisor Supervisor. Analyze the student's academic standing against university policies.\n\n"
            "Student Profile:\n"
            "- Major: {major}\n"
            "- Semester: {semester}\n"
            "- Current GPA: {gpa} (Target: {target_gpa})\n"
            "- Completed Courses/Credits: {completed_courses}\n\n"
            "Retrieved University Catalog Context:\n{context}\n\n"
            "User Specific Question:\n{query}\n\n"
            "Task: Provide a concise analysis of the student's status, academic standing (Good / Warning), credit limits, and key missing prerequisites or degree milestones."
        )
        chain = prompt | llm | StrOutputParser()
        analysis_res = chain.invoke({
            "major": state['profile'].get('major'),
            "semester": state['profile'].get('semester'),
            "gpa": state['profile'].get('gpa'),
            "target_gpa": state['profile'].get('target_gpa'),
            "completed_courses": state['profile'].get('completed_courses'),
            "context": state['retrieved_context'],
            "query": state['query']
        })
        state["analysis"] = analysis_res
        return state

    # 3. Recommendation Generator Node
    def generate_recommendation_node(state: AdvisorState) -> AdvisorState:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name, temperature=0.2)
        prompt = ChatPromptTemplate.from_template(
            "You are an Academic Advisor Specialist. Based on the situation analysis and university catalog rules, generate concrete, actionable recommendations.\n\n"
            "Analysis:\n{analysis}\n\n"
            "Catalog Context:\n{context}\n\n"
            "Task: Generate:\n"
            "1. Recommended Course Schedule for the next semester (with credit hours and priority).\n"
            "2. GPA Optimization Strategy (retakes, workload limit recommendations).\n"
            "3. Career / Track Specialization Advice.\n"
            "Format clearly with bullet points."
        )
        chain = prompt | llm | StrOutputParser()
        rec_res = chain.invoke({
            "analysis": state['analysis'],
            "context": state['retrieved_context']
        })
        state["recommendations"] = rec_res
        return state

    # 4. Prerequisite & Policy Validator Node
    def validate_decision_node(state: AdvisorState) -> AdvisorState:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name, temperature=0.1)
        prompt = ChatPromptTemplate.from_template(
            "You are an Academic Compliance Officer & Registrar Validator.\n\n"
            "Recommendations Proposed:\n{recommendations}\n\n"
            "Student Profile (GPA: {gpa}):\n"
            "University Rules Context:\n{context}\n\n"
            "Task: Perform strict compliance validation:\n"
            "- Prerequisite Check: Are required prerequisites satisfied?\n"
            "- Workload Limit Check: Is credit load within allowed limit (18 max, 14 if low GPA)?\n"
            "- Overall Approval Status: APPROVED / CONDITIONAL APPROVAL / REJECTED.\n"
            "Provide a final summary statement."
        )
        chain = prompt | llm | StrOutputParser()
        val_res = chain.invoke({
            "recommendations": state['recommendations'],
            "gpa": state['profile'].get('gpa'),
            "context": state['retrieved_context']
        })
        state["validation"] = val_res
        state["final_decision"] = f"### 🎓 Advisor Analysis\n{state['analysis']}\n\n### 🎯 Recommended Course & Action Plan\n{state['recommendations']}\n\n### ✅ Policy Compliance & Validation\n{state['validation']}"
        return state

    # Create StateGraph
    builder = StateGraph(AdvisorState)
    builder.add_node("retriever", retrieve_knowledge_node)
    builder.add_node("analyzer", analyze_profile_node)
    builder.add_node("recommender", generate_recommendation_node)
    builder.add_node("validator", validate_decision_node)

    builder.set_entry_point("retriever")
    builder.add_edge("retriever", "analyzer")
    builder.add_edge("analyzer", "recommender")
    builder.add_edge("recommender", "validator")
    builder.add_edge("validator", END)

    return builder.compile()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🎓 Academic Advisor Agent")
    st.markdown("<p style='font-size: 0.8rem; color: #94A3B8;'>LangGraph + ChromaDB Decision System</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.expander("⚙️ **Engine Configuration**", expanded=True):
        env_key = os.getenv("GROQ_API_KEY", "")
        groq_api_key = st.text_input("Groq API Key", type="password", value=env_key, placeholder="gsk_...")
        selected_model = st.selectbox("Model Engine", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile", "llama3-70b-8192"])
        top_k = st.slider("Top-K Rules Retrieved", min_value=1, max_value=8, value=4)
        min_relevance = st.slider("Match Cutoff Score", min_value=0.0, max_value=0.8, value=0.15, step=0.05)

    with st.expander("👤 **Student Profile Context**", expanded=True):
        student_major = st.selectbox("Major / Department", ["Computer Science (BS CS)", "Software Engineering (BS SE)", "Data Science (BS DS)", "Cyber Security (BS CY)"])
        student_semester = st.selectbox("Current Semester", ["Semester 1 (Freshman)", "Semester 2 (Freshman)", "Semester 3 (Sophomore)", "Semester 4 (Sophomore)", "Semester 5 (Junior)", "Semester 6 (Junior)", "Semester 7 (Senior)", "Semester 8 (Senior)"])
        student_gpa = st.number_input("Current Cumulative GPA", min_value=0.0, max_value=4.0, value=2.45, step=0.05)
        target_gpa = st.number_input("Target GPA Goal", min_value=0.0, max_value=4.0, value=3.20, step=0.05)
        completed_courses = st.text_area("Completed Courses & Grades", value="CS101 (C), MATH101 (B), CS102 (D+), PHYS101 (C+), CS201 (B)", help="List completed courses and grades for prerequisite validation.")

    with st.expander("🔄 **LangGraph Workflow Nodes**", expanded=True):
        st.markdown("🟢 **Node 1:** ChromaDB Retriever")
        st.markdown("🟢 **Node 2:** Situation Analyzer")
        st.markdown("🟢 **Node 3:** Recommendation Engine")
        st.markdown("🟢 **Node 4:** Compliance Validator")

    st.markdown("---")
    if st.button("🔥 Reset Agent Memory & DB", use_container_width=True):
        st.session_state["chat_history"] = []
        if os.path.exists(CHROMA_PATH):
            try:
                shutil.rmtree(CHROMA_PATH)
            except Exception:
                pass
        vs, dc, cc = seed_default_knowledge_if_needed()
        st.session_state["vector_store"] = vs
        st.session_state["doc_count"] = dc
        st.session_state["chunk_count"] = cc
        st.success("Agent state reset!")
        st.rerun()

# ----------------- HERO HEADER -----------------
st.markdown("""
<div class="hero-header">
    <h1>🎓 Academic Advisor Decision Agent</h1>
    <p>Knowledge-Based Decision Engine powered by LangGraph Orchestration & ChromaDB Vector Search</p>
</div>
""", unsafe_allow_html=True)

# ----------------- ANALYTICS & SYSTEM STATUS -----------------
sc1, sc2, sc3, sc4 = st.columns(4)

with sc1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">📚 Knowledge Base Docs</div>
        <div class="stat-num">{st.session_state['doc_count']} Catalog File(s)</div>
    </div>
    """, unsafe_allow_html=True)

with sc2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🧩 Policy Chunks</div>
        <div class="stat-num">{st.session_state['chunk_count']} Rule Vectors</div>
    </div>
    """, unsafe_allow_html=True)

with sc3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">👤 Student Standing</div>
        <div class="stat-num">GPA: {student_gpa:.2f} ({'Warning' if student_gpa < 2.0 else 'Active'})</div>
    </div>
    """, unsafe_allow_html=True)

with sc4:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">⚡ Workflow Engine</div>
        <div class="stat-num" style="color: #0E7490;">LangGraph Ready</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- KNOWLEDGE BASE MANAGER (PDF INGESTION) -----------------
with st.expander("📂 **1. Knowledge Base Manager (Course Catalog & Academic Rules PDF Ingestion)**", expanded=False):
    uploaded_files = st.file_uploader(
        "Upload University Course Catalogs, Degree Roadmaps, or Academic Policy PDFs", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    
    if st.button("🚀 Index & Update Vector Database"):
        if not uploaded_files:
            st.warning("Please select at least one PDF file.")
        else:
            with st.spinner("Processing & embedding academic documents into ChromaDB..."):
                documents = []
                summary_list = []
                splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)

                for f in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(f.read())
                        tmp_p = tmp.name

                    loader = PyPDFLoader(tmp_p)
                    docs = loader.load()
                    for d in docs:
                        d.metadata["source"] = f.name
                    
                    file_chunks = splitter.split_documents(docs)
                    documents.extend(docs)
                    summary_list.append({"Document Name": f.name, "Pages": len(docs), "Chunks": len(file_chunks), "Status": "Indexed"})
                    os.remove(tmp_p)

                all_chunks = splitter.split_documents(documents)
                vector_store = Chroma.from_documents(documents=all_chunks, embedding=embeddings, persist_directory=CHROMA_PATH)
                st.session_state["vector_store"] = vector_store
                st.session_state["doc_count"] = len(uploaded_files)
                st.session_state["chunk_count"] = len(all_chunks)
                st.session_state["uploaded_doc_list"] = summary_list
                st.success("🎉 Academic Knowledge Base updated successfully!")
                st.rerun()

    if st.session_state["uploaded_doc_list"]:
        st.markdown("#### 📋 Active Catalog Index Summary")
        st.dataframe(st.session_state["uploaded_doc_list"], use_container_width=True, hide_index=True)

# ----------------- QUICK DECISION SCENARIOS -----------------
st.markdown("### 💡 Quick Advisement Scenarios")
qp1, qp2, qp3, qp4 = st.columns(4)

preset_query = ""
if qp1.button("📌 Course Schedule Optimization", use_container_width=True):
    preset_query = "What courses should I register for next semester based on my prerequisites and major requirements?"
if qp2.button("📌 GPA Recovery Roadmap", use_container_width=True):
    preset_query = "My current GPA is low. What grade repeat options or workload strategy can help improve my GPA?"
if qp3.button("📌 Prerequisite & Capstone Check", use_container_width=True):
    preset_query = "Am I eligible to register for Senior Capstone Project CS490 and CS301 Database Systems?"
if qp4.button("📌 Career Track Specialization", use_container_width=True):
    preset_query = "I want to specialize in AI & Machine Learning. What elective sequence and MATH prerequisites do I need?"

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- INTERACTIVE QUERY STUDIO -----------------
st.markdown("### 💬 Ask Academic Advisor Decision Agent")

query_input = st.text_input(
    "Enter your academic decision query:",
    value=preset_query if preset_query else "",
    placeholder="e.g., Recommend a 15-credit course plan for next semester that balances core CS requirements and GPA recovery...",
    label_visibility="collapsed"
)

run_clicked = st.button("🚀 Execute Advisor Decision Workflow")

# ----------------- EXECUTION & DECISION VISUALIZATION -----------------
if run_clicked or preset_query:
    if not query_input.strip():
        st.warning("Please enter a question or query.")
    elif not groq_api_key or not groq_api_key.startswith("gsk_"):
        st.error("🔑 Invalid Groq API Key! Please enter a valid API key in the sidebar.")
    elif not st.session_state["vector_store"]:
        st.error("Vector Database is not initialized.")
    else:
        st.markdown("---")
        st.markdown("### 🔄 LangGraph Execution Progress")
        
        # Step Visual Cards Container
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        
        with st.spinner("Running LangGraph Multi-Stage Advisor Graph..."):
            start_t = time.time()
            
            # Build student profile dict
            profile_data = {
                "major": student_major,
                "semester": student_semester,
                "gpa": student_gpa,
                "target_gpa": target_gpa,
                "completed_courses": completed_courses
            }
            
            # Compile Graph
            app_graph = build_langgraph_workflow(
                vector_store=st.session_state["vector_store"],
                groq_api_key=groq_api_key,
                model_name=selected_model,
                top_k=top_k,
                min_relevance=min_relevance
            )
            
            # Initial State
            initial_state: AdvisorState = {
                "query": query_input,
                "profile": profile_data,
                "retrieved_context": "",
                "retrieved_docs": [],
                "analysis": "",
                "recommendations": "",
                "validation": "",
                "final_decision": ""
            }
            
            # Execute Graph safely
            try:
                final_state = app_graph.invoke(initial_state)
                elapsed = round(time.time() - start_t, 2)
            except Exception as e:
                err_str = str(e)
                if "404" in err_str or "model_not_found" in err_str:
                    st.error(f"⚠️ **Groq Model Error (404 Not Found):** The model `{selected_model}` is deprecated or unavailable on your Groq API key.\n\n👉 **Solution:** Please change the **Model Engine** dropdown in the sidebar to `llama-3.3-70b-versatile` or `llama3-70b-8192` and try again!")
                elif "401" in err_str or "invalid_api_key" in err_str:
                    st.error("🔑 **Invalid Groq API Key!** Please verify your Groq API key in the sidebar.")
                else:
                    st.error(f"⚠️ **Execution Error:** {err_str}")
                st.stop()
            
        # Display Visual Nodes Execution
        p_col1.markdown('<div class="graph-node-card">✓ Node 1: ChromaDB RAG Context</div>', unsafe_allow_html=True)
        p_col2.markdown('<div class="graph-node-card">✓ Node 2: Situation Analyzer</div>', unsafe_allow_html=True)
        p_col3.markdown('<div class="graph-node-card">✓ Node 3: Recommendation Engine</div>', unsafe_allow_html=True)
        p_col4.markdown('<div class="graph-node-card">✓ Node 4: Compliance Validator</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ----------------- OUTPUT TABS / CARDS -----------------
        tab_dec, tab_ana, tab_rec, tab_val, tab_src = st.tabs([
            "🎓 Final Decision Report", 
            "📊 Situation Analysis", 
            "🎯 Course Recommendations", 
            "✅ Compliance Validation", 
            "📑 Retrieved Catalog Rules"
        ])

        with tab_dec:
            st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid #0E7490;">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 600;">⏱️ Execution Time: {elapsed}s | LLM: {selected_model} | Status: Workflow Completed</div>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;">
                <div style="font-size: 0.95rem; line-height: 1.6; color: #0F172A;">
                    {final_state['final_decision'].replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tab_ana:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("#### 📊 Academic Situation Analysis")
            st.write(final_state["analysis"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_rec:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Personalized Action Plan & Course Schedule")
            st.write(final_state["recommendations"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_val:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("#### ✅ Prerequisite & Policy Validation Result")
            st.write(final_state["validation"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_src:
            st.markdown("#### 📑 RAG Retrieved Catalog Policies (ChromaDB)")
            if final_state["retrieved_docs"]:
                for idx, d in enumerate(final_state["retrieved_docs"]):
                    src_n = d.metadata.get("source", "Catalog")
                    page_n = d.metadata.get("page", 1)
                    st.markdown(f"""
                    <div class="source-badge">
                        <b>Source {idx+1}:</b> {src_n} (Page {page_n})<br>
                        <i style="color: #475569;">"{d.page_content}"</i>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("General policy guidelines applied. No custom PDF chunks crossed the cutoff threshold.")

        # Save to Session History
        st.session_state["chat_history"].append({"query": query_input, "decision": final_state["final_decision"], "time": elapsed})

# ----------------- HISTORY & EXPORTS -----------------
if st.session_state["chat_history"]:
    st.markdown("---")
    st.markdown("### 📜 Advisement Decision History")
    
    h1, h2 = st.columns([1, 1])
    with h1:
        txt_out = "\n\n".join([f"Q: {item['query']}\nDecision:\n{item['decision']}" for item in st.session_state['chat_history']])
        st.download_button("📥 Export Advisement Report (TXT)", data=txt_out, file_name="academic_advisement_report.txt", mime="text/plain", use_container_width=True)
    with h2:
        st.download_button("📥 Export Decision History (JSON)", data=json.dumps(st.session_state['chat_history'], indent=2), file_name="advisement_history.json", mime="application/json", use_container_width=True)

    for idx, item in enumerate(reversed(st.session_state["chat_history"])):
        with st.expander(f"📋 Query {len(st.session_state['chat_history']) - idx}: {item['query']}"):
            st.markdown(item["decision"])
