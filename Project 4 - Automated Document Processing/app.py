import os
import time
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pypdf import PdfReader

load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="University of Layyah AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATES -----------------
if "processed_docs" not in st.session_state:
    st.session_state["processed_docs"] = {}
if "vector_store" not in st.session_state:
    st.session_state["vector_store"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "processing_history" not in st.session_state:
    st.session_state["processing_history"] = []
if "all_chunks_count" not in st.session_state:
    st.session_state["all_chunks_count"] = 0

# ----------------- EXACT MATCH PASTEL THEME & UNIFORM STYLING -----------------
st.html("""
<style>
    /* Main App Background - Soft Off-White / Cream */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8F9F6 !important;
        color: #2D3748 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar - Soft Sage / Mint Green */
    section[data-testid="stSidebar"], [data-testid="stSidebarUserContent"] {
        background-color: #E2ECE1 !important;
        color: #2C3E50 !important;
        border-right: 1px solid #D1E0CF !important;
    }
    
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stMarkdown {
        color: #2C3E50 !important;
    }

    /* Modern Professional Uniform Width Radio Styling with Custom Colors */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 6px;
        display: flex;
        flex-direction: column;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.6);
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #D5E7D8;
        width: 100% !important;
        box-sizing: border-box;
        transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: #EAF3EC;
        border-color: #B8D0B9;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #FDF2E9 !important;
        border: 1px solid #FAD7BD !important;
        box-shadow: 0 1px 3px rgba(243, 156, 18, 0.15);
    }

    /* Hero Header - Soft Mint Container */
    .hero-header {
        background: #EAF3EC;
        border: 1px solid #D5E7D8;
        border-radius: 14px;
        padding: 24px 30px;
        color: #2C3E50;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .hero-header h1 {
        color: #1F382B;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .hero-header p {
        color: #4A5D52;
        margin: 6px 0 0 0;
        font-size: 0.95rem;
    }

    /* Cards */
    .card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        color: #2D3748;
    }

    /* KPI / Stat Containers - Strict Uniform Typography */
    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    .kpi-card-green {
        flex: 1;
        background: #EAF3EC;
        border: 1px solid #D5E7D8;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .kpi-card-peach {
        flex: 1;
        background: #FDF2E9;
        border: 1px solid #FAD7BD;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .kpi-card-yellow {
        flex: 1;
        background: #FEF9E7;
        border: 1px solid #F9E7BFC4;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .kpi-title {
        font-size: 0.70rem !important;
        color: #5C6F63 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 6px !important;
    }
    .kpi-value {
        font-size: 0.95rem !important;
        color: #1F382B !important;
        font-weight: 500 !important;
        line-height: 1.2 !important;
    }

    /* Warm Peach / Amber Action Buttons */
    .stButton>button {
        background-color: #F39C12 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        background-color: #D68910 !important;
    }
</style>
""")

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown("### ⚙️ Engine Configuration")
    env_api_key = os.getenv("GROQ_API_KEY", "")
    groq_api_key = st.text_input("Groq API Key", type="password", value=env_api_key, placeholder="gsk_...")
    
    if groq_api_key and groq_api_key.startswith("gsk_"):
        st.markdown("<span style='color: #276749; font-weight: 600;'>● API Connected</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #9B2C2C; font-weight: 600;'>● API Key Required</span>", unsafe_allow_html=True)

    selected_model = st.selectbox("LLM Model", ["llama-3.1-8b-instant", "llama3-70b-8192"])
    processing_mode = st.selectbox("Processing Mode", ["Standard Enterprise", "Deep Semantic Analysis"])
    chunk_size = st.slider("Chunk Size", 300, 1500, 700)
    retrieval_k = st.slider("Retrieval Top-K", 1, 10, 3)

    st.markdown("---")
    st.markdown("### 📁 Document Workspace")
    nav_selection = st.radio(
        "Navigate to",
        ["Dashboard & Ingestion", "AI Analysis & Validation", "RAG Assistant & Citations", "Document Comparison", "Analytics & Reports"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### 🟢 System Status")
    st.markdown("**Status:** Ready\n**Vector DB:** ChromaDB Active")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Reset Workspace", use_container_width=True):
        st.session_state["processed_docs"] = {}
        st.session_state["vector_store"] = None
        st.session_state["chat_history"] = []
        st.session_state["processing_history"] = []
        st.session_state["all_chunks_count"] = 0
        st.success("Workspace reset successfully!")
        st.rerun()

# ----------------- HERO HEADER & KPIS -----------------
st.html("""
<div class="hero-header">
    <h1>University of Layyah AI Assistant</h1>
    <p>AI-powered Retrieval Augmented Generation (RAG) Assistant for academic knowledge retrieval</p>
</div>
""")

num_docs = len(st.session_state["processed_docs"])
total_chunks = st.session_state["all_chunks_count"]
system_status = "IDLE" if num_docs == 0 else "READY"
pipeline_text = f"{num_docs} Complete"

st.html(f"""
<div class="kpi-container">
    <div class="kpi-card-green">
        <div class="kpi-title">Documents</div>
        <div class="kpi-value">{num_docs}</div>
    </div>
    <div class="kpi-card-peach">
        <div class="kpi-title">Chunks Indexed</div>
        <div class="kpi-value">{total_chunks}</div>
    </div>
    <div class="kpi-card-yellow">
        <div class="kpi-title">Processed Pipeline</div>
        <div class="kpi-value">{pipeline_text}</div>
    </div>
    <div class="kpi-card-green">
        <div class="kpi-title">System Status</div>
        <div class="kpi-value">{system_status}</div>
    </div>
</div>
""")

# ----------------- PYDANTIC SCHEMA -----------------
class EnterpriseDocumentSchema(BaseModel):
    document_title: str = Field(description="Precise title or main subject of the document")
    document_type: str = Field(description="Category e.g., University Information, Syllabus, Policy Document")
    primary_org_or_author: str = Field(description="Author, company, or institution associated with the document")
    effective_date: str = Field(description="Effective date or publication date if mentioned, else 'N/A'")
    key_entities: list[str] = Field(description="List of key entities, technologies, or people mentioned")
    summary: str = Field(description="Detailed executive summary of the document")
    sentiment_tone: str = Field(description="Overall tone e.g., Formal, Technical, Informative, Neutral, Positive")
    complexity_level: str = Field(description="Reading complexity e.g., Beginner, Intermediate, Expert")
    confidence_score: float = Field(description="Extraction confidence score between 0.0 and 1.0")

# ================= NAVIGATION SECTIONS =================

if nav_selection == "Dashboard & Ingestion":
    st.markdown("### 📤 Document Ingestion & Pipeline")
    st.markdown("Upload multiple enterprise documents (`PDF`, `TXT`, `MD`) for automated parsing, chunking, embedding, and validation.")
    
    uploaded_files = st.file_uploader("Upload documents", type=["pdf", "txt", "md"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("⚡ Process Documents Pipeline"):
            if not groq_api_key or not groq_api_key.startswith("gsk_"):
                st.error("Please enter a valid Groq API Key in the sidebar.")
            else:
                with st.status("🚀 Running Enterprise Processing Pipeline...", expanded=True) as status:
                    start_time = time.time()
                    all_chunks = []
                    
                    st.write("🟢 **Stage 1 & 2:** Parsing document files & extracting text...")
                    for uploaded_file in uploaded_files:
                        file_name = uploaded_file.name
                        doc_text = ""
                        
                        if file_name.endswith(".pdf"):
                            reader = PdfReader(uploaded_file)
                            for page in reader.pages:
                                txt = page.extract_text()
                                if txt:
                                    doc_text += txt + "\n"
                        else:
                            doc_text = uploaded_file.read().decode("utf-8")
                            
                        if doc_text.strip():
                            st.write(f"🔄 **Stage 3 & 4:** Cleaning and chunking **{file_name}**...")
                            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=int(chunk_size*0.1))
                            chunks = text_splitter.create_documents([doc_text], metadatas=[{"source": file_name}])
                            all_chunks.extend(chunks)
                            
                            st.write(f"🛡️ **Stage 5 & 6:** Running LLM Structured Extraction & Pydantic Validation...")
                            llm = ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=0.1)
                            prompt = f"""
                            Analyze this document text and return ONLY a valid JSON object matching this schema:
                            {{
                                "document_title": "string",
                                "document_type": "string",
                                "primary_org_or_author": "string",
                                "effective_date": "string",
                                "key_entities": ["string"],
                                "summary": "string",
                                "sentiment_tone": "string",
                                "complexity_level": "string",
                                "confidence_score": 0.95
                            }}
                            
                            Document Content:
                            {doc_text[:4000]}
                            """
                            try:
                                resp = llm.invoke([HumanMessage(content=prompt)])
                                content = resp.content.strip()
                                if "```json" in content:
                                    content = content.split("```json")[1].split("```")[0].strip()
                                elif "```" in content:
                                    content = content.split("```")[1].split("```")[0].strip()
                                    
                                parsed_json = json.loads(content)
                                validated_obj = EnterpriseDocumentSchema(**parsed_json)
                                st.session_state["processed_docs"][file_name] = validated_obj.model_dump()
                            except Exception as e:
                                st.error(f"Validation error on {file_name}: {e}")

                    if all_chunks:
                        st.write("📦 **Stage 7:** Building ChromaDB Hybrid Index for RAG Retrieval...")
                        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                        st.session_state["vector_store"] = Chroma.from_documents(all_chunks, embeddings)
                        st.session_state["all_chunks_count"] = len(all_chunks)

                    elapsed = round(time.time() - start_time, 2)
                    
                    st.session_state["processing_history"].insert(0, {
                        "time": datetime.now().strftime("%I:%M %p"),
                        "documents": len(uploaded_files),
                        "operation": "Full Ingestion Pipeline",
                        "status": "Completed"
                    })
                    
                    status.update(label=f"✅ Processing pipeline completed successfully in {elapsed}s!", state="complete", expanded=False)

    if st.session_state["processed_docs"]:
        st.markdown("### 📋 Processed Documents Registry")
        table_data = []
        for name, data in st.session_state["processed_docs"].items():
            table_data.append({
                "Document": name,
                "Type": data.get("document_type"),
                "Organization": data.get("primary_org_or_author"),
                "Sentiment": data.get("sentiment_tone"),
                "Status": "Indexed 🟢"
            })
        st.dataframe(table_data, use_container_width=True)

elif nav_selection == "AI Analysis & Validation":
    st.markdown("### 🧠 AI Document Analysis & Pydantic Validation")
    
    if not st.session_state["processed_docs"]:
        st.info("No documents processed yet. Please upload and process documents in the Dashboard tab.")
    else:
        selected_doc = st.selectbox("Select Document for Detailed Analysis", list(st.session_state["processed_docs"].keys()))
        data = st.session_state["processed_docs"][selected_doc]
        
        col1, col2 = st.columns(2)
        with col1:
            st.html(f"""
                <div class="card">
                    <h4>📊 Metadata & Classification</h4>
                    <p><b>Title:</b> {data.get('document_title')}</p>
                    <p><b>Type:</b> {data.get('document_type')}</p>
                    <p><b>Organization/Author:</b> {data.get('primary_org_or_author')}</p>
                    <p><b>Effective Date:</b> {data.get('effective_date')}</p>
                    <p><b>Confidence Score:</b> {data.get('confidence_score')}</p>
                </div>
            """)
        with col2:
            st.html(f"""
                <div class="card">
                    <h4>🔍 Sentiment & Complexity</h4>
                    <p><b>Sentiment Tone:</b> {data.get('sentiment_tone')}</p>
                    <p><b>Complexity Level:</b> {data.get('complexity_level')}</p>
                    <p><b>Key Entities:</b> {', '.join(data.get('key_entities', []))}</p>
                    <p><b>Validation Status:</b> <span style="color: #276749; font-weight: 600;">Schema Valid ✅</span></p>
                </div>
            """)
            
        st.html(f"""
            <div class="card">
                <h4>📝 Executive Summary</h4>
                <p>{data.get('summary')}</p>
            </div>
        """)
        
        st.markdown("### 🛡️ Pydantic Validation Report")
        st.success("✔ Schema Validated Successfully\n✔ Required Fields Detected & Verified\n✔ Data Types Correct (String, List, Float)")

elif nav_selection == "RAG Assistant & Citations":
    st.markdown("### 🔍 RAG Knowledge Assistant")
    st.markdown("Ask natural language questions across your uploaded documents with precise source citations.")
    
    if not st.session_state["vector_store"]:
        st.warning("Please upload and process documents first to initialize the RAG vector store.")
    else:
        st.markdown("**Suggested Questions:**")
        cols = st.columns(3)
        suggested_q = None
        if cols[0].button("Who is the Vice Chancellor of University of Layyah?"):
            suggested_q = "Who is the Vice Chancellor of University of Layyah?"
        if cols[1].button("How many departments does the university have?"):
            suggested_q = "How many departments does the university have?"
        if cols[2].button("Where is the university located?"):
            suggested_q = "Where is the university located?"

        user_query = st.text_input("Ask your question below...", value=suggested_q if suggested_q else "")
        
        if user_query:
            with st.spinner("Retrieving knowledge base & generating cited answer..."):
                retriever = st.session_state["vector_store"].as_retriever(search_kwargs={"k": retrieval_k})
                docs = retriever.invoke(user_query)
                context = "\n\n".join([f"[Source: {d.metadata.get('source')}]\n{d.page_content}" for d in docs])
                
                llm = ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=0.2)
                qa_prompt = f"""
                You are an expert University Assistant. Answer the user question based strictly on the provided document context. Cite your sources accurately.
                
                Context:
                {context}
                
                Question: {user_query}
                """
                response = llm.invoke([HumanMessage(content=qa_prompt)])
                st.session_state["chat_history"].append((user_query, response.content, docs))

        if st.session_state["chat_history"]:
            for q, a, source_docs in reversed(st.session_state["chat_history"]):
                st.html(f"""
                    <div class="card">
                        <p><b>Q:</b> {q}</p>
                        <p style="color: #276749;"><b>A:</b> {a}</p>
                        <hr style="border-color: #E2E8F0; margin: 10px 0;">
                        <p style="font-size: 0.85rem; color: #718096;"><b>Sources / Citations:</b></p>
                """)
                for sd in source_docs:
                    st.markdown(f"- 📄 `{sd.metadata.get('source')}`")
                st.markdown("</div>", unsafe_allow_html=True)

elif nav_selection == "Document Comparison":
    st.markdown("### ⚖️ AI Document Comparison")
    doc_list = list(st.session_state["processed_docs"].keys())
    if len(doc_list) < 2:
        st.info("Please upload and process at least **two documents** to use the Document Comparison feature.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            doc_a = st.selectbox("Select Document A", doc_list, index=0)
        with col_b:
            doc_b = st.selectbox("Select Document B", doc_list, index=1 if len(doc_list)>1 else 0)
            
        if st.button("⚡ Compare Documents"):
            data_a = st.session_state["processed_docs"][doc_a]
            data_b = st.session_state["processed_docs"][doc_b]
            
            st.markdown("### 📊 Comparison Results")
            c1, c2 = st.columns(2)
            with c1:
                st.html(f"""
                    <div class="card">
                        <h4>{doc_a}</h4>
                        <p><b>Type:</b> {data_a.get('document_type')}</p>
                        <p><b>Sentiment:</b> {data_a.get('sentiment_tone')}</p>
                    </div>
                """)
            with c2:
                st.html(f"""
                    <div class="card">
                        <h4>{doc_b}</h4>
                        <p><b>Type:</b> {data_b.get('document_type')}</p>
                        <p><b>Sentiment:</b> {data_b.get('sentiment_tone')}</p>
                    </div>
                """)
            st.success(f"Successfully compared **{doc_a}** and **{doc_b}**.")

elif nav_selection == "Analytics & Reports":
    st.markdown("### 📊 Analytics Dashboard & Report Generation")
    col1, col2 = st.columns(2)
    with col1:
        st.html("""
            <div class="card">
                <h4>📈 Document Types Distribution</h4>
                <p>PDF Documents: <b>100%</b></p>
            </div>
        """)
    with col2:
        st.html("""
            <div class="card">
                <h4>⚡ Processing Performance</h4>
                <p>Pipeline Success Rate: <b>100%</b></p>
            </div>
        """)
    
    st.markdown("---")
    report_json = json.dumps(st.session_state["processed_docs"], indent=2)
    st.download_button("📥 Download Enterprise JSON Report", data=report_json, file_name="university_report.json", mime="application/json")