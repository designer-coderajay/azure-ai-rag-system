#!/usr/bin/env python3
"""
Azure RAG Demo - Run This After Setting Up Azure Resources!

PREREQUISITES:
1. Azure resources created (follow SETUP_GUIDE.md)
2. .env file filled with your credentials
3. Dependencies installed: pip install -r requirements.txt

WHAT THIS DOES:
1. Creates sample documents about ML topics
2. Sets up the search index in Azure
3. Ingests the documents (chunk → embed → index)
4. Runs sample queries
5. Drops you into interactive mode
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

console = Console()


def create_sample_docs():
    """Create sample documents for the demo."""
    
    docs_dir = Path("./data/sample_docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Document 1: Machine Learning
    (docs_dir / "machine_learning.md").write_text("""# Machine Learning Fundamentals

## What is Machine Learning?

Machine learning is a subset of artificial intelligence that gives computers the ability to learn from data without being explicitly programmed. Instead of writing rules by hand, you show the system thousands of examples and it figures out the patterns itself.

## Types of Machine Learning

Supervised learning uses labeled training data where each example has an input and the correct output. The model learns to map inputs to outputs. Common examples include spam detection (input: email text, output: spam or not spam), image classification (input: image, output: cat or dog), and price prediction (input: house features, output: price).

Unsupervised learning works with data that has no labels. The algorithm finds hidden structure in the data. Clustering groups similar items together, like grouping customers by purchasing behavior. Dimensionality reduction compresses high-dimensional data into fewer dimensions while preserving important patterns.

Reinforcement learning involves an agent learning by interacting with an environment and receiving rewards or penalties. The agent learns a policy that maximizes cumulative reward. Notable successes include AlphaGo beating world champion Go players and robots learning to walk.

## Evaluation Metrics

Accuracy measures the percentage of correct predictions. However, accuracy can be misleading with imbalanced datasets. If 99% of emails are not spam, a model that always predicts "not spam" has 99% accuracy but is useless.

Precision measures how many of the positive predictions were actually correct. Recall measures how many actual positives were correctly identified. The F1 score is the harmonic mean of precision and recall, providing a balanced measure.
""")

    # Document 2: Mechanistic Interpretability
    (docs_dir / "mechanistic_interpretability.md").write_text("""# Mechanistic Interpretability

## What is Mechanistic Interpretability?

Mechanistic interpretability is the practice of reverse-engineering neural networks to understand exactly what computations they perform. Rather than treating the model as a black box, researchers open it up and study the internal mechanisms.

## Key Techniques

### Activation Patching

Activation patching is a causal intervention technique. You run the model on two different inputs and swap the internal activations at a specific layer. If the output changes, that layer was causally responsible for the difference.

For example, to test if attention head 7.3 is responsible for detecting sentiment: run a positive review through the model, save the activations of head 7.3, run a negative review, replace head 7.3's activations with the saved positive ones, and observe if the output flips from negative to positive.

### Induction Heads

Induction heads are a two-part attention mechanism that enables in-context learning. The first part (previous token head) copies information about what token preceded another token. The second part (the induction head itself) uses this to predict that when the same token appears again, the same next token will follow.

The pattern works like this: if the model sees the sequence [A][B] earlier in the text and then sees [A] again later, it predicts [B] will follow. This is the foundation of how transformers learn from context.

### Superposition

Superposition occurs when a neural network represents more features than it has dimensions in its activation space. The network encodes features along nearly orthogonal directions, allowing it to track many more concepts than its hidden dimension would suggest.

Key finding: a model with 100 dimensions can potentially represent thousands of features by using almost-orthogonal directions. This comes at the cost of interference between features, which explains why individual neurons often respond to seemingly unrelated concepts.

## Tools for Mechanistic Interpretability

TransformerLens is the primary Python library for mechanistic interpretability research. It provides hooks into every component of a transformer, allowing researchers to read, modify, and ablate activations at any point in the computation.
""")

    # Document 3: Transformer Architecture
    (docs_dir / "transformer_architecture.md").write_text("""# The Transformer Architecture

## Overview

The Transformer was introduced in 2017 in the paper "Attention Is All You Need." It replaced recurrent neural networks with a purely attention-based architecture and became the foundation for modern language models like GPT, BERT, and their successors.

## Self-Attention Mechanism

Self-attention is the core innovation. For each token in the input, the model computes how much attention to pay to every other token. This is done through three projections:

Query (Q): "What am I looking for?"
Key (K): "What do I contain?"
Value (V): "What information do I carry?"

The attention score between two tokens is computed as the dot product of the query of one token and the key of another, divided by the square root of the dimension for numerical stability. These scores are passed through softmax to create a probability distribution, then used to weight the values.

## Multi-Head Attention

Instead of computing attention once, transformers use multiple attention heads running in parallel. Each head can learn to attend to different types of relationships. One head might focus on syntactic relationships (subject-verb), another on semantic relationships (pronouns-antecedents), and another on positional patterns.

Typical modern models use 8 to 96 attention heads. The outputs of all heads are concatenated and projected back to the model dimension.

## Feed-Forward Networks

After the attention layer, each token passes through an identical feed-forward network independently. This network typically expands the dimension by 4x, applies a non-linearity (ReLU or GELU), then projects back down. Research suggests these layers store factual knowledge.

## Positional Encoding

Since attention treats the input as a set (no inherent order), positional information must be added explicitly. The original transformer used fixed sinusoidal encodings. Modern models use learned position embeddings or rotary position embeddings (RoPE), which encode relative positions through rotation matrices.

## Model Variants

GPT (decoder-only) uses causal attention where each token can only attend to previous tokens. This makes it ideal for text generation but means it cannot see future context.

BERT (encoder-only) uses bidirectional attention where each token can attend to all other tokens. This gives better understanding but makes it unsuitable for generation.

T5 (encoder-decoder) uses an encoder to process the input bidirectionally and a decoder to generate output autoregressively. This combines the strengths of both approaches.
""")

    console.print(f"[green]✅ Created 3 sample documents in {docs_dir}[/green]")
    return docs_dir


def main():
    console.print(Panel.fit(
        "[bold blue]Azure AI RAG System Demo[/bold blue]\n"
        "Retrieval Augmented Generation with Azure Services",
        border_style="blue",
    ))
    
    # Step 0: Check credentials
    console.print("\n[bold]Step 0: Checking Azure credentials...[/bold]")
    from src.config import config
    
    missing = config.validate()
    if missing:
        console.print("[red]❌ Missing credentials:[/red]")
        for m in missing:
            console.print(f"   - {m}")
        console.print("\n[yellow]💡 Copy .env.example to .env and fill in your values[/yellow]")
        console.print("[yellow]💡 Follow SETUP_GUIDE.md for Azure resource creation[/yellow]")
        return
    
    console.print("[green]✅ All credentials configured![/green]")
    
    # Step 1: Create sample documents
    console.print("\n[bold]Step 1: Creating sample documents...[/bold]")
    docs_dir = create_sample_docs()
    
    # Step 2: Setup search index
    console.print("\n[bold]Step 2: Creating Azure AI Search index...[/bold]")
    from src.pipeline import RAGPipeline
    
    pipeline = RAGPipeline(top_k=5)
    
    try:
        pipeline.setup()
    except Exception as e:
        console.print(f"[red]❌ Index creation failed: {e}[/red]")
        return
    
    # Step 3: Ingest documents
    console.print("\n[bold]Step 3: Ingesting documents...[/bold]")
    console.print("  This will: load files → chunk → embed → index in Azure")
    
    try:
        count = pipeline.ingest(docs_dir, upload_to_blob=True)
        console.print(f"[green]✅ Ingested {count} chunks![/green]")
    except Exception as e:
        console.print(f"[red]❌ Ingestion failed: {e}[/red]")
        return
    
    # Step 4: Run sample queries
    console.print("\n[bold]Step 4: Running sample queries...[/bold]")
    
    questions = [
        "What is activation patching and how does it work?",
        "Explain the difference between supervised and unsupervised learning.",
        "How does multi-head attention work in transformers?",
        "What is superposition in neural networks?",
    ]
    
    for question in questions:
        try:
            result = pipeline.query(question)
            result.print_result()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    # Step 5: Interactive mode
    console.print(f"\n{'='*60}")
    console.print("[bold]Interactive Mode[/bold] — type your questions!")
    console.print("Type 'quit' to exit, 'stats' for pipeline info")
    console.print(f"{'='*60}")
    
    while True:
        try:
            question = input("\n❓ You: ").strip()
            
            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                break
            if question.lower() == "stats":
                stats = pipeline.stats()
                for k, v in stats.items():
                    console.print(f"  {k}: {v}")
                continue
            
            result = pipeline.query(question)
            result.print_result()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    console.print("\n[bold]Done! 🎉[/bold]")


if __name__ == "__main__":
    main()
