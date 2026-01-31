"""
Document Processing Module.

Takes raw documents and prepares them for the search index.

THE PIPELINE:
1. LOAD: Read the file (PDF, TXT, MD, DOCX)
2. CHUNK: Split into smaller pieces
3. PREPARE: Format each chunk for indexing

WHY CHUNK?
- Embedding models have a token limit (~8000 tokens)
- Smaller chunks = more precise search results
- You want to find the EXACT paragraph that answers a question,
  not return an entire 50-page document

CHUNKING STRATEGY:
We use "recursive" chunking:
1. Try to split on paragraphs (\\n\\n)
2. If a paragraph is too big, split on sentences
3. Each chunk overlaps slightly with the next one
   (so we don't cut a thought in half)
"""

import hashlib
import re
from pathlib import Path


def load_text_file(path: str | Path) -> str:
    """Load a plain text or markdown file."""
    path = Path(path)
    return path.read_text(encoding="utf-8")


def load_pdf(path: str | Path) -> list[dict]:
    """
    Load a PDF file, returning text per page.
    
    Returns:
        List of dicts: [{"text": "...", "page": 1}, ...]
    """
    from pypdf import PdfReader
    
    reader = PdfReader(str(path))
    pages = []
    
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "page": i})
    
    return pages


def load_docx(path: str | Path) -> str:
    """Load a DOCX file."""
    from docx import Document
    
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def load_document(path: str | Path) -> list[dict]:
    """
    Load any supported document.
    
    Returns:
        List of dicts with "text", "source", and "page" keys
    """
    path = Path(path)
    suffix = path.suffix.lower()
    
    if suffix == ".pdf":
        pages = load_pdf(path)
        return [
            {"text": p["text"], "source": path.name, "page": p["page"]}
            for p in pages
        ]
    
    elif suffix == ".docx":
        text = load_docx(path)
        return [{"text": text, "source": path.name, "page": 0}]
    
    elif suffix in {".txt", ".md", ".markdown"}:
        text = load_text_file(path)
        return [{"text": text, "source": path.name, "page": 0}]
    
    else:
        print(f"⚠️ Unsupported file type: {suffix}")
        return []


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Uses recursive strategy:
    1. Split on paragraph breaks (\\n\\n)
    2. If paragraphs are too long, split on sentences
    3. Merge small chunks together until they hit the target size
    
    Args:
        text: The full text to chunk
        chunk_size: Target size in characters (not tokens)
        chunk_overlap: How many characters to overlap
        
    Returns:
        List of chunk strings
        
    Example:
        text = "Paragraph 1.\\n\\nParagraph 2.\\n\\nParagraph 3."
        chunks = chunk_text(text, chunk_size=100)
        # ["Paragraph 1.", "Paragraph 2.", "Paragraph 3."]
    """
    if not text or not text.strip():
        return []
    
    # Step 1: Split into paragraphs
    paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # Step 2: Split long paragraphs into sentences
    pieces = []
    for para in paragraphs:
        if len(para) > chunk_size:
            # Split on sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', para)
            pieces.extend(sentences)
        else:
            pieces.append(para)
    
    # Step 3: Merge small pieces into chunks of target size
    chunks = []
    current_chunk = ""
    
    for piece in pieces:
        # If adding this piece would exceed chunk_size, save current chunk
        if len(current_chunk) + len(piece) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Keep overlap from end of current chunk
            if chunk_overlap > 0:
                current_chunk = current_chunk[-chunk_overlap:] + "\n\n" + piece
            else:
                current_chunk = piece
        else:
            if current_chunk:
                current_chunk += "\n\n" + piece
            else:
                current_chunk = piece
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def process_document(
    path: str | Path,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    """
    Complete document processing: load → chunk → prepare for indexing.
    
    This is the main function you'll call.
    
    Args:
        path: Path to the document
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dicts ready for index_documents()
        
    Example:
        chunks = process_document("./docs/thesis.pdf")
        # [
        #   {"id": "abc123_0", "content": "...", "source": "thesis.pdf", "page": 1, "chunk_index": 0},
        #   {"id": "abc123_1", "content": "...", "source": "thesis.pdf", "page": 1, "chunk_index": 1},
        #   ...
        # ]
    """
    path = Path(path)
    print(f"📄 Processing: {path.name}")
    
    # Load document
    doc_parts = load_document(path)
    
    if not doc_parts:
        print(f"  ⚠️ No text extracted from {path.name}")
        return []
    
    # Chunk each part
    all_chunks = []
    chunk_counter = 0
    
    for part in doc_parts:
        text = part["text"]
        source = part["source"]
        page = part["page"]
        
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        
        for chunk_text_content in chunks:
            # Create a unique ID using hash
            hash_input = f"{source}:{page}:{chunk_counter}:{chunk_text_content[:100]}"
            chunk_id = hashlib.md5(hash_input.encode()).hexdigest()[:16]
            
            all_chunks.append({
                "id": chunk_id,
                "content": chunk_text_content,
                "source": source,
                "page": page,
                "chunk_index": chunk_counter,
            })
            chunk_counter += 1
    
    print(f"  ✅ Created {len(all_chunks)} chunks from {path.name}")
    return all_chunks


def process_directory(
    directory: str | Path,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    """
    Process all supported documents in a directory.
    
    Args:
        directory: Path to the directory
        
    Returns:
        All chunks from all documents
    """
    directory = Path(directory)
    
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    supported = {".pdf", ".txt", ".md", ".markdown", ".docx"}
    all_chunks = []
    
    for file_path in sorted(directory.iterdir()):
        if file_path.suffix.lower() in supported:
            chunks = process_document(file_path, chunk_size, chunk_overlap)
            all_chunks.extend(chunks)
    
    print(f"\n📊 Total: {len(all_chunks)} chunks from {directory}")
    return all_chunks


# Quick test
if __name__ == "__main__":
    # Test chunking
    sample_text = """
Machine learning is a subset of artificial intelligence. It enables systems to learn from data.

Deep learning uses neural networks with many layers. These networks can learn complex patterns from large amounts of data. They are particularly good at tasks like image recognition and natural language processing.

Natural language processing focuses on understanding and generating human language. It combines linguistics with machine learning to create systems that can read, understand, and produce text.
    """.strip()
    
    chunks = chunk_text(sample_text, chunk_size=200, chunk_overlap=30)
    
    print(f"Split into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
        print(chunk[:150] + "..." if len(chunk) > 150 else chunk)
