import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from app.backend.services.rag_service import (
    add_document,
    ask_question,
    ask_question_stream,
    delete_document_by_name,
    clear_database,
    get_analytics_metrics
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Internal imports
from app.backend.config import settings
from app.backend.utils.logger import get_logger
from app.backend.utils.helpers import secure_filename
from app.backend.services.pdf_service import get_loaded_documents


logger = get_logger("main")

# =========================================
# FASTAPI INSTANCE
# =========================================
app = FastAPI(
    title="VeriFact AI Backend API",
    description="Automated Hallucination Detection & RAG Observability System API",
    version="2.0.0"
)

# =========================================
# CORS MIDDLEWARE
# =========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# PYDANTIC SCHEMAS
# =========================================
class ChatMessage(BaseModel):
    question: str = Field(..., description="User question")
    answer: str = Field(..., description="AI generated answer")

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The user's query question")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Conversational history for sliding window memory")

class SingleClaimResult(BaseModel):
    claim: str
    label: str
    score: float
    verdict: str
    confidence: float
    method: str

class VerificationDetails(BaseModel):
    faithfulness_score: float
    average_confidence: float
    overall_verdict: str
    claim_results: List[SingleClaimResult]

class ChunkDetails(BaseModel):
    content: str
    source: str
    page: Any
    chunk_id: Any
    similarity_score: float

class LatencyTrace(BaseModel):
    embedding_ms: float
    retrieval_ms: float
    reranking_ms: float
    generation_ms: float
    nli_ms: float
    total_ms: float

class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: List[ChunkDetails]
    verification: VerificationDetails
    trace: LatencyTrace

class UploadResponse(BaseModel):
    message: str
    status: str
    filename: str
    chunks: Optional[int] = None

class DocumentItem(BaseModel):
    filename: str
    size_bytes: int
    file_type: str
    hash: str
    added_at: str
    status: str

# =========================================
# HEALTH ENDPOINTS
# =========================================
@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {
        "status": "online",
        "message": "VeriFact AI Backend running with FastAPI, Ollama and ChromaDB.",
        "config": {
            "llm": settings.LLM_MODEL,
            "nli": settings.NLI_MODEL,
            "max_upload_size_mb": settings.MAX_FILE_SIZE_MB
        }
    }

# =========================================
# RAG QA ENDPOINT
# =========================================
@app.post("/ask", status_code=status.HTTP_200_OK)
async def query_rag(request: QuestionRequest):
    """Processes user query, queries ChromaDB, generates answers, and verifies claims."""
    logger.info(f"Received query: '{request.question}'")
    try:
        # Convert request history to dictionary list if present
        history_list = []
        if request.history:
            history_list = [item.dict() for item in request.history]

        # Return a streaming response so the frontend can display tokens incrementally
        # The generator yields JSON lines with types: token, verification, trace, chunks
        # FastAPI will stream these lines to the client
        return StreamingResponse(
            ask_question_stream(request.question, history_list),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error serving query '{request.question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering the question: {str(e)}"
        )

# =========================================
# FILE UPLOAD ENDPOINT
# =========================================
@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """Validates magic bytes, checks for duplicates, chunks, indexes, and registers a document."""
    try:
        orig_name = secure_filename(file.filename)
        logger.info(f"Received upload request for file: '{orig_name}'")
        
        # Verify file suffix is allowed
        _, ext = os.path.splitext(orig_name.lower())
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' not allowed. Allowed types: {list(settings.ALLOWED_EXTENSIONS)}"
            )
            
        os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
        temp_path = os.path.join(settings.UPLOADS_DIR, f"temp_{orig_name}")
        
        # Save uploaded file in temp location safely
        with open(temp_path, "wb") as buffer:
            # Chunk writing to avoid high memory spikes on large uploads
            while content := await file.read(64 * 1024):  # 64KB chunks
                buffer.write(content)
                
        # Perform indexing and registry checks in service
        try:
            result = add_document(temp_path, orig_name)
            
            # Move temp file to finalized path on success
            final_path = os.path.join(settings.UPLOADS_DIR, orig_name)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
            
            return {
                "message": result["message"],
                "status": result["status"],
                "filename": orig_name,
                "chunks": result.get("chunks")
            }
            
        except ValueError as val_err:
            # Clean up temp file on semantic validation errors
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.warning(f"File validation failed for '{orig_name}': {val_err}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(val_err)
            )
            
        except Exception as e:
            # Clean up temp file on other failures
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error handling upload file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload and process file: {str(e)}"
        )

# =========================================
# DOCUMENT MANAGEMENT ENDPOINTS
# =========================================
@app.get("/documents", response_model=List[DocumentItem], status_code=status.HTTP_200_OK)
async def list_documents():
    """Lists all successfully processed and indexed documents in VeriFact AI."""
    try:
        return get_loaded_documents()
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve indexed documents list."
        )

@app.delete("/documents/{filename}", status_code=status.HTTP_200_OK)
async def delete_document(
    filename: str = Path(..., description="The name of the document to delete")
):
    """Deletes an indexed document from both disk storage and ChromaDB."""
    try:
        success = delete_document_by_name(filename)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{filename}' not found or could not be deleted."
            )
        return {
            "message": f"Document '{filename}' successfully deleted from vector index and disk storage."
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error deleting document '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

# =========================================
# RESET & OBSERVABILITY ANALYTICS
# =========================================
@app.post("/reset", status_code=status.HTTP_200_OK)
async def reset_database():
    """Securely wipes both the ChromaDB vector collections, upload folders, and registry."""
    try:
        clear_database()
        return {
            "message": "Database and file indexes successfully reset."
        }
    except Exception as e:
        logger.error(f"Error during system reset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset system: {str(e)}"
        )

@app.get("/analytics", status_code=status.HTTP_200_OK)
async def fetch_analytics():
    """Retrieves high-level analytics tracking faithfulness, latencies, and risk rates."""
    try:
        return get_analytics_metrics()
    except Exception as e:
        logger.error(f"Error retrieving analytics data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load analytics: {str(e)}"
        )