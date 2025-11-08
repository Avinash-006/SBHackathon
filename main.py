"""
FastAPI Backend Server with MCP Tools
"""
from mcp.server.fastmcp import FastMCP
from server.vector_db import VectorDatabaseManager
from server.rag_engine import RAGEngine

mcp = FastMCP("knowledge_navigator")


@mcp.tool()
async def search_docs(query: str, top_k: int = 5) -> dict:
    """Semantic search across documents"""
    db = VectorDatabaseManager()
    return db.search(query, top_k)


@mcp.tool()
async def summarize(document_ids: list[str], summary_type: str = "comparative") -> dict:
    """Summarize or compare documents"""
    rag = RAGEngine()
    return rag.summarize(document_ids, summary_type)


@mcp.tool()
async def query_documents(query: str, top_k: int = 5) -> dict:
    """Query documents using RAG (Retrieval Augmented Generation)"""
    rag = RAGEngine()
    return rag.query(query, top_k)


# Export app for uvicorn
app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
