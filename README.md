# Azure AI RAG System

A production-grade Retrieval Augmented Generation system built on Azure cloud services. Upload documents, ask questions, get accurate answers grounded in your data.

## Architecture

```
## Deep Dive Architecture: Ingestion to Generation

A robust RAG system operates in two distinct phases: **Data Ingestion** (preparing the knowledge base) and **Runtime Generation** (handling user queries). 

```text
========================================================================
PHASE 1: DATA INGESTION (Offline Processing)
========================================================================
[Raw Documents] (PDFs, TXT, Word)
      │
      ▼
[Azure Blob Storage]     <- Safe, scalable persistent storage
      │
      ▼
[Document Processor]     <- Extracts raw text, normalizes formatting
      │
      ▼
[Semantic Splitter]      <- Chunks text (e.g., 1000 tokens, 200 overlap)
      │                     Preserves context boundaries
      ▼
[Azure OpenAI]           <- text-embedding-3-small
      │                     Converts each text chunk into a 1536-dim vector
      ▼
[Azure AI Search]        <- Stores Vectors + BM25 Keyword Index
========================================================================

========================================================================
PHASE 2: RETRIEVAL & GENERATION (Runtime Execution)
========================================================================
[User Query]             <- e.g., "What is the company policy on remote work?"
      │
      ▼
[Azure OpenAI]           <- Embeds the user query into a 1536-dim vector
      │                     using the exact same embedding model
      ▼
[Azure AI Search]        <- Executes Hybrid Search
      │                     Cross-references query vector & keyword matches
      ▼
[Retrieved Context]      <- Returns the Top-5 most relevant document chunks
      │                     along with metadata (filenames, page numbers)
      ▼
[Prompt Assembler]       <- Constructs the strict prompt:
      │                     (System Instructions + Retrieved Context + Query)
      ▼
[Azure OpenAI]           <- GPT-4o-mini evaluates the prompt
      │                     Generates answer strictly using provided context
      ▼
[Final Output]           <- Streams answer to UI (Streamlit)
                            Appends accurate source citations
========================================================================
```

## Azure Services Used

| Service                | Purpose                        | Tier         | AI-102 Topic            |
| ---------------------- | ------------------------------ | ------------ | ----------------------- |
| **Azure OpenAI**       | Embeddings + Chat generation   | Standard S0  | Generative AI solutions |
| **Azure AI Search**    | Vector + keyword hybrid search | Free/Basic   | Knowledge mining        |
| **Azure Blob Storage** | Document storage               | Standard LRS | Data integration        |
| **Azure AI Foundry**   | Resource orchestration         | N/A          | AI platform management  |

## Quick Start

### 1. Azure Setup

Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step Azure resource creation.

### 2. Local Setup

```bash
cd azure-ai-rag-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Then fill in your Azure credentials
```

### 3. Run Demo

```bash
python demo.py
```

### 4. Web UI

```bash
streamlit run app.py
```

## Project Structure

```
project1-azure-rag/
├── SETUP_GUIDE.md          # Step-by-step Azure Portal instructions
├── .env.example            # Template for Azure credentials
├── requirements.txt        # Python dependencies
├── demo.py                 # Demo script (run this first!)
├── app.py                  # Streamlit web interface
├── src/
│   ├── config.py           # Configuration loader
│   ├── blob_storage.py     # Azure Blob Storage operations
│   ├── azure_openai.py     # Embeddings + Chat generation
│   ├── search_index.py     # Azure AI Search (index + search)
│   ├── document_processor.py  # Load + chunk documents
│   └── pipeline.py         # Main orchestrator (ties everything together)
└── data/
    └── sample_docs/        # Sample documents for testing
```

## Key Features

- **Hybrid Search**: Combines keyword matching with vector similarity for best results
- **Document Chunking**: Recursive strategy that preserves semantic coherence
- **Streaming Responses**: Token-by-token generation like ChatGPT
- **Source Attribution**: Every answer cites which documents were used
- **Web Interface**: Upload documents and ask questions through Streamlit

## API Usage

```python
from src.pipeline import RAGPipeline

pipeline = RAGPipeline()
pipeline.setup()                            # Create search index (once)
pipeline.ingest("./documents/")             # Ingest documents
result = pipeline.query("What is ML?")      # Ask questions
print(result.answer)
```

## Skills Demonstrated

- Azure OpenAI Service provisioning and model deployment
- Azure AI Search index creation with vector search
- Azure Blob Storage integration
- Azure AI Foundry project management
- Hybrid search (BM25 + vector) implementation
- RAG pipeline architecture and prompt engineering
- Production patterns: streaming, error handling, configuration

## License

MIT
