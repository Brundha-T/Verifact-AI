import os
import json
import zipfile
import xml.etree.ElementTree as ET
from app.backend.config import settings
from app.backend.utils.logger import get_logger
from app.backend.utils.helpers import calculate_file_hash, secure_filename

logger = get_logger("pdf_service")

# =========================================
# MAGIC NUMBERS
# =========================================
MAGIC_PDF = b"%PDF"
MAGIC_ZIP_DOCX = b"PK\x03\x04"

# =========================================
# REGISTRY MANAGEMENT
# =========================================
def load_registry() -> dict:
    """Loads the file registry tracking processed documents."""
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    if os.path.exists(settings.REGISTRY_FILE):
        try:
            with open(settings.REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading registry: {e}. Resetting registry.")
            return {}
    return {}

def save_registry(registry: dict):
    """Saves the file registry tracking processed documents."""
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    try:
        with open(settings.REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving registry: {e}")

# =========================================
# MAGIC BYTE VALIDATION
# =========================================
def validate_magic_bytes(file_path: str) -> str:
    """Checks magic bytes of file to determine actual type.
    
    Returns '.pdf', '.docx', '.txt', or raises ValueError if invalid.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            
        if header.startswith(MAGIC_PDF):
            return ".pdf"
        elif header.startswith(MAGIC_ZIP_DOCX):
            # Verify if it is really a docx zip archive
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path) as z:
                    if "word/document.xml" in z.namelist():
                        return ".docx"
            raise ValueError("ZIP archive is not a valid DOCX file.")
            
        # Fallback to checking if it is UTF-8 readable text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read(1024)
            return ".txt"
        except UnicodeDecodeError:
            raise ValueError("File content is not valid UTF-8 text.")
            
    except Exception as e:
        logger.error(f"Validation failed for {file_path}: {e}")
        raise ValueError(f"File validation failed: {str(e)}")

# =========================================
# DOCUMENT PARSERS
# =========================================
def parse_docx(file_path: str) -> str:
    """Parses text from a DOCX file using pure standard library ZipFile and XML parsing."""
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read("word/document.xml")
            root = ET.fromstring(xml_content)
            
            # OpenXML namespace
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            
            paragraphs = []
            for para in root.findall(".//w:p", ns):
                text_elems = para.findall(".//w:t", ns)
                text = "".join([t.text for t in text_elems if t.text])
                if text.strip():
                    paragraphs.append(text)
                    
            return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Failed parsing DOCX {file_path}: {e}")
        raise ValueError(f"Failed to parse DOCX: {e}")

def parse_txt(file_path: str) -> str:
    """Parses text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed parsing TXT {file_path}: {e}")
        raise ValueError(f"Failed to parse text file: {e}")

# =========================================
# FILE METADATA FETCH
# =========================================
def get_loaded_documents() -> list:
    """Returns a list of all currently loaded files from the registry."""
    registry = load_registry()
    docs_list = []
    for file_hash, meta in registry.items():
        docs_list.append({
            "filename": meta.get("filename"),
            "size_bytes": meta.get("size_bytes", 0),
            "file_type": meta.get("file_type"),
            "hash": file_hash,
            "added_at": meta.get("added_at", "Unknown"),
            "status": meta.get("status", "Indexed")
        })
    return docs_list
