"""
Streamlit Web UI for Azure RAG System.

A user-friendly web interface for:
- Uploading documents
- Asking questions
- Viewing search results
- Managing the pipeline

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(page_title="Azure RAG System", page_icon="🔍", layout="wide")


@st.cache_resource
def get_pipeline():
    """Initialize pipeline once."""
    from src.pipeline import RAGPipeline
    return RAGPipeline(top_k=5)


def main():
    st.title("🔍 Azure AI RAG System")
    st.caption("Ask questions about your documents using Azure OpenAI + AI Search")
    
    pipeline = get_pipeline()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        try:
            stats = pipeline.stats()
            st.metric("Indexed Documents", stats["document_count"])
            st.caption(f"Model: {stats['chat_model']}")
            st.caption(f"Index: {stats['index_name']}")
        except Exception as e:
            st.error(f"Connection error: {e}")
        
        st.divider()
        
        # Setup button
        if st.button("🔧 Setup Index"):
            with st.spinner("Creating index..."):
                try:
                    pipeline.setup()
                    st.success("Index created!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # File upload
        st.subheader("📁 Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
        )
        
        if uploaded_files and st.button("📤 Ingest Files"):
            temp_dir = Path("./data/uploads")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            for f in uploaded_files:
                temp_path = temp_dir / f.name
                temp_path.write_bytes(f.read())
            
            with st.spinner("Processing..."):
                try:
                    count = pipeline.ingest(temp_dir, upload_to_blob=True)
                    st.success(f"Ingested {count} chunks!")
                except Exception as e:
                    st.error(f"Error: {e}")
            
            # Cleanup
            for f in temp_dir.iterdir():
                f.unlink()
        
        # Quick ingest sample docs
        if st.button("📝 Load Sample Docs"):
            from demo import create_sample_docs
            docs_dir = create_sample_docs()
            with st.spinner("Ingesting sample docs..."):
                try:
                    count = pipeline.ingest(docs_dir)
                    st.success(f"Ingested {count} chunks!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Main content - tabs
    tab1, tab2 = st.tabs(["💬 Ask Questions", "🔎 Search"])
    
    with tab1:
        question = st.text_area("Your question:", height=80, placeholder="What is activation patching?")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            top_k = st.number_input("Sources", 1, 10, 5)
        
        if st.button("Ask", type="primary", disabled=not question):
            with st.spinner("Thinking..."):
                try:
                    result = pipeline.query(question, top_k=top_k)
                    
                    st.markdown("### Answer")
                    st.markdown(result.answer)
                    
                    with st.expander(f"📚 Sources ({len(result.sources)})"):
                        for i, src in enumerate(result.sources, 1):
                            score = src.get('score', 0)
                            source = src.get('source', 'unknown')
                            st.markdown(f"**{i}. {source}** (score: {score:.3f})")
                            st.text(src['content'][:300] + "...")
                            st.divider()
                            
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        search_query = st.text_input("Search query:")
        
        if search_query:
            try:
                results = pipeline.search_only(search_query, top_k=10)
                
                for r in results:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{r['source']}**")
                        with col2:
                            st.metric("Score", f"{r['score']:.3f}")
                        st.text(r['content'][:400])
                        st.divider()
            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
