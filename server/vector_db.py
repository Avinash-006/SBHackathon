"""
Vector Database Manager for document indexing and semantic search
"""
import os
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions


DEFAULT_DB_PATH = Path("data/chroma_db")


class VectorDatabaseManager:
    """Manages ChromaDB vector database for document storage and retrieval"""

    def __init__(
        self,
        collection_name: str = "knowledge_navigator",
        persist_path: Optional[Path | str] = None,
    ):
        """Initialize the vector database manager"""

        self.collection_name = collection_name

        # Ensure persistence directory exists
        self.persist_path = Path(persist_path) if persist_path else DEFAULT_DB_PATH
        self.persist_path.mkdir(parents=True, exist_ok=True)

        # Create persistent Chroma client
        self.client = chromadb.PersistentClient(path=str(self.persist_path))

        # Use sentence transformer for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )
    
    def add_documents(self, documents: Dict[str, Dict]):
        
        if not documents:
            return
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for doc_id, doc_data in documents.items():
            content = doc_data.get("content", "")
            metadata = doc_data.get("metadata", {})
            
            if not content.strip():
                continue
            
           
            chunks = self._chunk_text(content, chunk_size=1000, overlap=200)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                ids.append(chunk_id)
                texts.append(chunk)
                metadatas.append({
                    **metadata,
                    "chunk_index": i,
                    "doc_id": doc_id
                })
        
        if ids:
            self.collection.add(
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
  
        if self.collection.count() == 0:
            return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        output = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "filename": meta.get("filename", "unknown"),
                "metadata": meta,
                "distance": dist
            })
        
        return output
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
       
        results = self.collection.get(
            where={"doc_id": doc_id}
        )
        
        if results.get("documents"):
            return {
                "text": "\n".join(results["documents"]),
                "metadata": results.get("metadatas", [{}])[0]
            }
        return None
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only if we're not too far from start
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap  # Overlap for context
        
        return chunks
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def get_all_document_ids(self) -> List[str]:
        """Get all unique document IDs from the collection"""
        if self.collection.count() == 0:
            return []
        
        # Get all items from collection
        all_items = self.collection.get()
        metadatas = all_items.get("metadatas", [])
        
        # Extract unique doc_ids
        doc_ids = set()
        for metadata in metadatas:
            doc_id = metadata.get("doc_id")
            if doc_id:
                doc_ids.add(doc_id)
        
        return list(doc_ids)
    
    def search_by_filename(self, filename: str) -> List[Dict]:
        """Search for documents by filename (exact or partial match)"""
        if self.collection.count() == 0:
            return []
        
        # Get all items from collection
        all_items = self.collection.get()
        documents = all_items.get("documents", [])
        metadatas = all_items.get("metadatas", [])
        ids = all_items.get("ids", [])
        
        filename_lower = filename.lower()
        matching_docs = []
        
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            meta_filename = meta.get("filename", "").lower()
            if filename_lower in meta_filename or meta_filename in filename_lower:
                matching_docs.append({
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "filename": meta.get("filename", "unknown"),
                    "metadata": meta,
                    "distance": 0.0  # Exact match
                })
        
        return matching_docs
    
    def get_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name
        }

