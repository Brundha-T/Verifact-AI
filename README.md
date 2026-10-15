# VeriFact AI: Hallucination-Aware RAG System

## 📌 Project Overview

VeriFact AI is an AI-powered question-answering and fact-verification system that allows users to ask questions based on information contained in PDF documents.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from uploaded documents and generate context-based answers. It also incorporates Natural Language Inference (NLI) to verify the factual consistency of generated answers against the retrieved context and help identify potential hallucinations.

The main goal of this project is to make AI-generated responses more reliable, transparent, and grounded in document-based evidence.

## 🎯 Objectives

- Enable users to ask questions about PDF documents.
- Retrieve relevant information from documents using semantic search.
- Generate answers using a language model and retrieved context.
- Verify generated answers using Natural Language Inference (NLI).
- Help identify answers that may be unsupported by the available evidence.

## ✨ Key Features

- **PDF-Based Question Answering:** Ask questions using the content of PDF documents.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant document chunks before generating answers.
- **Semantic Search:** Find relevant information based on the meaning of a query.
- **AI-Powered Responses:** Use the Phi-3 language model through Ollama to generate answers.
- **Hallucination Verification:** Apply NLI-based verification to assess whether generated answers are supported by the retrieved context.
- **Context-Grounded Responses:** Use retrieved document information to support answer generation.

## 🔄 System Workflow

1. **PDF Upload:** The user provides a PDF document as the knowledge source.
2. **Text Extraction:** Text is extracted from the PDF.
3. **Text Chunking:** The extracted text is divided into smaller chunks for efficient retrieval.
4. **Embedding Generation:** Text chunks are converted into vector embeddings.
5. **Vector Storage:** The embeddings are stored in ChromaDB.
6. **Question Processing:** The user's question is converted into an embedding.
7. **Relevant Information Retrieval:** ChromaDB retrieves relevant document chunks based on semantic similarity.
8. **Answer Generation:** The retrieved context is provided to the Phi-3 language model through Ollama to generate an answer.
9. **NLI Verification:** The generated answer is checked against the retrieved context to assess factual consistency and identify potential unsupported claims.
10. **Response Display:** The answer and the verification results are presented through the application interface.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | User interface |
| FastAPI | Backend API development |
| LangChain | RAG workflow and language-model integration |
| ChromaDB | Vector storage and similarity search |
| Hugging Face | Access to machine learning models and NLP tools |
| Ollama | Local language-model execution |
| Phi-3 | Language model for answer generation |
| Natural Language Inference (NLI) | Verification of answer consistency against retrieved context |

## 🏗️ System Architecture

The system follows a Retrieval-Augmented Generation architecture with an additional verification stage.

**Document Processing → Text Chunking → Embedding Generation → ChromaDB Vector Store → Relevant Context Retrieval → Phi-3 Answer Generation → NLI Verification → Final Response**

This architecture combines information retrieval, language generation, and natural language inference to improve the reliability of document-based question answering.

## 💡 Use Cases

- Question answering over academic documents.
- Extracting information from technical reports.
- Searching and understanding PDF documentation.
- Verifying AI-generated answers against a document knowledge base.
- Reducing the risk of unsupported AI-generated responses.

## 🚀 Getting Started

### Prerequisites

Before running the project, ensure that you have:

- Python installed.
- Git installed.
- Ollama installed and configured.
- The required language model downloaded.
- Access to the project's source code.

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Brundha-T/Verifact-AI.git
```

**2. Navigate to the project directory**

```bash
cd Verifact-AI
```

**3. Create and activate a virtual environment**

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

**4. Install the dependencies**

```bash
pip install -r requirements.txt
```

**5. Configure Ollama**

Install Ollama and ensure that the required Phi-3 model is available.

```bash
ollama pull phi3
```

**6. Run the application**

Check the project's entry-point files and README instructions before starting the application.

For a Streamlit entry-point file:

```bash
streamlit run app.py
```

For a FastAPI entry-point module, use the appropriate module and application variable configured in your source code.

**Note:** The exact commands for starting the application may vary depending on the project's file structure and configuration.

## 🔮 Future Enhancements

- Improve verification accuracy using more advanced NLI models.
- Provide clearer explanations for unsupported or inconsistent answers.
- Support additional document formats.
- Improve retrieval quality through better embedding models and chunking strategies.
- Add evaluation metrics for retrieval quality and hallucination detection.
- Explore deployment options for wider accessibility.

## Author

Brundha T
