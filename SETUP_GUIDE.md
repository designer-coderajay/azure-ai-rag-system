# Project 1: Azure AI RAG System — Complete Setup Guide

## 🧒 What Are We Building?

Imagine a smart assistant that can read YOUR documents and answer questions about them.

- You upload PDFs/documents to Azure (cloud storage)
- Azure AI Search reads them and creates a searchable index
- When you ask a question, it finds relevant parts
- Azure OpenAI (GPT) reads those parts and gives you an answer

This is called RAG: Retrieval Augmented Generation.

---

## PHASE 1: Set Up Azure Portal (15 minutes)

### Step 1: Open Azure Portal

1. Open your browser
2. Go to: **https://portal.azure.com**
3. Sign in with the account that has your ₹17,996 credits
4. You'll see the Azure "Home" page — a dashboard with blue tiles

> **What is Azure Portal?**
> Think of it as a control panel for all your cloud resources.
> Like a file manager, but for cloud services.

### Step 2: Check Your Credits

1. Click the **search bar** at the very top of the page
2. Type: **"Cost Management"**
3. Click **"Cost Management + Billing"**
4. Look for your remaining credit balance
5. Set a budget alert:
   - Click **"Budgets"** in the left menu
   - Click **"+ Add"**
   - Set amount: **$150** (safety buffer)
   - Add your email for alerts

### Step 3: Create a Resource Group

> **What is a Resource Group?**
> A folder. That's it. It groups related resources together.
> When you're done with a project, you delete the folder and everything inside goes away.

1. Click the **search bar** at the top
2. Type: **"Resource groups"**
3. Click **"Resource groups"**
4. Click **"+ Create"**
5. Fill in:
   - **Subscription**: Select your subscription (the one with credits)
   - **Resource group name**: `rg-rag-project`
   - **Region**: `Sweden Central` (cheapest for AI services in Europe)
     - If Sweden Central isn't available, use `West Europe` or `East US`
6. Click **"Review + create"**
7. Click **"Create"**

✅ You now have a folder for all Project 1 resources.

---

## PHASE 2: Create Azure OpenAI Service (10 minutes)

> **What is Azure OpenAI?**
> Microsoft hosts OpenAI's models (GPT-4, GPT-4o-mini) on Azure.
> You get an API endpoint — your code sends text, gets AI responses back.
> It's like ChatGPT, but as an API you control.

### Step 4: Create the OpenAI Resource

1. Click the **search bar** at the top
2. Type: **"Azure OpenAI"**
3. Click **"Azure OpenAI"**
4. Click **"+ Create"**
5. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `rg-rag-project`
   - **Region**: `Sweden Central` (MUST match your resource group if possible)
   - **Name**: `openai-rag-project` (must be globally unique, add numbers if taken)
   - **Pricing tier**: `Standard S0`
6. Click **"Next"** through the tabs (keep defaults)
7. Click **"Review + submit"**
8. Click **"Create"**
9. Wait 1-2 minutes for deployment

### Step 5: Deploy Models Inside Azure OpenAI

> **Why deploy models?**
> Creating the OpenAI resource just gave you a "server."
> Now you need to put specific models ON that server.
> We need two: one for chat (GPT-4o-mini) and one for embeddings.

1. After deployment completes, click **"Go to resource"**
2. Click **"Go to Azure AI Foundry portal"** (blue button, might say "Go to Azure OpenAI Studio")
   - This opens a NEW tab — the AI Foundry / AI Studio interface
3. In the left sidebar, click **"Deployments"** (or "Model deployments")
4. Click **"+ Create deployment"** (or "+ Deploy model")

**Deploy Chat Model:**
5. Select model: **gpt-4o-mini**
6. Deployment name: **gpt-4o-mini** (keep it simple)
7. Click **"Deploy"**

**Deploy Embedding Model:**
8. Click **"+ Create deployment"** again
9. Select model: **text-embedding-3-small**
10. Deployment name: **text-embedding-3-small**
11. Click **"Deploy"**

### Step 6: Get Your OpenAI Credentials

1. Go back to Azure Portal (the other tab)
2. Navigate to your OpenAI resource (search "openai-rag" in search bar)
3. In the left sidebar, click **"Keys and Endpoint"**
4. Copy and save these somewhere safe:
   - **KEY 1**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Endpoint**: `https://openai-rag-project.openai.azure.com/`

🔑 **SAVE THESE! You'll need them in your code.**

---

## PHASE 3: Create Azure AI Search (10 minutes)

> **What is Azure AI Search?**
> A search engine. You put documents in, it creates an index.
> When you search, it finds relevant results FAST.
> It supports both keyword search AND vector search (semantic meaning).
> Think of it as Google, but for your own documents.

### Step 7: Create the Search Resource

1. Click the **search bar** at the top
2. Type: **"AI Search"**
3. Click **"AI Search"**
4. Click **"+ Create"**
5. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `rg-rag-project`
   - **Service name**: `search-rag-project` (globally unique)
   - **Location**: `Sweden Central`
   - **Pricing tier**: Click **"Change Pricing Tier"**
     - Select **"Free"** (for development)
     - ⚠️ Free tier: 3 indexes, 50MB storage — enough for learning
     - If you need more later, upgrade to Basic ($70/month)
6. Click **"Review + create"**
7. Click **"Create"**

### Step 8: Get Your Search Credentials

1. After deployment, click **"Go to resource"**
2. In left sidebar, click **"Keys"**
3. Copy **"Primary admin key"**: `xxxxxxxx`
4. Go back, look at the **Overview** page
5. Copy the **URL**: `https://search-rag-project.search.windows.net`

🔑 **SAVE THESE TOO!**

---

## PHASE 4: Create Azure Blob Storage (10 minutes)

> **What is Blob Storage?**
> Cloud file storage. "Blob" = Binary Large OBject.
> It's like a USB drive in the cloud.
> You upload files, Azure can read them from there.

### Step 9: Create Storage Account

1. Click the **search bar**
2. Type: **"Storage accounts"**
3. Click **"Storage accounts"**
4. Click **"+ Create"**
5. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `rg-rag-project`
   - **Storage account name**: `storageragproject` (lowercase, no dashes, globally unique)
   - **Region**: `Sweden Central`
   - **Performance**: `Standard`
   - **Redundancy**: `LRS` (Locally redundant — cheapest)
6. Click **"Review + create"**
7. Click **"Create"**

### Step 10: Create a Container and Upload Documents

> **What is a Container?**
> A folder inside your storage account. You organize files in containers.

1. After deployment, click **"Go to resource"**
2. In the left sidebar, click **"Containers"** (under "Data storage")
3. Click **"+ Container"**
4. Name: `documents`
5. Public access level: **Private**
6. Click **"Create"**
7. Click on your new `documents` container
8. Click **"Upload"**
9. Upload some test files (PDFs, text files about any topic)
   - Use the sample docs from our local RAG project, or any PDFs you have

### Step 11: Get Storage Credentials

1. In your Storage account, left sidebar → **"Access keys"**
2. Click **"Show"** next to Key 1
3. Copy the **"Connection string"**: `DefaultEndpointsProtocol=https;AccountName=...`

🔑 **SAVE THIS!**

---

## PHASE 5: Connect AI Search to Blob Storage (The Magic Part)

> **What happens here?**
> We tell Azure AI Search: "Watch this blob container.
> Whenever documents appear, read them, chunk them, and make them searchable."
> This is called an INDEXER + DATA SOURCE + INDEX pipeline.

### Step 12: Import Data in AI Search

1. Go to your **AI Search** resource (search for it)
2. Click **"Import data"** (top bar)
3. **Data Source**:
   - Data source: **Azure Blob Storage**
   - Data source name: `blob-documents`
   - Connection string: Click **"Choose an existing connection"**
     - Select your storage account → select `documents` container
   - Click **"Next: Add cognitive skills"**
4. **Cognitive Skills** (optional enrichments):
   - Skip this for now (click **"Skip to: Customize target index"**)
   - (This is where you'd add OCR, language detection, etc.)
5. **Customize Target Index**:
   - Index name: `rag-index`
   - Make sure **"content"** field is marked as:
     - ✅ Retrievable
     - ✅ Searchable
   - Check **"metadata_storage_name"** is:
     - ✅ Retrievable
     - ✅ Filterable
6. Click **"Next: Create an indexer"**
7. **Indexer**:
   - Name: `blob-indexer`
   - Schedule: **Once** (for now)
8. Click **"Submit"**

Wait 1-2 minutes. Your documents are now indexed! 🎉

### Step 13: Add Vector Search (Semantic Search)

> This makes search understand MEANING, not just keywords.
> "car" will match "automobile" even though the words are different.

1. Still in AI Search, click **"Indexes"** in left sidebar
2. Click on your **"rag-index"**
3. Click **"Edit JSON"** (or we'll handle this in code — see below)

Actually, the easiest way to add vector search is through the code.
We'll create a new index with vector fields programmatically.

---

## PHASE 6: Collect All Your Credentials

You should now have these saved. Create a `.env` file:

```
AZURE_OPENAI_ENDPOINT=https://openai-rag-project.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

AZURE_SEARCH_ENDPOINT=https://search-rag-project.search.windows.net
AZURE_SEARCH_KEY=your-admin-key-here
AZURE_SEARCH_INDEX=rag-index

AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=documents
```

---

## Next: Write the Code (in VS Code)

Now we switch to VS Code. All the Azure resources are set up.
The code lives in this project folder.

See the Python files in `src/` for the implementation.
