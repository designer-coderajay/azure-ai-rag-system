"""
RAG Pipeline - The Main Orchestrator.

This ties ALL the pieces together into a simple interface:

    pipeline = RAGPipeline()
    pipeline.setup()                          # Create search index
    pipeline.ingest("./documents/")           # Load, chunk, embed, index
    answer = pipeline.query("What is ML?")    # Search + generate answer

WHAT HAPPENS WHEN YOU CALL pipeline.query():

1. Your question goes to Azure OpenAI → gets converted to 1536 numbers (embedding)
2. Those numbers go to Azure AI Search → finds the 5 most similar document chunks
3. Those chunks + your question go to GPT-4o-mini → generates an answer
4. You get back the answer + the source documents

That's the entire RAG flow. Everything else is just making each step better.
"""

from pathlib import Path
from dataclasses import dataclass

from src.config import config
from src.blob_storage import upload_file, upload_directory, list_files
from src.search_index import create_index, index_documents, search, get_index_stats
from src.azure_openai import chat_completion, chat_completion_stream
from src.document_processor import process_document, process_directory


@dataclass
class RAGResult:
    """
    The complete result of a RAG query.
    
    Contains:
    - answer: What GPT generated
    - sources: The document chunks that were used
    - question: The original question (for reference)
    """
    question: str
    answer: str
    sources: list[dict]
    
    def print_result(self):
        """Pretty print the result."""
        print(f"\n{'='*60}")
        print(f"❓ Question: {self.question}")
        print(f"{'='*60}")
        print(f"\n💡 Answer:\n{self.answer}")
        print(f"\n📚 Sources ({len(self.sources)}):")
        for i, src in enumerate(self.sources, 1):
            score = src.get('score', 0)
            source = src.get('source', 'unknown')
            page = src.get('page', '')
            print(f"   {i}. {source}" + (f" (p.{page})" if page else "") + f" [score: {score:.3f}]")
        print()


class RAGPipeline:
    """
    The main RAG pipeline.
    
    Usage:
        # Step 1: Create pipeline
        pipeline = RAGPipeline()
        
        # Step 2: Setup (creates search index - run once)
        pipeline.setup()
        
        # Step 3: Ingest documents
        pipeline.ingest("./data/sample_docs/")
        
        # Step 4: Query
        result = pipeline.query("What is machine learning?")
        result.print_result()
    """
    
    def __init__(self, top_k: int = 5):
        """
        Args:
            top_k: Number of document chunks to retrieve per query
        """
        self.top_k = top_k
        
        # Validate config
        missing = config.validate()
        if missing:
            print("⚠️ Missing Azure credentials:")
            for m in missing:
                print(f"   - {m}")
            print("💡 Copy .env.example to .env and fill in your values")
    
    def setup(self):
        """
        One-time setup: create the search index.
        
        Run this once when you start the project.
        If the index already exists, it gets updated (not destroyed).
        """
        print("🔧 Setting up search index...")
        create_index()
        print("✅ Setup complete!")
    
    def ingest(
        self,
        source: str | Path,
        upload_to_blob: bool = False,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> int:
        """
        Ingest documents into the RAG system.
        
        Steps:
        1. (Optional) Upload files to Azure Blob Storage
        2. Load and chunk the documents
        3. Compute embeddings and add to search index
        
        Args:
            source: Path to file or directory
            upload_to_blob: Also upload to Azure Blob Storage?
            chunk_size: Characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Number of chunks indexed
        """
        source = Path(source)
        
        # Optionally upload to blob storage
        if upload_to_blob:
            print("\n☁️ Uploading to Azure Blob Storage...")
            if source.is_dir():
                upload_directory(source)
            else:
                upload_file(source)
        
        # Process documents (load → chunk)
        print("\n📄 Processing documents...")
        if source.is_dir():
            chunks = process_directory(source, chunk_size, chunk_overlap)
        else:
            chunks = process_document(source, chunk_size, chunk_overlap)
        
        if not chunks:
            print("⚠️ No chunks created. Check your documents.")
            return 0
        
        # Index documents (embed → upload to search)
        print("\n🔍 Indexing in Azure AI Search...")
        count = index_documents(chunks)
        
        print(f"\n✅ Ingestion complete! {count} chunks indexed.")
        return count
    
    def query(self, question: str, top_k: int | None = None) -> RAGResult:
        """
        Ask a question and get an answer.
        
        The full RAG flow:
        1. Search for relevant chunks (Azure AI Search)
        2. Format them as context
        3. Send to GPT-4o-mini with the question
        4. Return the answer + sources
        
        Args:
            question: Your question
            top_k: Override number of chunks to retrieve
            
        Returns:
            RAGResult with answer and sources
        """
        k = top_k or self.top_k
        
        # Step 1: Search
        print(f"🔍 Searching for: {question[:50]}...")
        results = search(question, top_k=k)
        
        if not results:
            return RAGResult(
                question=question,
                answer="I couldn't find any relevant information in the indexed documents.",
                sources=[],
            )
        
        # Step 2: Format context
        context_parts = []
        for i, r in enumerate(results, 1):
            source_info = f"[Source: {r['source']}"
            if r.get('page'):
                source_info += f", Page {r['page']}"
            source_info += "]"
            
            context_parts.append(f"{source_info}\n{r['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 3: Generate answer
        print("🤖 Generating answer...")
        answer = chat_completion(question, context)
        
        return RAGResult(
            question=question,
            answer=answer,
            sources=results,
        )
    
    def query_stream(self, question: str, top_k: int | None = None):
        """
        Same as query() but streams the answer token by token.
        
        Yields:
            Individual tokens as they're generated
        """
        k = top_k or self.top_k
        
        results = search(question, top_k=k)
        
        if not results:
            yield "I couldn't find any relevant information."
            return
        
        context_parts = []
        for r in results:
            source_info = f"[Source: {r['source']}]"
            context_parts.append(f"{source_info}\n{r['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        for token in chat_completion_stream(question, context):
            yield token
    
    def search_only(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Search without generating an answer.
        
        Useful for debugging: see what chunks the search returns.
        """
        return search(query, top_k=top_k)
    
    def stats(self) -> dict:
        """Get pipeline statistics."""
        index_stats = get_index_stats()
        
        return {
            "index_name": config.search.index_name,
            "document_count": index_stats["document_count"],
            "storage_bytes": index_stats["storage_size_bytes"],
            "chat_model": config.openai.chat_deployment,
            "embedding_model": config.openai.embedding_deployment,
        }


# Quick test
if __name__ == "__main__":
    pipeline = RAGPipeline()
    
    print("\n📊 Pipeline Stats:")
    try:
        stats = pipeline.stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   Error: {e}")
        print("   💡 Make sure Azure credentials are configured in .env")
