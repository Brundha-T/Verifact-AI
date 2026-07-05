import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

pdf_path = os.path.join(BASE_DIR, "data", "sample doc.pdf")

persist_directory = os.path.join(BASE_DIR, "chroma_db")

# LOAD PDF
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# SPLIT
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)

docs = text_splitter.split_documents(documents)

# ADD METADATA
for i, doc in enumerate(docs):
    doc.metadata["chunk_id"] = i

# EMBEDDING MODEL
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# CREATE VECTOR DB
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embedding_model,
    persist_directory=persist_directory
)

vectorstore.persist()

print("ChromaDB created successfully")