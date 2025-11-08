# 📚 Internal Knowledge Navigator - Quick Start Edition

> Just provide your **query** and **documents folder path** - the system handles everything else automatically!

## 🎯 What This Does

Search, compare, and summarize documents using AI. Perfect for:
- Comparing contract versions
- Finding policy changes
- Extracting key information from documents
- Multi-document analysis

## 📁 Project Structure

project/
├── requirements.txt
├── .env
├── app.py # Main Streamlit app (run this!)
├── main.py # Backend server
├── input.json # Auto-generated from user inputs
├── output.json # Auto-generated responses
├── metadata.json # Auto-generated project info
├── server/
│ ├── vector_db.py
│ ├── rag_engine.py
│ └── tools/
└── your_documents/ # 👈 Put your documents here!

text

## 🚀 Setup (3 Minutes)

### Step 1: Create Virtual Environment

**Windows:**
python -m venv .venv
..venv\Scripts\activate

text

**macOS/Linux:**
python3 -m venv .venv
source .venv/bin/activate

text

### Step 2: Install Dependencies

Copy this into `requirements.txt`:

mcp==0.7.3
fastapi==0.110.0
uvicorn==0.29.0
streamlit==1.32.2
google-generativeai==0.7.0
chromadb==0.5.0
pypdf==4.0.1
python-docx==0.8.11
python-dotenv==1.0.0
pydantic==2.5.0
httpx==0.27.0

text

Then run:
pip install -r requirements.txt

text

### Step 3: Add Your Gemini API Key

Create `.env` file:
GEMINI_API_KEY=your_api_key_here

text

Get your free API key: https://makersuite.google.com/app/apikey

## ▶️ Run the App

streamlit run app.py

text

The app will open in your browser at `http://localhost:8501`

## 💡 How to Use

### 1️⃣ Enter Your Documents Folder Path
Example: ./my_documents
Example: C:\Users\YourName\HR_Files
Example: /home/user/contracts

text

### 2️⃣ Enter Your Query
Examples:

"Compare risk clauses in contract_v1.pdf and contract_v2.pdf"

"Summarize the leave policy changes in 2024"

"What are the key differences between these employment agreements?"

"Find all documents mentioning liability and indemnification"

text

### 3️⃣ Click "Search & Analyze" ✨

The system will:
1. 🔍 Automatically scan your folder
2. 📊 Index all documents (first time only)
3. 🤖 Search using AI semantic understanding
4. 📝 Generate detailed comparisons/summaries
5. 💾 Save results to `output.json`

## 📄 Auto-Generated Files

### input.json
Automatically created from your inputs:
{
"folder_path": "./your_documents",
"query": "Compare risk clauses in contract v1 and v2",
"timestamp": "2025-11-07T12:04:00Z"
}

text

### output.json
Contains your results:
{
"status": "success",
"query": "Compare risk clauses in contract v1 and v2",
"results": {
"documents_found": ["contract_v1.pdf", "contract_v2.pdf"],
"summary": "Key differences identified...",
"key_differences": [
{
"clause": "Risk Allocation",
"old_value": "50/50 split",
"new_value": "70/30 split",
"impact": "Company assumes more risk"
}
]
}
}

text

### metadata.json
Auto-generated project info:
{
"project": "Knowledge Navigator",
"last_run": "2025-11-07T12:04:00Z",
"folder_indexed": "./your_documents",
"total_documents": 12,
"file_types": [".pdf", ".docx", ".txt"]
}

text

## 🎨 Streamlit App Interface

The `app.py` creates this simple interface:

import streamlit as st
import json
import os
from datetime import datetime
from server.vector_db import VectorDatabaseManager
from server.rag_engine import RAGEngine

st.title("📚 Internal Knowledge Navigator")
st.markdown("### Enter your query and documents folder - we'll handle the rest!")

User Inputs
folder_path = st.text_input(
"📁 Documents Folder Path",
placeholder="./documents or C:\my_docs",
help="Path to folder containing your PDFs, DOCX, or TXT files"
)

query = st.text_area(
"❓ Your Query",
placeholder="e.g., Compare risk clauses between contract v1 and v2",
height=100
)

if st.button("🔍 Search & Analyze", type="primary"):
if not folder_path or not query:
st.error("Please provide both folder path and query!")
else:
with st.spinner("Processing..."):
# Save input.json
input_data = {
"folder_path": folder_path,
"query": query,
"timestamp": datetime.now().isoformat()
}
with open("input.json", "w") as f:
json.dump(input_data, f, indent=2)

text
        # Index documents (if not already indexed)
        st.info("📊 Indexing documents from folder...")
        db = VectorDatabaseManager()
        docs_indexed = index_folder(folder_path, db)
        
        # Update metadata.json
        metadata = {
            "project": "Knowledge Navigator",
            "last_run": datetime.now().isoformat(),
            "folder_indexed": folder_path,
            "total_documents": docs_indexed,
            "file_types": [".pdf", ".docx", ".txt"]
        }
        with open("metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Execute RAG query
        st.info("🤖 Analyzing documents with AI...")
        rag = RAGEngine()
        result = rag.query(query)
        
        # Save output.json
        output_data = {
            "status": "success",
            "query": query,
            "execution_time": result.get("execution_time", 0),
            "results": result
        }
        with open("output.json", "w") as f:
            json.dump(output_data, f, indent=2)
        
        # Display results
        st.success("✅ Analysis Complete!")
        st.markdown("### 📊 Results")
        st.json(result)
        
        # Download button
        st.download_button(
            "💾 Download Results (JSON)",
            data=json.dumps(output_data, indent=2),
            file_name="results.json",
            mime="application/json"
        )
def index_folder(folder_path, db):
"""Index all documents in the folder"""
from pathlib import Path

text
documents = {}
count = 0

for file_path in Path(folder_path).rglob("*"):
    if file_path.suffix.lower() in [".pdf", ".txt", ".docx"]:
        content = extract_text(file_path)
        doc_id = str(file_path).replace("/", "_")
        documents[doc_id] = {
            "content": content,
            "metadata": {
                "filename": file_path.name,
                "source": str(file_path),
                "type": file_path.suffix[1:]
            }
        }
        count += 1

db.add_documents(documents)
return count
def extract_text(file_path):
"""Extract text from PDF/DOCX/TXT"""
from pypdf import PdfReader
from docx import Document

text
if file_path.suffix == ".pdf":
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() for page in reader.pages)
elif file_path.suffix == ".docx":
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)
else:
    return file_path.read_text()
text

## 🔧 Backend Server (main.py)

Minimal FastAPI server with MCP tools:

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from server.vector_db import VectorDatabaseManager
from server.rag_engine import RAGEngine

mcp = FastMCP("knowledge_navigator")

@mcp.tool
async def search_docs(query: str, top_k: int = 5) -> dict:
"""Semantic search across documents"""
db = VectorDatabaseManager()
return db.search(query, top_k)

@mcp.tool
async def summarize(document_ids: list, summary_type: str = "comparative") -> dict:
"""Summarize or compare documents"""
rag = RAGEngine()
return rag.summarize(document_ids, summary_type)

if name == "main":
import uvicorn
uvicorn.run(mcp.get_asgi_app(), host="0.0.0.0", port=8000)

text

## 📖 Example Usage

### Example 1: Compare Contracts
**Folder:** `./contracts`  
**Query:** `Compare liability clauses between employment_2023.pdf and employment_2024.pdf`

**Result:**
{
"documents_compared": ["employment_2023.pdf", "employment_2024.pdf"],
"key_differences": [
{
"clause": "Liability Cap",
"old_value": "$500K",
"new_value": "$750K",
"impact": "Increased exposure by $250K"
}
]
}

text

### Example 2: Policy Summary
**Folder:** `./HR_policies`  
**Query:** `Summarize the remote work policy`

**Result:**
{
"summary": "Remote work policy allows 10 days/year with manager approval...",
"key_points": [
"10 remote days per year",
"Manager approval required",
"VPN access mandatory"
]
}

text

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key invalid" | Check `.env` file has correct `GEMINI_API_KEY` |
| "Folder not found" | Use absolute path: `C:\Users\Name\docs` |
| "No documents indexed" | Ensure folder contains .pdf, .docx, or .txt files |
| Import errors | Run `pip install -r requirements.txt` again |

## 📚 Supported File Types

- ✅ PDF (.pdf)
- ✅ Word Documents (.docx)
- ✅ Text Files (.txt)

## 🎯 Tips for Best Results

1. **Specific queries work best:** "Compare risk clauses in contract v1 vs v2" is better than "tell me about contracts"
2. **Organize your folders:** Keep related documents together
3. **First run takes longer:** Indexing happens once, then searches are instant
4. **Check output.json:** All results are saved there automatically

## 🚀 You're Ready!

Just run `streamlit run app.py` and start querying your documents!

---

**Made with ❤️ using MCP, Gemini, Chroma, and Streamlit**