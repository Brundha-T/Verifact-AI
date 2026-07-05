import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# =========================================
# LOGGING SETUP
# =========================================
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "app.log")

# Setup formatter
formatter = logging.Formatter(LOG_FORMAT)

# Setup handlers
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Configure Root Logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Avoid duplicate handlers if loaded multiple times
if not root_logger.handlers:
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str):
    """Returns a structured logger instance for a given module."""
    return logging.getLogger(name)
