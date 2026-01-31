"""
Azure Blob Storage Module.

This handles uploading and downloading documents to/from Azure cloud storage.

SIMPLE ANALOGY:
- Blob Storage = USB drive in the cloud
- Container = Folder on the USB drive
- Blob = A file on the USB drive

WHAT THIS MODULE DOES:
1. upload_file() - Puts a file from your computer into Azure
2. list_files() - Shows all files in your Azure container
3. download_file() - Gets a file from Azure to your computer
4. upload_directory() - Uploads an entire folder
"""

from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContainerClient
from src.config import config


def get_container_client() -> ContainerClient:
    """
    Connect to your Azure Blob container.
    
    Think of this as "plugging in the USB drive."
    Returns a client object you use for all operations.
    """
    # BlobServiceClient = connection to the storage account
    blob_service = BlobServiceClient.from_connection_string(
        config.storage.connection_string
    )
    
    # ContainerClient = connection to a specific container (folder)
    container = blob_service.get_container_client(
        config.storage.container_name
    )
    
    # Create the container if it doesn't exist
    if not container.exists():
        container.create_container()
        print(f"📁 Created container: {config.storage.container_name}")
    
    return container


def upload_file(local_path: str | Path, blob_name: str | None = None) -> str:
    """
    Upload a single file to Azure Blob Storage.
    
    Args:
        local_path: Path to the file on your computer
        blob_name: Name in Azure (defaults to filename)
        
    Returns:
        The blob name (path in Azure)
        
    Example:
        upload_file("./docs/thesis.pdf")
        # Now thesis.pdf is in Azure!
    """
    local_path = Path(local_path)
    
    if not local_path.exists():
        raise FileNotFoundError(f"File not found: {local_path}")
    
    # Use the filename if no blob_name specified
    if blob_name is None:
        blob_name = local_path.name
    
    container = get_container_client()
    
    # Upload the file
    # open in binary mode ("rb" = read bytes)
    with open(local_path, "rb") as data:
        container.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,  # Replace if already exists
        )
    
    print(f"✅ Uploaded: {local_path.name} → {blob_name}")
    return blob_name


def upload_directory(local_dir: str | Path) -> list[str]:
    """
    Upload all supported files from a directory.
    
    Supported: .pdf, .txt, .md, .docx
    
    Returns:
        List of uploaded blob names
    """
    local_dir = Path(local_dir)
    
    if not local_dir.is_dir():
        raise ValueError(f"Not a directory: {local_dir}")
    
    supported = {".pdf", ".txt", ".md", ".docx", ".markdown"}
    uploaded = []
    
    for file_path in local_dir.iterdir():
        if file_path.suffix.lower() in supported:
            blob_name = upload_file(file_path)
            uploaded.append(blob_name)
    
    print(f"\n📊 Uploaded {len(uploaded)} files total")
    return uploaded


def list_files() -> list[dict]:
    """
    List all files in your Azure container.
    
    Returns:
        List of dicts with file info (name, size, last_modified)
    """
    container = get_container_client()
    
    files = []
    for blob in container.list_blobs():
        files.append({
            "name": blob.name,
            "size_kb": round(blob.size / 1024, 1),
            "last_modified": str(blob.last_modified),
        })
    
    return files


def download_file(blob_name: str, local_path: str | Path) -> Path:
    """
    Download a file from Azure to your computer.
    
    Args:
        blob_name: Name of the file in Azure
        local_path: Where to save it on your computer
        
    Returns:
        Path to the downloaded file
    """
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    container = get_container_client()
    
    blob_client = container.get_blob_client(blob_name)
    
    with open(local_path, "wb") as f:
        data = blob_client.download_blob()
        f.write(data.readall())
    
    print(f"✅ Downloaded: {blob_name} → {local_path}")
    return local_path


def delete_file(blob_name: str):
    """Delete a file from Azure."""
    container = get_container_client()
    container.delete_blob(blob_name)
    print(f"🗑️ Deleted: {blob_name}")


# Quick test
if __name__ == "__main__":
    print("Testing Blob Storage connection...")
    
    try:
        files = list_files()
        print(f"\n📁 Files in container '{config.storage.container_name}':")
        if files:
            for f in files:
                print(f"  📄 {f['name']} ({f['size_kb']} KB)")
        else:
            print("  (empty — upload some files!)")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your AZURE_STORAGE_CONNECTION_STRING in .env")
