# Azure AI RAG System

A production-grade Retrieval Augmented Generation system built on Azure cloud services. Upload documents, ask questions, get accurate answers grounded in your data.

## Architecture

```
User Question
     │
     ▼
┌─────────────────────┐
│  Azure OpenAI       │ ← Embedding: text-embedding-3-small
│  (Embed Query)      │    Converts question to 1536-dim vector
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Azure AI Search    │ ← Hybrid search: keyword + vector
│  (Find Relevant     │    Returns top-5 most relevant chunks
│   Document Chunks)  │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Azure OpenAI       │ ← Generation: GPT-4o-mini
│  (Generate Answer)  │    Answers using ONLY the retrieved context
└─────────────────────┘
     │
     ▼
  Answer + Sources
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
