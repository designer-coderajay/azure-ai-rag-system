"""
Azure OpenAI Module.

This connects to Azure's hosted OpenAI models for two things:
1. EMBEDDINGS - Converting text to numbers (vectors) that capture meaning
2. CHAT - Generating answers using GPT-4o-mini

SIMPLE ANALOGY:
- Embeddings = Converting words into coordinates on a map
  "cat" → [0.2, 0.8, 0.1, ...]  (close to "dog", far from "car")
- Chat = Asking a smart assistant a question with context

HOW AZURE OPENAI DIFFERS FROM REGULAR OPENAI:
- Regular OpenAI: You call api.openai.com with an OpenAI API key
- Azure OpenAI: You call YOUR-NAME.openai.azure.com with an Azure key
- Same models, different hosting. Azure gives you enterprise security,
  regional deployment, and content filtering.
"""

from openai import AzureOpenAI
from src.config import config


def get_openai_client() -> AzureOpenAI:
    """
    Create a connection to Azure OpenAI.
    
    This client object handles authentication and API calls.
    You create it once, then use it for all requests.
    """
    client = AzureOpenAI(
        azure_endpoint=config.openai.endpoint,
        api_key=config.openai.key,
        api_version=config.openai.api_version,
    )
    return client


def get_embedding(text: str) -> list[float]:
    """
    Convert a single text into an embedding vector.
    
    WHAT HAPPENS:
    1. We send the text to Azure OpenAI's embedding model
    2. The model reads the text and understands its meaning
    3. It returns a list of 1536 numbers (the embedding)
    4. Similar texts will have similar numbers
    
    Args:
        text: Any string (sentence, paragraph, document chunk)
        
    Returns:
        A list of 1536 floats (the embedding vector)
        
    Example:
        vec = get_embedding("machine learning is AI")
        # vec = [0.023, -0.045, 0.012, ...]  (1536 numbers)
    """
    client = get_openai_client()
    
    response = client.embeddings.create(
        input=text,
        model=config.openai.embedding_deployment,  # "text-embedding-3-small"
    )
    
    # The response contains the embedding in response.data[0].embedding
    return response.data[0].embedding


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple texts into embeddings at once (faster than one by one).
    
    Azure OpenAI can process up to 16 texts in a single API call.
    We batch them for efficiency.
    
    Args:
        texts: List of strings
        
    Returns:
        List of embedding vectors (same order as input)
    """
    client = get_openai_client()
    
    all_embeddings = []
    
    # Process in batches of 16 (Azure limit)
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        response = client.embeddings.create(
            input=batch,
            model=config.openai.embedding_deployment,
        )
        
        # Extract embeddings in order
        for item in response.data:
            all_embeddings.append(item.embedding)
    
    return all_embeddings


def chat_completion(
    question: str,
    context: str,
    system_prompt: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> str:
    """
    Generate an answer using GPT-4o-mini with context.
    
    This is the "G" (Generation) in RAG:
    1. We give GPT the retrieved context (relevant document chunks)
    2. We give it the user's question
    3. GPT reads the context and answers the question
    
    The system_prompt tells GPT to ONLY use the context.
    This prevents hallucination (making stuff up).
    
    Args:
        question: The user's question
        context: Retrieved document chunks (formatted as string)
        system_prompt: Instructions for GPT
        temperature: Creativity (0 = factual, 1 = creative)
        max_tokens: Maximum length of answer
        
    Returns:
        The generated answer as a string
    """
    client = get_openai_client()
    
    if system_prompt is None:
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- ONLY use information from the context below to answer
- If the context doesn't contain the answer, say "I don't have enough information to answer this."
- Be concise and direct
- Cite which document/section the information comes from when possible"""
    
    # Format the user message with context
    user_message = f"""Context:
{context}

---

Question: {question}

Answer:"""
    
    # Call Azure OpenAI
    response = client.chat.completions.create(
        model=config.openai.chat_deployment,  # "gpt-4o-mini"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    # Extract the answer
    # response.choices[0] = the first (and only) response
    # .message.content = the actual text
    return response.choices[0].message.content


def chat_completion_stream(
    question: str,
    context: str,
    system_prompt: str | None = None,
):
    """
    Same as chat_completion but streams tokens one by one.
    
    This makes the response appear word-by-word like ChatGPT.
    Useful for UI where you want to show progress.
    
    Yields:
        Individual tokens (words/parts of words)
    """
    client = get_openai_client()
    
    if system_prompt is None:
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Only use information from the context. If the context doesn't contain the answer, say so."""
    
    user_message = f"""Context:
{context}

---

Question: {question}

Answer:"""
    
    # stream=True makes it return tokens one at a time
    response = client.chat.completions.create(
        model=config.openai.chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=1024,
        stream=True,  # ← This is the key difference
    )
    
    # Yield each token as it arrives
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# Quick test
if __name__ == "__main__":
    print("Testing Azure OpenAI connection...")
    
    try:
        # Test embedding
        embedding = get_embedding("Hello, this is a test.")
        print(f"✅ Embedding works! Dimension: {len(embedding)}")
        
        # Test chat
        answer = chat_completion(
            question="What is 2+2?",
            context="Basic math: 2+2 equals 4.",
        )
        print(f"✅ Chat works! Answer: {answer}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in .env")
