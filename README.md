<div align="center">

# Azure AI RAG System

**Ask questions about your own documents. Get answers that cite their source.**

Hybrid search (keywords + vectors) on Azure AI Search, answers from Azure OpenAI, documents in Azure Blob Storage.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-0078D4) ![Azure AI Search](https://img.shields.io/badge/Azure-AI%20Search-0078D4) ![License](https://img.shields.io/badge/license-MIT-green)

[Quick start](#quick-start) · [How it works](#how-it-works-start-to-finish) · [Configuration](#configuration) · [API](#api-usage) · [Limitations](#limitations)

</div>

---

## The problem and the approach

A language model on its own does not know your company's documents, so it may answer confidently and wrongly.

This project keeps **knowledge** and **reasoning** apart:

1. Your documents are split into chunks and stored in **Azure AI Search**.
2. For each question, the search service finds the few chunks that best match it.
3. Only those chunks are sent to **Azure OpenAI**, with an instruction to answer from them alone, or to say it doesn't have enough information.
4. The answer comes back with the source file (and page, for PDFs) of every chunk used.

> **What this does and does not guarantee.** The prompt tells the model to use only the retrieved text, and the temperature is low (0.1), which makes invented answers much less likely. It does not make them impossible: the model can still misread a chunk, and retrieval can miss the right one. Check the cited sources for anything important.

Because documents stay in your own Azure resources, your data is not sent to a third-party service beyond Azure. Check your tenant's Azure OpenAI data-handling and retention settings against your own policy; this repo does not configure them.

## The whole system in one picture

```mermaid
flowchart LR
    subgraph IN["1 · INGEST (once per document)"]
        direction TB
        D["Your files<br/>PDF · DOCX · TXT"] --> P["Load text<br/>document_processor.py"]
        P --> C["Chunk<br/>500 chars, 50 overlap"]
        C --> E["Embed each chunk<br/>text-embedding-3-small<br/>1536 numbers"]
        E --> I[("Azure AI Search<br/>keyword index + vector index")]
        D -. "optional copy" .-> B[("Azure Blob Storage")]
    end

    subgraph ASK["2 · ASK (every question)"]
        direction TB
        Q["Question"] --> QE["Embed the question<br/>same model"]
        QE --> H["Hybrid search<br/>keywords + vectors<br/>top 5 chunks"]
        H --> PR["Build prompt<br/>rules + chunks + question"]
        PR --> G["Chat model<br/>gpt-4o-mini"]
        G --> A["Answer + sources"]
    end

    I ==> H

    classDef store fill:#e8f1ff,stroke:#2b5fd9,color:#111;
    classDef step fill:#f6f6f6,stroke:#888,color:#111;
    classDef out fill:#e9f8ec,stroke:#2e8b57,color:#111;
    class I,B store;
    class D,P,C,E,Q,QE,H,PR,G step;
    class A out;
```

## How it works, start to finish

### Phase 1 · Ingest: turn documents into something searchable

```mermaid
sequenceDiagram
    autonumber
    participant U as You (demo.py or app.py)
    participant PL as RAGPipeline
    participant BL as Blob Storage
    participant DP as document_processor
    participant AO as Azure OpenAI
    participant AS as Azure AI Search
    U->>PL: ingest(folder, upload_to_blob=True)
    opt upload_to_blob is True
        PL->>BL: Upload the original files
    end
    PL->>DP: Load and chunk every file
    DP-->>PL: Chunks with source, page, chunk_index
    PL->>AO: Embed the chunk texts (batched)
    AO-->>PL: One 1536-number vector per chunk
    PL->>AS: Upload chunks plus their vectors
    AS-->>U: Count of chunks indexed
```

| Step | What happens | Code |
|---|---|---|
| **1. Create the index** (once) | Defines the fields (`id`, `content`, `source`, `page`, `chunk_index`) and a 1536-dimension vector field searched with HNSW. | `search_index.create_index()` via `pipeline.setup()` |
| **2. Back up originals** (optional) | Copies the files to a Blob container. Search does not read from Blob; this is storage only. | `blob_storage.upload_directory()` |
| **3. Load text** | Reads `.txt`, `.pdf` (page by page) and `.docx`. | `document_processor.load_document()` |
| **4. Chunk** | Splits on blank lines, then sentences for long paragraphs, then merges pieces up to **500 characters** with a **50-character** overlap, so a fact is less likely to be cut in half. | `document_processor.chunk_text()` |
| **5. Embed** | Each chunk becomes a vector with `text-embedding-3-small`. Chunks with similar meaning get similar vectors. | `azure_openai.get_embeddings_batch()` |
| **6. Index** | Text and vector are stored together, so one query can use both. | `search_index.index_documents()` |

### Phase 2 · Ask: find the evidence, then answer

```mermaid
sequenceDiagram
    autonumber
    participant U as You
    participant PL as RAGPipeline.query
    participant AO as Azure OpenAI
    participant AS as Azure AI Search
    U->>PL: "What is the remote work policy?"
    PL->>AO: Embed the question
    AO-->>PL: Question vector
    PL->>AS: Keyword query + vector query together, top 5
    AS-->>PL: 5 chunks with source and page
    alt nothing found
        PL-->>U: "I couldn't find any relevant information..."
    else chunks found
        PL->>PL: Build context: [Source: file, Page n] + text, per chunk
        PL->>AO: System rules + context + question (temperature 0.1)
        AO-->>PL: Answer based on the context
        PL-->>U: Answer + list of source chunks
    end
```

| Step | What happens | Why it matters |
|---|---|---|
| **1. Embed the question** | Same embedding model as ingestion. | Question and chunks must live in the same "meaning space" to be comparable. |
| **2. Hybrid search** | One request carries both a keyword query (`search_text`) and a vector query. Azure AI Search runs both and merges the rankings. | Keywords catch exact terms such as names and codes; vectors catch paraphrases. Together they miss less than either alone. |
| **3. Take the top 5** | Default `top_k=5`, adjustable per call and in the web UI. | More chunks give more context but more noise and cost. |
| **4. Assemble the prompt** | Each chunk is labelled `[Source: file, Page n]` and joined with `---` separators. | The model can cite what it read. |
| **5. Generate** | `gpt-4o-mini`, temperature 0.1, max 1024 tokens. The rules say: use only the context; if the answer is not there, say "I don't have enough information to answer this."; be concise; cite the document. | Keeps answers grounded and repeatable. |
| **6. Return** | `RAGResult` holds the question, the answer and the source chunks. | Every answer can be checked against its evidence. |

## Azure services used

| Service | Role in this project | Tier used in the guide |
|---|---|---|
| **Azure OpenAI** | Embeddings (`text-embedding-3-small`) and chat (`gpt-4o-mini`) | Standard S0 |
| **Azure AI Search** | Stores chunks; runs hybrid keyword + vector search | Free or Basic |
| **Azure Blob Storage** | Optional copy of the original documents | Standard LRS |
| **Azure AI Foundry** | Where you organise the resources | n/a |

Pricing and free-tier limits change; check the Azure pricing pages before relying on them.

## Quick start

**1. Create the Azure resources** by following [SETUP_GUIDE.md](SETUP_GUIDE.md).

**2. Install locally**

```bash
git clone https://github.com/designer-coderajay/azure-ai-rag-system.git
cd azure-ai-rag-system
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in your Azure values
```

**3. Run the command-line demo** (creates the index, ingests sample documents, asks questions)

```bash
python demo.py
```

**4. Or use the web interface**

```bash
streamlit run app.py
```

In the sidebar: **Setup Index** once, then upload files and press **Ingest Files** (or ingest the built-in samples), then ask questions in the main panel. A separate search box shows raw search results without calling the chat model.

## Configuration

Set these in `.env` (template: `.env.example`). Never commit `.env`.

| Variable | Meaning | Default in code |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI resource URL | none |
| `AZURE_OPENAI_KEY` | Its key | none |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-06-01` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Name you gave the chat deployment | `gpt-4o-mini` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Name you gave the embedding deployment | `text-embedding-3-small` |
| `AZURE_SEARCH_ENDPOINT` | Your Search service URL | none |
| `AZURE_SEARCH_KEY` | Admin key | none |
| `AZURE_SEARCH_INDEX` | Index name | `rag-index` |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob connection string | none |
| `AZURE_STORAGE_CONTAINER` | Container name | `documents` |

The index vector field is fixed at 1536 dimensions. If you switch to an embedding model with a different size, change `vector_search_dimensions` in `src/search_index.py` and recreate the index.

## Project structure

```
azure-ai-rag-system/
├── app.py                    # Streamlit web interface
├── demo.py                   # Command-line walkthrough (run this first)
├── requirements.txt          # Python dependencies
├── .env.example              # Template for Azure credentials
├── SETUP_GUIDE.md            # Step-by-step Azure Portal instructions
└── src/
    ├── config.py             # Loads settings from .env
    ├── document_processor.py # Load PDF/DOCX/TXT and split into chunks
    ├── azure_openai.py       # Embeddings, chat, streaming chat, the system prompt
    ├── search_index.py       # Create index, upload chunks, hybrid and vector search
    ├── blob_storage.py       # Upload, list, download, delete files in Blob
    └── pipeline.py           # RAGPipeline: ties everything together
```

Sample documents are generated at run time under `data/sample_docs/` by `demo.py` and `app.py`; that folder is not in the repository.

## API usage

```python
from src.pipeline import RAGPipeline

pipeline = RAGPipeline(top_k=5)
pipeline.setup()                                   # create the search index (once)
pipeline.ingest("./documents/")                    # load, chunk, embed, index
pipeline.ingest("./documents/", upload_to_blob=True)   # also copy originals to Blob

result = pipeline.query("What is the remote work policy?")
print(result.answer)
for s in result.sources:
    print(s["source"], s.get("page"))

for token in pipeline.query_stream("Summarise the leave policy"):
    print(token, end="", flush=True)               # token-by-token output

hits = pipeline.search_only("remote work", top_k=10)   # retrieval only, no chat model
```

`query_stream` is available in the Python API. The bundled Streamlit app calls `query`, so it shows the full answer at once.

## Limitations

- **Chunking is character-based.** Chunks target 500 characters, not tokens, and the overlap is the last 50 characters of the previous chunk, which can start mid-word. Very long tables and scanned PDFs (no text layer) are not handled well.
- **No re-ranking and no semantic ranker.** Results are the search service's merged keyword and vector ranking only.
- **Answer quality depends on retrieval.** If the right chunk is not in the top 5, the model cannot use it. Raise `top_k` or tune the chunk size.
- **Keys, not managed identity.** The code reads API keys from `.env`. `azure-identity` is in `requirements.txt`, but the shown code authenticates with keys; for production, consider managed identities and a secret store.
- **No access control per document.** Anyone who can query the index can retrieve any chunk in it.
- **Not tested here.** This README was checked against the source code, not by running the pipeline against live Azure resources.

## Skills demonstrated

Azure OpenAI deployment · Azure AI Search index design with vector search · hybrid (BM25 + vector) retrieval · Azure Blob Storage integration · RAG prompt design · streaming responses · configuration management

## License

MIT
