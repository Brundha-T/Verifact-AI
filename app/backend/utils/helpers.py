import hashlib
import re
import os

def calculate_file_hash(file_path: str) -> str:
    """Calculates the SHA-256 hash of a file's content."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def secure_filename(filename: str) -> str:
    """Sanitizes a filename to prevent path traversal and shell injection.
    
    Standard library alternative to Werkzeug's secure_filename.
    """
    # Get basename only to prevent directory traversal (e.g. ../../etc/passwd)
    name = os.path.basename(filename)
    
    # Strip non-alphanumeric/dot/dash/underscore characters
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    
    # Remove leading dots or dashes which could be hidden files
    name = re.sub(r"^[.-]+", "", name)
    
    # If filename is empty, default to "uploaded_file"
    if not name:
        name = "uploaded_file"
        
    return name

def clean_text(text: str) -> str:
    """Cleans whitespace and standardizes formatting in text chunks."""
    if not text:
        return ""
    # Standardize spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()
