# Backwards compatibility redirect
import os
from app.backend.services.rag_service import (
    ask_question as _ask_question,
    add_document as _add_document,
    clear_database as _clear_database
)

def add_document(pdf_path):
    orig_name = os.path.basename(pdf_path)
    return _add_document(pdf_path, orig_name)

def ask_question(question):
    # Simply forward and strip any extra trace keys for old compatibility
    res = _ask_question(question)
    return {
        "answer": res["answer"],
        "retrieved_chunks": res["retrieved_chunks"],
        "verification": res["verification"]
    }

def clear_database():
    return _clear_database()