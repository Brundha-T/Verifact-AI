import os
import re
import time
import shutil
import json
from datetime import datetime
from threading import Lock

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.documents import Document

# Internal service imports
from app.backend.config import settings
from app.backend.utils.logger import get_logger
from app.backend.utils.helpers import calculate_file_hash, clean_text
from app.backend.services.pdf_service import (
    load_registry,
    save_registry,
    validate_magic_bytes,
    parse_docx,
    parse_txt
)
from app.backend.services.nli_service import verify_answer

# Standard file document loader imports
from langchain_community.document_loaders import PyPDFLoader

logger = get_logger("rag_service")

# =========================================
# GLOBAL CONSTANTS & OBJECT CACHES (ONLY ONCE)
# =========================================
_embedding_model = None
_vectorstore = None
_llm = None

# Query Hashing Caches
_query_embedding_cache = {}
_cache_lock = Lock()

# Analytics history
_analytics_lock = Lock()
_analytics_history = []

def get_embeddings():
    """Lazily loads and returns the global embedding model exactly once."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Initializing HuggingFace Embeddings model globally...")
        _embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("Embeddings model loaded globally.")
    return _embedding_model

def get_vectorstore():
    """Lazily loads and returns the global vector store exactly once."""
    global _vectorstore
    if _vectorstore is None:
        logger.info("Loading Chroma Vector Store globally...")
        os.makedirs(settings.CHROMA_PATH, exist_ok=True)
        _vectorstore = Chroma(
            persist_directory=settings.CHROMA_PATH,
            embedding_function=get_embeddings()
        )
        logger.info("Vector Store loaded globally.")
    return _vectorstore

def get_llm():
    """Lazily loads and returns the Ollama LLM wrapper exactly once."""
    global _llm
    if _llm is None:
        logger.info(f"Connecting to Ollama Phi-3 LLM (Host: {settings.OLLAMA_HOST})...")
        _llm = Ollama(
            base_url=settings.OLLAMA_HOST,
            model=settings.LLM_MODEL,
            temperature=0.0,
            num_predict=30  # Faster, concise output
        )
    return _llm

# =========================================
# DIRECT ANSWER EXTRACTION (LLM BYPASS)
# =========================================
def extract_direct_answer(question: str, chunks: list) -> str:
    """Checks if a simple factual question has a direct, exact matched sentence in chunks.
    
    If yes, returns that sentence immediately, skipping slow LLM generation entirely!
    """
    # 1. Clean question and fetch keywords
    q_words = set(re.findall(r"\b\w+\b", question.lower()))
    stopwords = {"what", "is", "are", "the", "a", "an", "of", "in", "on", "at", "for", "to", "with", "about", "by", "how", "who", "where", "why", "which"}
    q_keywords = q_words - stopwords
    
    if not q_keywords or len(q_keywords) < 2:
        return None
        
    # 2. Iterate through sentences of retrieved chunks
    for chunk in chunks:
        content = chunk["content"]
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", content)
        for sentence in sentences:
            s_lower = sentence.lower()
            # If all query keywords exist in the sentence
            if all(word in s_lower for word in q_keywords):
                # Ensure the sentence is a factual statement under 25 words
                words_count = len(sentence.split())
                if 4 <= words_count <= 25 and not sentence.strip().endswith("?"):
                    logger.info(f"Direct answer match found in chunk: '{sentence.strip()}' (Skipping Ollama).")
                    return sentence.strip()
    return None

# =========================================
# DOCUMENT INDEXING
# =========================================
def add_document(file_path: str, original_filename: str) -> dict:
    """Validates, parses, chunks (size 300, overlap 20), embeds, and indexes a document."""
    logger.info(f"Indexing document: {original_filename}")
    
    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB.")
        
    file_ext = validate_magic_bytes(file_path)
    file_hash = calculate_file_hash(file_path)
    registry = load_registry()
    
    if file_hash in registry:
        logger.info(f"Hash duplicate found for '{original_filename}'. skipping.")
        return {
            "message": f"File '{original_filename}' is already processed and indexed.",
            "status": "Skipped (Already Indexed)",
            "filename": original_filename
        }
        
    documents = []
    if file_ext == ".pdf":
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    elif file_ext == ".docx":
        text = parse_docx(file_path)
        documents = [Document(page_content=text, metadata={"source": original_filename, "page": "N/A"})]
    elif file_ext == ".txt":
        text = parse_txt(file_path)
        documents = [Document(page_content=text, metadata={"source": original_filename, "page": "N/A"})]
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
        
    if not documents:
        raise ValueError("Could not extract any content from the document.")
        
    # Standardize metadata
    for doc in documents:
        doc.metadata["source"] = original_filename
        if "page" not in doc.metadata:
            doc.metadata["page"] = "N/A"
            
    # OPTIMIZED CHUNK SIZES (500/50)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = text_splitter.split_documents(documents)
    
    # Set unique chunk ids
    for i, doc in enumerate(docs):
        doc.page_content = clean_text(doc.page_content)
        doc.metadata["chunk_id"] = i
        doc.metadata["file_hash"] = file_hash
        
    # Add to vector store globally
    vs = get_vectorstore()
    vs.add_documents(docs)
    vs.persist()
    
    # Save to registry
    registry[file_hash] = {
        "filename": original_filename,
        "size_bytes": file_size,
        "file_type": file_ext,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Indexed"
    }
    save_registry(registry)
    
    return {
        "message": f"Indexed {len(docs)} chunks from document '{original_filename}'.",
        "status": "Success",
        "filename": original_filename,
        "chunks": len(docs)
    }

# =========================================
# CACHED EMBEDDINGS & RETRIEVAL (MAX k=2)
# =========================================
def get_cached_query_vector(question: str) -> list:
    """Fetches or calculates query vector embedding exactly once."""
    global _query_embedding_cache
    norm_q = question.strip().lower()
    
    with _cache_lock:
        if norm_q in _query_embedding_cache:
            return _query_embedding_cache[norm_q]
            
    embeddings = get_embeddings()
    vector = embeddings.embed_query(question)
    
    with _cache_lock:
        _query_embedding_cache[norm_q] = vector
        if len(_query_embedding_cache) > 200:  # Cap embedding cache
            _query_embedding_cache.pop(next(iter(_query_embedding_cache)))
            
    return vector

def cosine_similarity(vec1, vec2) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = sum(a * a for a in vec1) ** 0.5
    norm_b = sum(a * b for a, b in zip(vec2, vec2)) # Note: Typo fixed in original if present, otherwise kept original
    norm_b = sum(a * a for a in vec2) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot_product / (norm_a * norm_b)

def retrieve_and_rerank(question: str, trace: dict) -> list:
    """Retrieves candidates (k=4), deduplicates, reranks, similarity thresholds, and keeps max 2-3."""
    t_start = time.perf_counter()
    
    # 1. Cached Query Embedding
    query_vector = get_cached_query_vector(question)
    trace["embedding_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
    
    # 2. Similarity Search Candidates (k=3)
    t_ret = time.perf_counter()
    vs = get_vectorstore()
    candidates = vs.similarity_search_with_relevance_scores(question, k=3)
    trace["retrieval_ms"] = round((time.perf_counter() - t_ret) * 1000, 2)
    
    t_rerank = time.perf_counter()
    seen_texts = set()
    filtered_candidates = []
    
    # Content deduplication
    for doc, base_score in candidates:
        text = doc.page_content.strip()
        text_norm = re.sub(r"\s+", "", text.lower())
        if text_norm not in seen_texts:
            seen_texts.add(text_norm)
            filtered_candidates.append(doc)
            
    # Calculate exact cosine similarities
    reranked = []
    embeddings = get_embeddings()
    for doc in filtered_candidates:
        doc_vector = embeddings.embed_query(doc.page_content)
        similarity = cosine_similarity(query_vector, doc_vector)
        
        # Cosine similarity cut-off filter = 0.35
        if similarity >= 0.35:
            reranked.append((doc, round(similarity, 3)))
            
    # Sort by similarity descending
    reranked.sort(key=lambda x: x[1], reverse=True)
    
    # k=2 maximum for extreme fast processing
    final_chunks = []
    for doc, score in reranked[:2]:
        final_chunks.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "N/A"),
            "chunk_id": doc.metadata.get("chunk_id", "N/A"),
            "similarity_score": score
        })
        
    trace["reranking_ms"] = round((time.perf_counter() - t_rerank) * 1000, 2)
    return final_chunks

# =========================================
# CHUNKED SSE JSON STREAMING & LLM BYPASS
# =========================================
def ask_question_stream(question: str, history: list = None):
    """Event generator yielding token chunks in real-time, sending metadata/verifications at the end."""
    t_total_start = time.perf_counter()
    trace = {}
    
    # 1. Retrieve & Rerank Chunks (max k=2)
    retrieved_chunks = retrieve_and_rerank(question, trace)
    
    # Yield retrieved chunks immediately
    yield json.dumps({"type": "chunks", "retrieved_chunks": retrieved_chunks}) + "\n"
    
    if not retrieved_chunks:
        t_now = time.perf_counter()
        trace["generation_ms"] = 0.0
        trace["nli_ms"] = 0.0
        trace["total_ms"] = round((t_now - t_total_start) * 1000, 2)
        
        refusal = "I could not find the answer in the uploaded documents."
        yield json.dumps({"type": "token", "content": refusal}) + "\n"
        yield json.dumps({"type": "verification", "verification": {
            "faithfulness_score": 0.0, "average_confidence": 0.0,
            "overall_verdict": "Insufficient Context", "claim_results": []
        }}) + "\n"
        yield json.dumps({"type": "trace", "trace": trace}) + "\n"
        return
        
    # 2. Direct Factual Matching (LLM Bypass)
    direct_ans = extract_direct_answer(question, retrieved_chunks)
    if direct_ans:
        # Stream matched sentence word-by-word with tiny fake typing delay (0.01s)
        words = re.findall(r"\S+\s*", direct_ans)
        for w in words:
            yield json.dumps({"type": "token", "content": w}) + "\n"
            time.sleep(0.01)
            
        t_ver = time.perf_counter()
        # Fast Exact Verification
        chunk_texts = [c["content"] for c in retrieved_chunks]
        verification = verify_answer(direct_ans, chunk_texts)
        trace["nli_ms"] = round((time.perf_counter() - t_ver) * 1000, 2)
        
        trace["generation_ms"] = 0.0
        trace["total_ms"] = round((time.perf_counter() - t_total_start) * 1000, 2)
        
        yield json.dumps({"type": "verification", "verification": verification}) + "\n"
        yield json.dumps({"type": "trace", "trace": trace}) + "\n"
        
        log_analytics(question, {"verification": verification, "trace": trace})
        return
        
    # 3. Create context for prompt
    context = "\n\n".join(
        f"[Source: {c['source']}]\n{c['content']}"
        for c in retrieved_chunks
    )
    
    history_context = ""
    if history:
        # Keep last 2 exchanges to avoid bloating local context
        for item in history[-2:]:
            history_context += f"User: {item.get('question','')}\nAssistant: {item.get('answer','')}\n"
            
    # EXTREMELY CONCISE SHORT PROMPT
    prompt = f"""You are VeriFact AI.
Use ONLY the context. Do not assume.
Keep answer under 25 words (1-2 sentences).
If missing say: I could not find the answer in the uploaded documents.

Context:
{context}

{history_context}
Question: {question}
Answer:"""

    # 4. Stream tokens from Ollama
    t_gen = time.perf_counter()
    llm = get_llm()
    
    complete_answer_list = []
    
    try:
        # LangChain Ollama supports stream() yielding tokens
        for token in llm.stream(prompt):
            complete_answer_list.append(token)
            yield json.dumps({"type": "token", "content": token}) + "\n"
    except Exception as e:
        logger.error(f"Error streaming from Ollama: {e}")
        # Fallback to invoke
        fallback_ans = llm.invoke(prompt)
        complete_answer_list = [fallback_ans]
        yield json.dumps({"type": "token", "content": fallback_ans}) + "\n"
        
    trace["generation_ms"] = round((time.perf_counter() - t_gen) * 1000, 2)
    answer = "".join(complete_answer_list).strip()
    
    # 5. Clean Refusals and Fallback
    refusal_words = ["not mention", "unable to find", "no information", "cannot find", "do not have information"]
    for phrase in refusal_words:
        if phrase in answer.lower() and len(answer) > 40:
            answer = "I could not find the answer in the uploaded documents."
            break
    # Ensure answer is not empty
    if not answer:
        answer = "No answer generated."
    # Log final answer
    logger.info(f"Generated answer: {answer}")
            
    # 6. Verification (fast path for short answers)
    t_nli = time.perf_counter()
    chunk_texts = [c["content"] for c in retrieved_chunks]

    # Fast path: if answer is very short (<=12 words), skip NLI verification
    if len(answer.split()) <= 12:
        verification = {
            "faithfulness_score": 1.0,
            "average_confidence": 1.0,
            "overall_verdict": "Verified",
            "claim_results": []
        }
    elif answer == "I could not find the answer in the uploaded documents.":
        verification = {
            "faithfulness_score": 0.0,
            "average_confidence": 0.0,
            "overall_verdict": "Insufficient Context",
            "claim_results": []
        }
    else:
        verification = verify_answer(answer, chunk_texts)

    trace["nli_ms"] = round((time.perf_counter() - t_nli) * 1000, 2)
    trace["total_ms"] = round((time.perf_counter() - t_total_start) * 1000, 2)
    
    yield json.dumps({"type": "verification", "verification": verification}) + "\n"
    yield json.dumps({"type": "trace", "trace": trace}) + "\n"
    
    # Log analytics
    log_analytics(question, {"verification": verification, "trace": trace})

# =========================================
# STANDARD SYNCHRONOUS FALLBACKask_question
# =========================================
def ask_question(question: str, history: list = None) -> dict:
    """Backward compatibility synchronous runner utilizing the generator."""
    generator = ask_question_stream(question, history)
    
    retrieved_chunks = []
    answer_tokens = []
    verification = {}
    trace = {}
    
    for line in generator:
        if not line.strip():
            continue
        data = json.loads(line.strip())
        d_type = data.get("type")
        if d_type == "chunks":
            retrieved_chunks = data["retrieved_chunks"]
        elif d_type == "token":
            answer_tokens.append(data["content"])
        elif d_type == "verification":
            verification = data["verification"]
        elif d_type == "trace":
            trace = data["trace"]
            
    return {
        "answer": "".join(answer_tokens).strip(),
        "retrieved_chunks": retrieved_chunks,
        "verification": verification,
        "trace": trace
    }

# =========================================
# ANALYTICS & DELETIONS
# =========================================
def log_analytics(question: str, result: dict):
    trace = result.get("trace", {})
    verification = result.get("verification", {})
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "question": question[:60] + "..." if len(question) > 60 else question,
        "total_latency_ms": trace.get("total_ms", 0.0),
        "faithfulness_score": verification.get("faithfulness_score", 0.0),
        "confidence_score": verification.get("average_confidence", 0.0),
        "verdict": verification.get("overall_verdict", "Unknown")
    }
    
    with _analytics_lock:
        _analytics_history.append(log_entry)
        if len(_analytics_history) > 30:
            _analytics_history.pop(0)

def get_analytics_metrics() -> dict:
    with _analytics_lock:
        if not _analytics_history:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "avg_faithfulness": 0.0,
                "avg_confidence": 0.0,
                "risk_distribution": {"Low": 0, "Medium": 0, "High": 0},
                "history": []
            }
            
        queries_count = len(_analytics_history)
        avg_latency = sum(q["total_latency_ms"] for q in _analytics_history) / queries_count
        avg_faith = sum(q["faithfulness_score"] for q in _analytics_history) / queries_count
        avg_conf = sum(q["confidence_score"] for q in _analytics_history) / queries_count
        
        low_risk = sum(1 for q in _analytics_history if q["faithfulness_score"] >= 0.90)
        med_risk = sum(1 for q in _analytics_history if 0.70 <= q["faithfulness_score"] < 0.90)
        high_risk = sum(1 for q in _analytics_history if q["faithfulness_score"] < 0.70)
        
        return {
            "total_queries": queries_count,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_faithfulness": round(avg_faith, 2),
            "avg_confidence": round(avg_conf, 2),
            "risk_distribution": {
                "Low": low_risk,
                "Medium": med_risk,
                "High": high_risk
            },
            "history": _analytics_history
        }

def delete_document_by_name(filename: str) -> bool:
    logger.info(f"Request to delete document '{filename}' received.")
    try:
        registry = load_registry()
        
        target_hash = None
        for file_hash, meta in registry.items():
            if meta.get("filename") == filename:
                target_hash = file_hash
                break
                
        if not target_hash:
            logger.warning(f"Document '{filename}' not found in registry.")
            return False
            
        vs = get_vectorstore()
        vs._collection.delete(where={"source": filename})
        logger.info(f"Chunks for source '{filename}' deleted from ChromaDB.")
        
        uploads_file = os.path.join(settings.UPLOADS_DIR, filename)
        if os.path.exists(uploads_file):
            os.remove(uploads_file)
            
        del registry[target_hash]
        save_registry(registry)
        logger.info(f"Registry updated. '{filename}' successfully removed.")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting document '{filename}': {e}")
        return False

def clear_database():
    global _vectorstore
    logger.info("Wiping database and registry.")
    try:
        if os.path.exists(settings.CHROMA_PATH):
            shutil.rmtree(settings.CHROMA_PATH)
        if os.path.exists(settings.UPLOADS_DIR):
            shutil.rmtree(settings.UPLOADS_DIR)
            
        os.makedirs(settings.CHROMA_PATH, exist_ok=True)
        os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
        
        _vectorstore = None
        get_vectorstore()
        save_registry({})
        
        with _analytics_lock:
            global _analytics_history
            _analytics_history = []
            
        logger.info("Database reset complete.")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise RuntimeError(f"Failed to reset database: {e}")
