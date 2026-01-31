"""
Azure AI Search Module.

This is the BRAIN of the RAG system. It stores document chunks as searchable vectors
and finds the most relevant ones when you ask a question.

SIMPLE ANALOGY:
Think of a library:
- INDEX = The library's catalog system
- DOCUMENTS = Individual catalog cards (each chunk of text)
- SEARCH = Finding the right books by looking through the catalog
- VECTOR SEARCH = Finding books by MEANING, not just exact words

WHAT THIS MODULE DOES:
1. create_index() - Sets up the catalog system (run once)
2. index_documents() - Adds document chunks to the catalog
3. search() - Finds relevant chunks for a question
4. hybrid_search() - Combines keyword + meaning search (best results)

VECTOR SEARCH EXPLAINED:
- Each document chunk gets converted to a list of 1536 numbers (embedding)
- Your question also gets converted to 1536 numbers
- Azure AI Search finds chunks whose numbers are closest to your question's numbers
- "Closest numbers" = "Most similar meaning"
"""

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchIndex,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

from src.config import config
from src.azure_openai import get_embedding, get_embeddings_batch


def get_index_client() -> SearchIndexClient:
    """
    Client for MANAGING indexes (create, delete, list).
    
    Think of this as the library administrator who sets up
    the cataloging system.
    """
    return SearchIndexClient(
        endpoint=config.search.endpoint,
        credential=AzureKeyCredential(config.search.key),
    )


def get_search_client() -> SearchClient:
    """
    Client for SEARCHING within an index.
    
    Think of this as the librarian who helps you find books.
    """
    return SearchClient(
        endpoint=config.search.endpoint,
        index_name=config.search.index_name,
        credential=AzureKeyCredential(config.search.key),
    )


def create_index():
    """
    Create the search index with vector search support.
    
    THIS RUNS ONCE to set up the "catalog system."
    
    The index defines:
    - What fields each document has (id, content, source, etc.)
    - Which fields are searchable by keywords
    - Which fields support vector search
    - How vector search works (algorithm, dimensions)
    
    IMPORTANT CONCEPTS:
    - SearchableField: Can be searched with keywords (like ctrl+F)
    - SimpleField: Stored but not searched (like metadata)
    - Vector field: Searched by meaning (embedding similarity)
    """
    index_client = get_index_client()
    
    # ---- Define the fields (columns in the catalog) ----
    fields = [
        # Unique ID for each chunk (like a catalog card number)
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,           # This is the primary key
            filterable=True,    # Can filter by ID
        ),
        
        # The actual text content of the chunk
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            # searchable=True by default for SearchableField
            # This means keyword search works on this field
        ),
        
        # Which file this chunk came from
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,    # Can filter by source file
            facetable=True,     # Can group results by source
        ),
        
        # Page number (for PDFs)
        SimpleField(
            name="page",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        
        # Position of this chunk in the document
        SimpleField(
            name="chunk_index",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        
        # The embedding vector (1536 numbers)
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            # Vector search configuration:
            vector_search_dimensions=1536,  # text-embedding-3-small outputs 1536 dims
            vector_search_profile_name="my-vector-profile",
        ),
    ]
    
    # ---- Configure vector search algorithm ----
    # HNSW = Hierarchical Navigable Small World
    # It's like a network of shortcuts that lets you quickly find similar vectors
    # Think of it like an expressway system vs checking every single road
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="my-hnsw-config",
                # These are sensible defaults:
                # m=4: each node connects to 4 neighbors
                # efConstruction=400: thoroughness when building the index
                # efSearch=500: thoroughness when searching
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="my-vector-profile",
                algorithm_configuration_name="my-hnsw-config",
            ),
        ],
    )
    
    # ---- Configure semantic search (optional but powerful) ----
    # Semantic search re-reads top results with a language model
    # to better understand meaning. It's like having a librarian
    # double-check the results and re-rank them.
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content")]
        ),
    )
    
    semantic_search = SemanticSearch(configurations=[semantic_config])
    
    # ---- Create the index ----
    index = SearchIndex(
        name=config.search.index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )
    
    # Create or update the index
    result = index_client.create_or_update_index(index)
    print(f"✅ Index '{result.name}' created/updated successfully!")
    return result


def delete_index():
    """Delete the index (removes all data!)."""
    index_client = get_index_client()
    index_client.delete_index(config.search.index_name)
    print(f"🗑️ Index '{config.search.index_name}' deleted")


def index_documents(chunks: list[dict]) -> int:
    """
    Add document chunks to the search index.
    
    Each chunk needs:
    - id: Unique identifier
    - content: The text
    - source: Where it came from
    - page: Page number (0 if not applicable)
    - chunk_index: Position in document
    
    This function also computes embeddings for each chunk.
    
    Args:
        chunks: List of dicts with the above fields
        
    Returns:
        Number of chunks indexed
        
    Example:
        chunks = [
            {"id": "doc1_chunk0", "content": "ML is AI...", "source": "ml.pdf", "page": 1, "chunk_index": 0},
            {"id": "doc1_chunk1", "content": "Deep learning...", "source": "ml.pdf", "page": 1, "chunk_index": 1},
        ]
        index_documents(chunks)
    """
    if not chunks:
        print("⚠️ No chunks to index")
        return 0
    
    search_client = get_search_client()
    
    # Step 1: Compute embeddings for all chunks
    print(f"🧮 Computing embeddings for {len(chunks)} chunks...")
    texts = [c["content"] for c in chunks]
    embeddings = get_embeddings_batch(texts)
    
    # Step 2: Add embeddings to each chunk
    documents = []
    for chunk, embedding in zip(chunks, embeddings):
        doc = {
            "id": chunk["id"],
            "content": chunk["content"],
            "source": chunk.get("source", "unknown"),
            "page": chunk.get("page", 0),
            "chunk_index": chunk.get("chunk_index", 0),
            "content_vector": embedding,  # The 1536-number vector
        }
        documents.append(doc)
    
    # Step 3: Upload to Azure AI Search (in batches of 1000)
    print(f"📤 Uploading {len(documents)} documents to index...")
    
    batch_size = 1000
    total_uploaded = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = search_client.upload_documents(documents=batch)
        
        # Count successes
        succeeded = sum(1 for r in result if r.succeeded)
        total_uploaded += succeeded
    
    print(f"✅ Indexed {total_uploaded}/{len(documents)} chunks successfully!")
    return total_uploaded


def search(
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
) -> list[dict]:
    """
    Search for relevant document chunks using HYBRID search.
    
    HYBRID = keyword search + vector search combined.
    
    Why hybrid?
    - Keyword search finds exact matches: "GPT-4" matches "GPT-4"
    - Vector search finds meaning: "car" matches "automobile"
    - Together = best of both worlds
    
    Args:
        query: The question or search query
        top_k: How many results to return
        source_filter: Only search in a specific document (optional)
        
    Returns:
        List of dicts with content, source, score
    """
    search_client = get_search_client()
    
    # Step 1: Convert query to embedding (for vector search)
    query_embedding = get_embedding(query)
    
    # Step 2: Create vector query
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    )
    
    # Step 3: Build filter (optional)
    filter_expr = None
    if source_filter:
        filter_expr = f"source eq '{source_filter}'"
    
    # Step 4: Execute hybrid search
    # search_text = keyword search
    # vector_queries = vector search
    # Both run simultaneously, results are combined
    results = search_client.search(
        search_text=query,              # Keyword search
        vector_queries=[vector_query],   # Vector search
        top=top_k,
        filter=filter_expr,
        select=["id", "content", "source", "page", "chunk_index"],
    )
    
    # Step 5: Format results
    search_results = []
    for result in results:
        search_results.append({
            "id": result["id"],
            "content": result["content"],
            "source": result["source"],
            "page": result.get("page", 0),
            "score": result["@search.score"],
        })
    
    return search_results


def vector_search_only(query: str, top_k: int = 5) -> list[dict]:
    """
    Pure vector search (no keywords).
    
    Use this when you want purely semantic matching.
    Good for questions that use very different words than the documents.
    """
    search_client = get_search_client()
    
    query_embedding = get_embedding(query)
    
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    )
    
    results = search_client.search(
        search_text=None,               # No keyword search
        vector_queries=[vector_query],
        top=top_k,
        select=["id", "content", "source", "page"],
    )
    
    return [
        {
            "id": r["id"],
            "content": r["content"],
            "source": r["source"],
            "page": r.get("page", 0),
            "score": r["@search.score"],
        }
        for r in results
    ]


def get_index_stats() -> dict:
    """Get statistics about the index."""
    index_client = get_index_client()
    
    try:
        stats = index_client.get_index_statistics(config.search.index_name)
        return {
            "document_count": stats.document_count,
            "storage_size_bytes": stats.storage_size,
        }
    except Exception:
        return {"document_count": 0, "storage_size_bytes": 0}


# Quick test
if __name__ == "__main__":
    print("Testing Azure AI Search...")
    
    try:
        # Check if index exists
        stats = get_index_stats()
        print(f"📊 Index stats: {stats['document_count']} documents")
        
        # Try a search
        if stats["document_count"] > 0:
            results = search("test query", top_k=3)
            print(f"🔍 Search returned {len(results)} results")
            for r in results:
                print(f"   - [{r['score']:.3f}] {r['content'][:80]}...")
        else:
            print("📭 Index is empty. Run the pipeline to add documents!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY in .env")
        print("💡 Run create_index() first if the index doesn't exist")
