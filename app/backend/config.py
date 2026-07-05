import os

class Settings:
    # =========================================
    # PATHS
    # =========================================
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
    UPLOADS_DIR = "uploads"
    REGISTRY_FILE = os.path.join(UPLOADS_DIR, "registry.json")

    # =========================================
    # MODELS
    # =========================================
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "phi3")
    NLI_MODEL = os.getenv("NLI_MODEL", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")

    # =========================================
    # SECURITY & VALIDATION
    # =========================================
    MAX_FILE_SIZE_MB = 15
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

settings = Settings()
