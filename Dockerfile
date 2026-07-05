# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (build-essential needed for some packages like ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501
