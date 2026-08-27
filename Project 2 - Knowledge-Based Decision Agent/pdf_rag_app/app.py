import os
import time
import json
import tempfile
import gc
import shutil
import base64
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# ----------------- PATH & PAGE CONFIG -----------------
CHROMA_PATH = "./chroma_db"

st.set_page_config(
    page_title="University of Layyah AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- EMBEDDINGS CACHING -----------------
@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = get_embeddings()

# ----------------- SESSION STATES -----------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "doc_count" not in st.session_state:
    st.session_state["doc_count"] = 0
if "chunk_count" not in st.session_state:
    st.session_state["chunk_count"] = 0
if "uploaded_doc_list" not in st.session_state:
    st.session_state["uploaded_doc_list"] = []
if "last_response_time" not in st.session_state:
    st.session_state["last_response_time"] = 0.0

# Persistent Vector DB Check
if "vector_store" not in st.session_state:
    if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
        try:
            st.session_state["vector_store"] = Chroma(
                persist_directory=CHROMA_PATH, 
                embedding_function=embeddings
            )
        except Exception:
            st.session_state["vector_store"] = None
    else:
        st.session_state["vector_store"] = None

# ----------------- OFFICIAL LOGO MATCHED THEME CSS -----------------
st.html("""
<style>
    /* Global Screen & Sidebar Theme (Charcoal & Warm White Background) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    section[data-testid="stSidebar"], [data-testid="stSidebarUserContent"] {
        background-color: #FBFBFB !important;
        color: #222222 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar Border & Styling */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #E5E5E5 !important;
        background-color: #F4F4F5 !important;
    }

    /* Sidebar Expander Custom Styling */
    div[data-testid="stSidebar"] .streamlit-expanderHeader {
        background: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #E0E0E0 !important;
        color: #222222 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stSidebar"] .streamlit-expanderContent {
        background: #FFFFFF !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid #E0E0E0 !important;
        border-top: none !important;
    }

    /* Hero Banner Header (Logo Orange & Charcoal) */
    .hero-header {
        background: linear-gradient(135deg, #FF9933 0%, #E67E22 100%) !important;
        border-radius: 14px !important;
        padding: 22px 26px !important;
        color: #FFFFFF !important;
        margin-bottom: 18px !important;
        border: 1px solid #D35400 !important;
        box-shadow: 0 6px 20px -4px rgba(230, 126, 34, 0.25) !important;
    }
    .hero-header h1 {
        color: #FFFFFF !important;
        margin: 0 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    .hero-header p {
        color: #FFF5EC !important;
        margin: 4px 0 0 0 !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
    }

    /* Section Headings */
    .section-title {
        color: #222222;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        margin-bottom: 10px !important;
        margin-top: 20px !important;
    }

    /* Workflow Info Banner */
    .workflow-banner {
        background: #FFF3E0 !important;
        border-radius: 10px !important;
        padding: 12px 18px !important;
        margin-bottom: 18px !important;
        font-size: 0.85rem !important;
        color: #B26500 !important;
        font-weight: 500 !important;
        border: 1px solid #FFE0B2 !important;
    }

    /* Compact & Balanced Stat Cards */
    .stat-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }
    .stat-card:hover {
        transform: translateY(-2px) !important;
        border-color: #FF9933 !important;
    }
    
    .stat-num {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #222222 !important;
        margin-top: 2px !important;
    }
    
    .stat-label {
        font-size: 0.62rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.4px !important;
        color: #1E8449 !important;
    }

    /* Suggested Box Header */
    .suggested-box {
        background: #FFF8F0 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        border: 1px solid #FFE0B2 !important;
    }
    .suggested-box h4 {
        color: #222222 !important;
        margin: 0 0 2px 0 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    /* Main CTA Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #FF9933 0%, #E67E22 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 8px 18px !important;
        box-shadow: 0 3px 10px rgba(230, 126, 34, 0.25) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #E67E22 100%, #D35400 100%) !important;
    }

    /* Preset Chip Buttons */
    div[data-testid="column"] .stButton>button {
        background: #FFFFFF !important;
        color: #222222 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 18px !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
    }
    div[data-testid="column"] .stButton>button:hover {
        background: #FFF3E0 !important;
        border-color: #FF9933 !important;
    }

    /* Unified Styled Containers for Lower Sections */
    .content-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
    }

    /* Source Cards */
    .source-card {
        background: #FAFAFA !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        margin-top: 8px !important;
        font-size: 0.82rem !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 3px solid #1E8449 !important;
    }

    /* Status Badges */
    .status-badge-ready {
        background-color: #E8F8F5 !important;
        color: #117A65 !important;
        padding: 3px 10px !important;
        border-radius: 16px !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
    }
    .status-badge-waiting {
        background-color: #FEF9E7 !important;
        color: #B7950B !important;
        padding: 3px 10px !important;
        border-radius: 16px !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
    }
</style>
""")

# ----------------- SIDEBAR -----------------
with st.sidebar:
    # Automatically load 'logo.png' from project folder
    logo_filename = "logo.png"
    logo_base64 = ""
    
    if os.path.exists(logo_filename):
        with open(logo_filename, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode("utf-8")

    if logo_base64:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 12px; background: white; padding: 0px; border-radius: 10px; border: 1px solid #E0E0E0; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                <img src="data:image/png;base64,{logo_base64}" style="width: 100%; height: 105px; object-fit: fill; display: block;">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="text-align: center; background: white; padding: 22px; border-radius: 10px; border: 1px solid #E0E0E0; margin-bottom: 12px;">
                <h4 style="color: #FF9933; margin:0; font-size: 0.9rem;">University of Layyah</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.expander("ℹ️ **System Specs**", expanded=False):
        st.write("Advanced RAG Architecture with persistent Chroma VectorDB, conversational memory, and ChatGroq LLMs.")

    with st.expander("⚙️ **Engine Settings**", expanded=True):
        env_api_key = os.getenv("GROQ_API_KEY", "")
        groq_api_key = st.text_input("Groq API Key", type="password", value=env_api_key, placeholder="gsk_...")
        selected_model = st.selectbox("Model Engine", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile", "llama3-70b-8192"])
        top_k = st.slider("Top-K Chunks", min_value=1, max_value=8, value=3)
        similarity_threshold = st.slider("Match Cutoff Score", min_value=0.0, max_value=0.8, value=0.2, step=0.05)

    with st.expander("📊 **Live Database Status**", expanded=True):
        if st.session_state["vector_store"] is not None:
            st.html('<span class="status-badge-ready">● PERSISTED & ACTIVE</span>')
        else:
            st.html('<span class="status-badge-waiting">IDLE / STANDBY</span>')

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔥 Reset Engine & Memory", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state["doc_count"] = 0
        st.session_state["chunk_count"] = 0
        st.session_state["uploaded_doc_list"] = []
        st.session_state["last_response_time"] = 0.0
        
        if "vector_store" in st.session_state:
            st.session_state["vector_store"] = None
        
        gc.collect()
        
        if os.path.exists(CHROMA_PATH):
            try:
                shutil.rmtree(CHROMA_PATH)
            except Exception:
                time.sleep(0.5)
                try:
                    shutil.rmtree(CHROMA_PATH)
                except Exception:
                    pass
            
        st.success("Engine & memory reset successfully!")
        st.rerun()

# ----------------- HERO BANNER -----------------
st.html("""
<div class="hero-header">
    <h1>🎓 University of Layyah AI Engine</h1>
    <p>Retrieval-Augmented Intelligence System for Campus Knowledge Base</p>
</div>
""")

# ----------------- WORKFLOW BANNER -----------------
st.html("""
<div class="workflow-banner">
    💡 <b>Smart Workflow:</b> Upload University documents once -> Persistent DB saves them automatically -> Ask multi-turn questions seamlessly!
</div>
""")

# ----------------- SYSTEM OVERVIEW -----------------
st.html('<div class="section-title">📊 Real-Time Analytics</div>')

sc1, sc2, sc3 = st.columns(3)

with sc1:
    st.html(f"""
    <div class="stat-card">
        <div class="stat-label">📄 Document Count</div>
        <div class="stat-num">{st.session_state['doc_count']} Loaded</div>
    </div>
    """)

with sc2:
    st.html(f"""
    <div class="stat-card">
        <div class="stat-label">🧩 Indexed Chunks</div>
        <div class="stat-num">{st.session_state['chunk_count']} Vectors</div>
    </div>
    """)

with sc3:
    status_str = "Active (Disk)" if st.session_state["vector_store"] else "Ready"
    st.html(f"""
    <div class="stat-card">
        <div class="stat-label">⚡ Database Engine</div>
        <div class="stat-num">{status_str}</div>
    </div>
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- INGESTION EXPANDER -----------------
with st.expander("📂 **1. Knowledge Base Manager (PDF Persistent Ingestion)**", expanded=(st.session_state["vector_store"] is None)):
    uploaded_files = st.file_uploader(
        "Upload University PDF documents to build/update the knowledge base", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    
    if st.button("🚀 Process & Index Documents"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF file.")
        else:
            with st.spinner("Indexing & saving vectors to persistent storage..."):
                documents = []
                doc_summary_list = []
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

                for file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(file.read())
                        tmp_path = tmp_file.name

                    loader = PyPDFLoader(tmp_path)
                    docs = loader.load()
                    
                    for d in docs:
                        d.metadata["source"] = file.name
                        
                    file_chunks = text_splitter.split_documents(docs)
                    documents.extend(docs)
                    
                    doc_summary_list.append({
                        "Document Name": file.name,
                        "Pages": len(docs),
                        "Chunks": len(file_chunks),
                        "Status": "Persisted"
                    })
                    os.remove(tmp_path)

                all_chunks = text_splitter.split_documents(documents)
                
                vector_store = Chroma.from_documents(
                    documents=all_chunks, 
                    embedding=embeddings, 
                    persist_directory=CHROMA_PATH
                )

                st.session_state["vector_store"] = vector_store
                st.session_state["doc_count"] = len(uploaded_files)
                st.session_state["chunk_count"] = len(all_chunks)
                st.session_state["uploaded_doc_list"] = doc_summary_list
                
                st.success("🎉 Knowledge Base updated and saved to persistent disk!")
                st.rerun()

    if st.session_state["uploaded_doc_list"]:
        st.markdown("#### 📋 Indexed Knowledge Summary")
        st.dataframe(st.session_state["uploaded_doc_list"], use_container_width=True, hide_index=True)

# ----------------- PRESET CHIPS & INPUT -----------------
st.html("""
<div class="suggested-box">
    <h4>💡 Quick Access Prompts</h4>
    <p style="font-size: 0.82rem; color: #555555; margin-top: -2px; margin-bottom: 6px;">Click any pill below to instantly test the system:</p>
</div>
""")

col_p1, col_p2 = st.columns(2)
preset_input = None
if col_p1.button("📌 Who is the Vice Chancellor of University of Layyah?", use_container_width=True):
    preset_input = "Who is the Vice Chancellor of the University of Layyah?"
if col_p2.button("📌 How many departments does University of Layyah have?", use_container_width=True):
    preset_input = "How many departments does the University of Layyah have?"

col_p3, col_p4 = st.columns(2)
if col_p3.button("📌 What are the contact details for general inquiries?", use_container_width=True):
    preset_input = "What are the primary contact details for general inquiries?"
if col_p4.button("📌 Where is University of Layyah located?", use_container_width=True):
    preset_input = "Where is the University of Layyah located?"

st.markdown("<br>", unsafe_allow_html=True)

# Seamless Interactive Query Studio Card
st.html("""
<div class="content-card" style="margin-top: 0px !important;">
    <div class="section-title" style="margin-top: 0px !important; margin-bottom: 12px !important;">💬 Interactive Query Studio</div>
</div>
""")

with st.container():
    st.html('<div class="content-card" style="margin-top: -10px !important;">')
    user_query = st.text_input(
        "Query Prompt", 
        value=preset_input if preset_input else "",
        placeholder="Ask anything about University of Layyah...",
        label_visibility="collapsed"
    )
    search_clicked = st.button("🔍 Execute RAG Search")
    st.html('</div>')

def format_docs(docs):
    return "\n\n".join(f"[Source: {d.metadata.get('source', 'Doc')}] {d.page_content}" for d in docs)

# ----------------- RAG EXECUTION -----------------
if search_clicked or preset_input:
    if not st.session_state["vector_store"]:
        st.error("Knowledge base is empty! Please upload PDF documents first.")
    elif not user_query.strip():
        st.warning("Please enter a question.")
    elif not groq_api_key or not groq_api_key.startswith("gsk_"):
        st.error("🔑 Invalid Groq API Key! Please check sidebar inputs.")
    else:
        with st.spinner("⚡ Running vector search & generating LLM response..."):
            try:
                start_time = time.time()
                
                retriever = st.session_state["vector_store"].as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={"k": top_k, "score_threshold": similarity_threshold}
                )
                
                llm = ChatGroq(groq_api_key=groq_api_key, model_name=selected_model, temperature=0.1)

                source_docs = retriever.invoke(user_query)

                system_prompt = (
                    "You are a professional assistant for the University of Layyah. "
                    "Use the provided context and conversation history to answer accurately using clear bullet points. "
                    "If the answer isn't in context, explicitly state that facts are not present in uploaded documents.\n\n"
                    "Context:\n{context}"
                )
                
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{question}")
                ])

                formatted_context = format_docs(source_docs) if source_docs else "No relevant context found."

                chain = qa_prompt | llm | StrOutputParser()

                answer = chain.invoke({
                    "context": formatted_context,
                    "chat_history": st.session_state["chat_history"],
                    "question": user_query
                })

                elapsed_time = round(time.time() - start_time, 2)
                st.session_state["last_response_time"] = elapsed_time

                st.session_state["chat_history"].append(HumanMessage(content=user_query))
                st.session_state["chat_history"].append(AIMessage(content=answer))

                # AI Output Box with Unified Container Styling
                st.html('<div class="section-title">💡 Generated Insight</div>')
                st.html(f"""
                <div class="content-card" style="border-left: 4px solid #FF9933 !important;">
                    <span style="font-size: 0.82rem; color: #7F8C8D; font-weight: 600;">⏱️ Response Latency: {elapsed_time}s | LLM: {selected_model}</span>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;">
                    <div style="color: #222222; font-size: 0.95rem; line-height: 1.5;">{answer.replace(chr(10), '<br>')}</div>
                </div>
                """)

                # Citations
                st.html('<div class="section-title">📑 Context Sources</div>')
                if source_docs:
                    src_cols = st.columns(min(len(source_docs), 3))
                    for idx, doc in enumerate(source_docs):
                        page_num = doc.metadata.get("page", 0) + 1
                        source_name = doc.metadata.get("source", "Document.pdf")
                        snippet = doc.page_content[:150].replace("\n", " ") + "..."
                        
                        with src_cols[idx % 3]:
                            st.html(f"""
                            <div class="source-card">
                                <b>Source {idx+1}:</b> {source_name}<br>
                                <span style="color:#1E8449; font-weight:600;">Page: {page_num}</span>
                                <hr style="margin: 5px 0; border: none; border-top: 1px solid #E2E8F0;">
                                <i style="color:#666666;">"{snippet}"</i>
                            </div>
                            """)
                else:
                    st.warning("⚠️ No document chunks crossed the match threshold. Generating based on conversational context.")

            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

# ----------------- HISTORY & EXPORT -----------------
if st.session_state["chat_history"]:
    st.markdown("---")
    h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
    
    with h_col1:
        st.html('<div class="section-title">📜 Conversation History</div>')
        
    with h_col2:
        chat_txt = "\n\n".join([f"Q: {st.session_state['chat_history'][i].content}\nA: {st.session_state['chat_history'][i+1].content}" for i in range(0, len(st.session_state["chat_history"]), 2)])
        st.download_button(
            label="📥 Export TXT",
            data=chat_txt,
            file_name="rag_chat_log.txt",
            mime="text/plain",
            use_container_width=True
        )

    with h_col3:
        json_data = []
        for i in range(0, len(st.session_state["chat_history"]), 2):
            json_data.append({
                "question": st.session_state["chat_history"][i].content,
                "answer": st.session_state["chat_history"][i+1].content
            })
        st.download_button(
            label="📥 Export JSON",
            data=json.dumps(json_data, indent=2),
            file_name="rag_chat_log.json",
            mime="application/json",
            use_container_width=True
        )

    for i in range(0, len(st.session_state["chat_history"]), 2):
        usr_msg = st.session_state["chat_history"][i].content
        ai_msg = st.session_state["chat_history"][i+1].content if i+1 < len(st.session_state["chat_history"]) else ""
        
        with st.expander(f"❓ {usr_msg}"):
            st.write(ai_msg)