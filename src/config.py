"""
Configuration Module.

Loads Azure credentials from .env file and provides them to all components.

WHY A SEPARATE CONFIG FILE?
- Keeps secrets out of your code
- Easy to switch between environments (dev/prod)
- One place to change all settings

HOW IT WORKS:
1. Reads .env file (python-dotenv library)
2. Creates dataclass objects with typed fields
3. Other modules import config and use the values
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


# Load .env file from project root
# This reads the file and puts values into os.environ
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class AzureOpenAIConfig:
    """
    Settings for Azure OpenAI Service.
    
    endpoint: The URL of your Azure OpenAI resource
    key: Your API key (like a password)
    api_version: Which version of the API to use
    chat_deployment: Name of your GPT model deployment
    embedding_deployment: Name of your embedding model deployment
    """
    endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key: str = os.getenv("AZURE_OPENAI_KEY", "")
    api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")


@dataclass
class AzureSearchConfig:
    """
    Settings for Azure AI Search.
    
    endpoint: URL of your search service
    key: Admin key for creating/managing indexes
    index_name: Name of the search index
    """
    endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    key: str = os.getenv("AZURE_SEARCH_KEY", "")
    index_name: str = os.getenv("AZURE_SEARCH_INDEX", "rag-index")


@dataclass 
class AzureStorageConfig:
    """
    Settings for Azure Blob Storage.
    
    connection_string: Full connection string (contains account name + key)
    container_name: Name of the blob container where documents live
    """
    connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container_name: str = os.getenv("AZURE_STORAGE_CONTAINER", "documents")


@dataclass
class AppConfig:
    """
    Master config that holds all sub-configs.
    
    Usage:
        from src.config import config
        print(config.openai.endpoint)
        print(config.search.index_name)
    """
    openai: AzureOpenAIConfig = None
    search: AzureSearchConfig = None
    storage: AzureStorageConfig = None
    
    def __post_init__(self):
        self.openai = AzureOpenAIConfig()
        self.search = AzureSearchConfig()
        self.storage = AzureStorageConfig()
    
    def validate(self) -> list[str]:
        """
        Check which credentials are missing.
        Returns list of missing items.
        """
        missing = []
        
        if not self.openai.endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.openai.key:
            missing.append("AZURE_OPENAI_KEY")
        if not self.search.endpoint:
            missing.append("AZURE_SEARCH_ENDPOINT")
        if not self.search.key:
            missing.append("AZURE_SEARCH_KEY")
        if not self.storage.connection_string:
            missing.append("AZURE_STORAGE_CONNECTION_STRING")
        
        return missing
    
    def print_status(self):
        """Print which services are configured."""
        missing = self.validate()
        
        if not missing:
            print("✅ All Azure credentials configured!")
        else:
            print("❌ Missing credentials:")
            for m in missing:
                print(f"   - {m}")
            print("\n💡 Copy .env.example to .env and fill in your values")


# Create a global config instance
# Other files just do: from src.config import config
config = AppConfig()


if __name__ == "__main__":
    config.print_status()
