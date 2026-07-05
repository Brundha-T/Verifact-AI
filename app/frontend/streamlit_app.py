import streamlit as st
import requests
import json
import os
# Add backend path for configuration import
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from config import settings
import re
import time

# =========================================
# PAGE CONFIGURATION
# =========================================
st.set_page_config(
    page_title="VeriFact AI Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# BACKEND API CONFIG
# =========================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# =========================================
# PREMIUM CSS STYLING INJECTION (AESTHETICS WOW FACTOR)
# =========================================
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .glass-card:hover {
        border-color: rgba(0, 204, 153, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 204, 153, 0.08) !important;
    }
    
    /* Sticky Navigation */
    .sticky-nav {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(0,0,0,0.7);
        padding: 8px 0;
        display: flex;
        justify-content: center;
        gap: 24px;
        z-index: 1000;
        backdrop-filter: blur(8px);
    }
    .sticky-nav a {
    color: #00cc99;
    text-decoration: none;
    font-weight: 500;
}
.sticky-nav a:hover {
    color: #fff;
}
/* Smooth scrolling */
html {
    scroll-behavior: smooth;
}
    /* Spacer to avoid content hidden under fixed nav */
    .nav-spacer {
        height: 80px;
    }
    /* Offset for anchor navigation to account for fixed header */
    [id] {
        scroll-margin-top: 100px;
    }

    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        text-align: center !important;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Premium Chat Bubbles */
    .chat-bubble-user {
        background: linear-gradient(135deg, #00b4db, #0083b0) !important;
        color: white !important;
        border-radius: 16px 16px 4px 16px !important;
        padding: 14px 18px !important;
        margin: 10px 0 10px auto !important;
        max-width: 75% !important;
        width: fit-content !important;
        box-shadow: 0 4px 15px rgba(0, 180, 219, 0.2) !important;
        animation: slideInRight 0.3s ease-out;
    }
    .chat-bubble-ai {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #e2e8f0 !important;
        border-radius: 16px 16px 16px 4px !important;
        padding: 16px 20px !important;
        margin: 10px auto 10px 0 !important;
        max-width: 80% !important;
        width: fit-content !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        animation: slideInLeft 0.3s ease-out;
    }
    
    /* Citation tags */
    .citation-tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 204, 153, 0.15) !important;
        color: #00cc99 !important;
        border: 1px solid rgba(0, 204, 153, 0.3) !important;
        border-radius: 6px !important;
        padding: 1px 6px !important;
        font-size: 0.78em !important;
        font-weight: 600 !important;
        margin: 0 3px !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
        text-decoration: none !important;
    }
    .citation-tag:hover {
        background: #00cc99 !important;
        color: #121212 !important;
    }
    
    /* Semantic highlighting */
    .semantic-highlight-verified {
        background: rgba(0, 204, 153, 0.15) !important;
        border-bottom: 2px solid #00cc99 !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
    }
    .semantic-highlight-mostly {
        background: rgba(243, 156, 18, 0.15) !important;
        border-bottom: 2px solid #f39c12 !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
    }
    .semantic-highlight-hallucinated {
        background: rgba(231, 76, 60, 0.18) !important;
        border-bottom: 2px solid #e74c3c !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
    }
    
    /* Latency Waterfall Bar */
    .waterfall-bar {
        height: 24px;
        border-radius: 6px;
        display: inline-block;
        margin-right: 10px;
    }
    
    /* Animations */
    @keyframes slideInRight {
        from { transform: translateX(30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideInLeft {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Responsive custom spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 204, 153, 0.1) !important;
        border-color: rgba(0, 204, 153, 0.3) !important;
        color: #00cc99 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================================
# SESSION STATE INITIALIZATION
# =========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_query_result" not in st.session_state:
    st.session_state.last_query_result = None

if "document_registry" not in st.session_state:
    st.session_state.document_registry = []

# =========================================
# REFRESH DOCUMENTS HELPER
# =========================================
def refresh_documents():
    """Fetches the updated document list from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/documents", timeout=10)
        if response.status_code == 200:
            st.session_state.document_registry = response.json()
        else:
            st.session_state.document_registry = []
    except Exception as e:
        logger_err = f"API connection error: {e}"
        st.session_state.document_registry = []

# Initial pull of document list
if not st.session_state.document_registry:
    refresh_documents()

# =========================================
# SIDEBAR NAVIGATION & QUICK ACTIONS
# =========================================
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=70)
    st.title("VeriFact AI")
    st.caption("Automated Hallucination Detection & Observability")
    
    st.markdown("---")
    
    # RAG Stats Widget
    st.subheader("System Status")
    
    total_docs = len(st.session_state.document_registry)
    if total_docs > 0:
        st.success(f"🟢 Database Ready ({total_docs} File(s))")
    else:
        st.warning("🟡 Database Empty (Upload document)")
        
    st.info(
        """
        **LLM Engine:** Ollama / `phi3`
        **NLI Model:** DeBERTa-v3
        **Vector Store:** ChromaDB
        """
    )
    
    st.markdown("---")
    
    # Fast Reset Action
    st.subheader("Quick Control Panel")
    if st.button("🗑 Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_query_result = None
        st.success("Chat history cleared.")
        st.rerun()
        
    if st.button("🚨 Factory Reset System", use_container_width=True, type="primary"):
        with st.spinner("Wiping DB and Registry..."):
            try:
                res = requests.post(f"{BACKEND_URL}/reset", timeout=15)
                if res.status_code == 200:
                    st.session_state.chat_history = []
                    st.session_state.last_query_result = None
                    refresh_documents()
                    st.success("System completely factory reset!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Wipe failed.")
            except Exception as e:
                st.error(f"Error resetting: {e}")

# =========================================
# MAIN DASHBOARD PANELS (TABBED VIEW)
# =========================================
st.markdown("""
<div class='sticky-nav'>
    <a href='#qa'>💬 QA Dashboard</a>
    <a href='#trace'>🔬 Trace</a>
    <a href='#analytics'>📊 Analytics</a>
    <a href='#docs'>📁 Documents</a>
</div>
<div class='nav-spacer'></div>
""", unsafe_allow_html=True)

# Tabs for the main sections
tab_chat, tab_obs, tab_metrics, tab_docs = st.tabs([
    "💬 Interactive QA Studio",
    "🔬 Observability Trace",
    "📊 Observability Analytics",
    "📁 Document Registry"
])

# =========================================
# TAB 1: INTERACTIVE CHAT STUDIO
# =========================================
with tab_chat:
    st.markdown("<div id='qa'></div>", unsafe_allow_html=True)
    st.markdown("<h3>💬 Conversational RAG Sandbox</h3>", unsafe_allow_html=True)
    st.caption("Ask questions grounded exclusively on your indexed document corpus with full citation mapping.")
    
    # 1. Display Chat scrolling history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown(
                """
                <div style="text-align: center; opacity: 0.4; padding: 60px 0;">
                    <img src="https://img.icons8.com/nolan/96/chat.png" style="width: 60px; margin-bottom: 15px;"/>
                    <h4>No conversation exchanges yet.</h4>
                    <p>Indexed documents inside the Document Registry and ask a question below!</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for exchange in st.session_state.chat_history:
                # User Bubble
                st.markdown(
                    f'<div class="chat-bubble-user">{exchange["question"]}</div>',
                    unsafe_allow_html=True
                )
                
                # Assistant Bubble with Citation parsing
                answer_html = exchange["answer"]
                
                # Render citation annotations nicely in HTML
                # Find brackets e.g. [1] and replace with interactive citation tags
                answer_html = re.sub(
                    r"\[(\d+)\]",
                    r'<a href="#chunk_\1" class="citation-tag">[\1]</a>',
                    answer_html
                )
                
                st.markdown(
                    f'<div class="chat-bubble-ai">🤖 <b>VeriFact AI:</b><br/>{answer_html}</div>',
                    unsafe_allow_html=True
                )
                
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # 2. Input Box & Send
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([6, 1])
        with col_input:
            user_question = st.text_input(
                "Ask a question from your documents...",
                placeholder="What is the main finding in the document?",
                label_visibility="collapsed"
            )
        with col_btn:
            submit_btn = st.form_submit_button("Send 🚀", use_container_width=True)
            
    if submit_btn and user_question.strip():
        if total_docs == 0:
            st.error("No documents loaded! Please go to the **📁 Document Registry** tab and upload documents first.")
        else:
            with st.spinner("🔍 Retrieving context, synthesizing grounded answer & running NLI claim verification..."):
                try:
                    # Collect history inside state format
                    payload_history = []
                    for h in st.session_state.chat_history[-3:]:  # Sliding window of last 3 turns
                        payload_history.append({
                            "question": h["question"],
                            "answer": h["answer"]
                        })
                        
                    payload = {
                        "question": user_question,
                        "history": payload_history
                    }
                    
                    # Send request to backend with streaming enabled
                    response = requests.post(
                        f"{BACKEND_URL}/ask",
                        json=payload,
                        stream=True,
                        timeout=300,
                    )

                    if response.status_code == 200:
                        # Initialize placeholders for progressive display
                        answer = ""
                        verification = {}
                        trace = {}
                        retrieved_chunks = []
                        answer_placeholder = st.empty()

                        # Iterate over streaming JSON lines from the backend
                        for raw_line in response.iter_lines():
                            if not raw_line:
                                continue
                            try:
                                data = json.loads(raw_line.decode())
                            except Exception:
                                continue
                            d_type = data.get("type")
                            if d_type == "token":
                                token = data.get("content", "")
                                answer += token
                                # Update the AI bubble with the current partial answer
                                answer_placeholder.markdown(
                                    f"<div class='chat-bubble-ai'>🤖 <b>VeriFact AI:</b><br/>{answer}</div>",
                                    unsafe_allow_html=True,
                                )
                            elif d_type == "verification":
                                verification = data.get("verification", {})
                            elif d_type == "trace":
                                trace = data.get("trace", {})
                            elif d_type == "chunks":
                                retrieved_chunks = data.get("retrieved_chunks", [])

                        # Store the final result in session state
                        st.session_state.last_query_result = {
                            "answer": answer,
                            "verification": verification,
                            "trace": trace,
                            "retrieved_chunks": retrieved_chunks,
                        }

                        # Append to chat history and refresh UI
                        st.session_state.chat_history.append({
                            "question": user_question,
                            "answer": answer,
                        })
                        st.rerun()
                    else:
                        st.error(f"Error from backend API: {response.text}")
                except Exception as e:
                    st.error(f"API Execution Error: {e}")
                    
    # Export Conversation Feature
    if st.session_state.chat_history:
        st.markdown("<br/>", unsafe_allow_html=True)
        # Create markdown download
        md_content = "# VeriFact AI - Grounded Chat Report\n\n"
        for i, h in enumerate(st.session_state.chat_history):
            md_content += f"### Exchange {i+1}\n"
            md_content += f"**User Question:** {h['question']}\n\n"
            md_content += f"**AI Answer:** {h['answer']}\n\n"
            md_content += "---\n\n"
            
        st.download_button(
            label="📥 Export Chat Log (Markdown)",
            data=md_content,
            file_name=f"verifact_chat_report_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=False
        )

# =========================================
# TAB 2: OBSERVABILITY STUDIO & TRACE
# =========================================
with tab_obs:
    st.markdown("<div id='trace'></div>", unsafe_allow_html=True)
    st.markdown("<h3>🔬 Deep Observability & Verification Trace</h3>", unsafe_allow_html=True)
    st.caption("Detailed RAG Pipeline Latency waterfall, document citation mappings, and claim-level NLI verification highlights.")
    
    result = st.session_state.last_query_result
    
    if not result:
        st.markdown(
            """
            <div style="text-align: center; opacity: 0.4; padding: 80px 0;">
                <img src="https://img.icons8.com/nolan/96/workflow.png" style="width: 60px; margin-bottom: 15px;"/>
                <h4>No Observability Traces loaded.</h4>
                <p>Submit a question in the chat sandbox to map its detailed pipeline trace here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        trace = result.get("trace", {})
        verification = result.get("verification", {})
        retrieved_chunks = result.get("retrieved_chunks", [])
        
        # Grid layout for summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "Faithfulness Score",
                f"{verification.get('faithfulness_score', 0.0) * 100:.0f}%",
                help="Proportion of claims in AI generated answer strictly supported by context."
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "NLI Average Confidence",
                f"{verification.get('average_confidence', 0.0) * 100:.0f}%",
                help="Mean confidence probability score returned by DeBERTa-v3 NLI model."
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "Pipeline Execution Latency",
                f"{trace.get('total_ms', 0.0) / 1000:.2f}s",
                help="Total time taken to complete embedding, retrieval, reranking, Ollama generation and claim-level NLI checks."
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # 1. LATENCY WATERFALL (HTML styled)
        st.subheader("⏱ RAG Latency Breakdown (Waterfall)")
        
        embed_ms = trace.get("embedding_ms", 0.0)
        ret_ms = trace.get("retrieval_ms", 0.0)
        rerank_ms = trace.get("reranking_ms", 0.0)
        gen_ms = trace.get("generation_ms", 0.0)
        nli_ms = trace.get("nli_ms", 0.0)
        total_ms = trace.get("total_ms", 1.0)
        
        # Compile bars percentages
        def get_width(val):
            return max(1.0, (val / total_ms) * 100)
            
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.02); padding: 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                <div style="margin-bottom: 12px;">
                    <div style="width: 150px; display: inline-block; font-size: 0.9em; font-weight: 500;">1. Query Embedding</div>
                    <div class="waterfall-bar" style="width: {get_width(embed_ms)}%; background: #3498db;"></div>
                    <span style="font-size: 0.85em; opacity: 0.7;">{embed_ms} ms</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="width: 150px; display: inline-block; font-size: 0.9em; font-weight: 500;">2. ChromaDB Retrieval</div>
                    <div class="waterfall-bar" style="width: {get_width(ret_ms)}%; background: #9b59b6;"></div>
                    <span style="font-size: 0.85em; opacity: 0.7;">{ret_ms} ms</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="width: 150px; display: inline-block; font-size: 0.9em; font-weight: 500;">3. Semantic Reranking</div>
                    <div class="waterfall-bar" style="width: {get_width(rerank_ms)}%; background: #e67e22;"></div>
                    <span style="font-size: 0.85em; opacity: 0.7;">{rerank_ms} ms</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="width: 150px; display: inline-block; font-size: 0.9em; font-weight: 500;">4. LLM Generation</div>
                    <div class="waterfall-bar" style="width: {get_width(gen_ms)}%; background: #00cc99;"></div>
                    <span style="font-size: 0.85em; opacity: 0.7;">{gen_ms} ms</span>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="width: 150px; display: inline-block; font-size: 0.9em; font-weight: 500;">5. NLI Verification</div>
                    <div class="waterfall-bar" style="width: {get_width(nli_ms)}%; background: #e74c3c;"></div>
                    <span style="font-size: 0.85em; opacity: 0.7;">{nli_ms} ms</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # 2. CLAIM VERIFICATION BREAKDOWN & SHIELD LEVEL INDICATOR
        st.subheader("🛡 Claim Verification Mappings")
        
        verdict = verification.get("overall_verdict", "Unknown")
        faithfulness = verification.get("faithfulness_score", 0.0)
        
        if faithfulness >= 0.90:
            st.success(f"🟢 **Verdict: {verdict} (Low Hallucination Risk)** — All synthesized sentences are strictly entailed by the text context.")
        elif faithfulness >= 0.70:
            st.warning(f"🟡 **Verdict: {verdict} (Medium Hallucination Risk)** — Some claims might not have complete explicit backing.")
        else:
            st.error(f"🔴 **Verdict: {verdict} (High Hallucination Risk)** — Severe groundedness warnings detected!")
            
        claim_results = verification.get("claim_results", [])
        for i, claim in enumerate(claim_results):
            c_verdict = claim.get("verdict", "Unknown")
            c_score = claim.get("score", 0.0)
            c_conf = claim.get("confidence", 0.0)
            c_method = claim.get("method", "N/A")
            c_text = claim.get("claim", "")
            
            with st.expander(f"Sentence Claim [{i+1}] — Verdict: {c_verdict} (Conf: {c_conf * 100:.0f}%)"):
                col_c1, col_c2 = st.columns([4, 1])
                with col_c1:
                    st.markdown(f"**Claim Text:** `{c_text}`")
                    st.write(f"**NLI Entailment Score:** `{c_score}` | **Validation Method:** `{c_method}`")
                with col_c2:
                    if c_verdict == "Verified":
                        st.success("Verified")
                    elif c_verdict == "Mostly Supported":
                        st.warning("Mostly Supported")
                    else:
                        st.error("Hallucinated")
                        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # 3. SEMANTIC SOURCE HIGHLIGHTING
        st.subheader("📚 Retrieved Chunks with Semantic Highlight")
        st.caption("We highlight matching statements inside retrieved source text. Entailed claims are highlighted in green, warnings in red.")
        
        for i, chunk in enumerate(retrieved_chunks):
            content = chunk["content"]
            source = chunk["source"]
            page = chunk["page"]
            score = chunk.get("similarity_score", 0.0)
            
            # Apply semantic highlights to the chunk content
            highlighted_content = content
            
            # Iterate claim results and find matching text in content to wrap in styled span
            for c_res in claim_results:
                claim_text = c_res.get("claim", "")
                c_ver = c_res.get("verdict", "Unknown")
                
                # Simple exact match or subset match inside content
                # To be resilient, search for words
                words = re.findall(r"\b\w+\b", claim_text.lower())
                # If there is enough token overlap, try highlighting
                if len(words) > 3:
                    # Look for claim phrases in chunk content (case insensitive)
                    # We look for continuous word sequences or similar substrings
                    # For safety, let's look for exact phrase match
                    # Escape text for regex safety
                    escaped_claim = re.escape(claim_text.strip())
                    # Clean up dots/commas matches
                    escaped_claim = re.sub(r'\\.', r'\.?', escaped_claim)
                    
                    try:
                        pattern = re.compile(escaped_claim, re.IGNORECASE)
                        if c_ver == "Verified":
                            highlighted_content = pattern.sub(
                                f'<span class="semantic-highlight-verified">{claim_text}</span>',
                                highlighted_content
                            )
                        elif c_ver == "Mostly Supported":
                            highlighted_content = pattern.sub(
                                f'<span class="semantic-highlight-mostly">{claim_text}</span>',
                                highlighted_content
                            )
                        else:
                            highlighted_content = pattern.sub(
                                f'<span class="semantic-highlight-hallucinated">{claim_text}</span>',
                                highlighted_content
                            )
                    except Exception:
                        pass
                        
            # Render chunk card
            st.markdown(
                f"""
                <div class="glass-card" id="chunk_{i+1}">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="font-weight: 600; color: #00cc99;">📖 Citation [{i+1}]</span>
                        <span style="font-size: 0.85em; opacity: 0.65;">Source: {source} | Page: {page} | Score: {score}</span>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); font-size: 0.92em; line-height: 1.6; color: #cbd5e1;">
                        {highlighted_content}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================
# TAB 3: OBSERVABILITY METRICS & HISTORICAL ANALTICS
# =========================================
with tab_metrics:
    st.markdown("<div id='analytics'></div>", unsafe_allow_html=True)
    st.markdown("<h3>📊 RAG & Hallucination Analytics Dashboard</h3>", unsafe_allow_html=True)
    st.caption("Historical trace monitoring of faithfulness trend lines, latencies, and risk-level metrics.")
    
    # Fetch historical data from backend API
    analytics = None
    try:
        ans_resp = requests.get(f"{BACKEND_URL}/analytics", timeout=10)
        if ans_resp.status_code == 200:
            analytics = ans_resp.json()
    except Exception as e:
        st.error(f"Failed to fetch analytics metrics: {e}")
        
    if not analytics or analytics.get("total_queries", 0) == 0:
        st.markdown(
            """
            <div style="text-align: center; opacity: 0.4; padding: 80px 0;">
                <img src="https://img.icons8.com/nolan/96/combo-chart.png" style="width: 60px; margin-bottom: 15px;"/>
                <h4>No analytics metrics logged.</h4>
                <p>Run query questions inside the Chat Studio to populate historical trend charts here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Analytics cards
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Queries Served", analytics["total_queries"])
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Average Pipeline Latency", f"{analytics['avg_latency_ms'] / 1000:.2f}s")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Average Faithfulness", f"{analytics['avg_faithfulness'] * 100:.0f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Average NLI Confidence", f"{analytics['avg_confidence'] * 100:.0f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Risk Distribution Chart
        st.subheader("🛡 Hallucination Risk Distribution")
        risk_dist = analytics.get("risk_distribution", {})
        st.bar_chart(risk_dist)
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Queries Log Table
        st.subheader("📜 Historical Query Metrics Logs")
        st.dataframe(
            analytics.get("history", []),
            column_config={
                "timestamp": "Time",
                "question": "User Query",
                "total_latency_ms": "Latency (ms)",
                "faithfulness_score": "Faithfulness Score",
                "confidence_score": "Confidence",
                "verdict": "Overall Verdict"
            },
            use_container_width=True
        )

# =========================================
# TAB 4: DOCUMENT REGISTRY & MANAGEMENT
# =========================================
with tab_docs:
    st.markdown("<div id='docs'></div>", unsafe_allow_html=True)
    st.markdown("<h3>📁 Document Management Center</h3>", unsafe_allow_html=True)
    st.caption("Upload multi-format document files, track their status, and manage vector store contents.")
    
    # Grid layout for file manager
    col_u1, col_u2 = st.columns([1, 2])
    
    with col_u1:
        st.subheader("Upload Documents")
        st.caption("Drop files to validation check, hash index, and vectorize.")
        
        uploaded_files = st.file_uploader(
            "Supported formats: .pdf, .docx, .txt (Max 15MB)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        
        if st.button("🚀 Process & Vectorize Documents", use_container_width=True):
            if not uploaded_files:
                st.warning("Please upload at least one document file.")
            else:
                success_docs = 0
                error_docs = 0
                
                # Active progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Processing ({i+1}/{len(uploaded_files)}): {file.name}")
                    
                    files_payload = {
                        "file": (file.name, file.getvalue(), "application/octet-stream")
                    }
                    
                    try:
                        resp = requests.post(f"{BACKEND_URL}/upload", files=files_payload, timeout=300)
                        if resp.status_code == 201:
                            success_docs += 1
                        else:
                            error_docs += 1
                            st.error(f"Error uploading '{file.name}': {resp.json().get('detail')}")
                    except Exception as e:
                        error_docs += 1
                        st.error(f"Connection failed for '{file.name}': {e}")
                        
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                status_text.text(f"Indexing Complete! Success: {success_docs} | Errors: {error_docs}")
                time.sleep(1.5)
                progress_bar.empty()
                status_text.empty()
                
                # Pull new lists
                refresh_documents()
                st.rerun()
                
    with col_u2:
        st.subheader("Currently Indexed Documents")
        st.caption("Manage files currently registered in vector space.")
        
        if not st.session_state.document_registry:
            st.markdown(
                """
                <div style="text-align: center; opacity: 0.4; padding: 50px 0; border: 1px dashed rgba(255,255,255,0.1); border-radius: 12px;">
                    <img src="https://img.icons8.com/nolan/96/empty-folder.png" style="width: 50px; margin-bottom: 10px;"/>
                    <h5>No documents indexed yet.</h5>
                    <p>Upload files on the left to start indexing context.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for item in st.session_state.document_registry:
                filename = item["filename"]
                size_kb = round(item["size_bytes"] / 1024, 2)
                file_type = item["file_type"]
                added_at = item["added_at"]
                
                # Custom Document Card with Inline Delete
                col_d1, col_d2 = st.columns([5, 1])
                with col_d1:
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px 18px; border-radius: 10px; margin-bottom: 10px; font-size: 0.9em;">
                            <div style="font-weight: 600; color: #f8fafc;">📄 {filename}</div>
                            <div style="font-size: 0.8em; opacity: 0.65; margin-top: 4px;">Type: {file_type} | Size: {size_kb} KB | Added: {added_at}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_d2:
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑", key=f"del_{filename}", help=f"Delete document: {filename}", use_container_width=True):
                        with st.spinner(f"Deleting '{filename}'..."):
                            try:
                                # URL encoding the name safely
                                safe_name = requests.utils.quote(filename)
                                res = requests.delete(f"{BACKEND_URL}/documents/{safe_name}", timeout=15)
                                if res.status_code == 200:
                                    st.success(f"Deleted '{filename}'!")
                                    time.sleep(1)
                                    refresh_documents()
                                    st.rerun()
                                else:
                                    st.error("Failed to delete.")
                            except Exception as e:
                                st.error(f"Error: {e}")
                                
            # PDF Inline Preview Support
            st.markdown("<br/>", unsafe_allow_html=True)
            st.subheader("🔍 Active PDF Viewer")
            pdf_names = [doc["filename"] for doc in st.session_state.document_registry if doc["file_type"] == ".pdf"]
            
            if pdf_names:
                selected_pdf = st.selectbox("Select document to preview:", pdf_names)
                if selected_pdf:
                    pdf_file_path = os.path.join(settings.UPLOADS_DIR, selected_pdf)
                    if os.path.exists(pdf_file_path):
                        try:
                            with open(pdf_file_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button(
                                label=f"📥 Download {selected_pdf} for Local View",
                                data=pdf_bytes,
                                file_name=selected_pdf,
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"Could not load preview: {e}")
            else:
                st.caption("No PDFs currently indexed to preview.")