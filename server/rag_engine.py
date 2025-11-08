"""
RAG Engine for query processing and document analysis
"""
import os
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google import genai
from server.vector_db import VectorDatabaseManager

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env file!")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


class RAGEngine:
    """RAG Engine for querying documents using Gemini AI"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """Initialize the RAG engine"""
        self.model_name = model_name
        self.db = VectorDatabaseManager()
        self.client = client
    
    def query(self, query: str, top_k: int = 5) -> Dict:
        """
        Process a query and return results
        
        Args:
            query: User query
            top_k: Number of relevant documents to retrieve
            
        Returns:
            Dictionary with query results
        """
        start_time = time.time()
        
        # Retrieve relevant documents
        retrieved_docs = self.db.search(query, top_k=top_k)
        
        if not retrieved_docs:
            return {
                "query": query,
                "documents_found": [],
                "summary": "No relevant documents found in the database.",
                "key_points": [],
                "execution_time": time.time() - start_time
            }
        
        # Build context from retrieved documents
        context = self._build_context(retrieved_docs)
        
        # Generate response using Gemini
        prompt = self._build_prompt(query, context, retrieved_docs)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            answer = response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            answer = f"Error generating response: {str(e)}"
        
        # Extract documents found
        documents_found = list(set([doc.get("filename", doc.get("source", "unknown")) 
                                   for doc in retrieved_docs]))
        
        execution_time = time.time() - start_time
        
        return {
            "query": query,
            "documents_found": documents_found,
            "summary": answer,
            "retrieved_documents": retrieved_docs[:3],  # Include top 3 for reference
            "execution_time": round(execution_time, 2)
        }
    
    def summarize(self, document_ids: List[str], summary_type: str = "comparative") -> Dict:
        """
        Summarize or compare documents
        
        Args:
            document_ids: List of document IDs to summarize
            summary_type: Type of summary ("comparative", "extractive", "abstractive")
            
        Returns:
            Dictionary with summary results
        """
        documents = []
        for doc_id in document_ids:
            doc = self.db.get_document_by_id(doc_id)
            if doc:
                documents.append(doc)
        
        if not documents:
            return {
                "status": "error",
                "message": "No documents found with provided IDs"
            }
        
        # Build comparison prompt
        if summary_type == "comparative":
            prompt = self._build_comparison_prompt(documents)
        else:
            prompt = self._build_summary_prompt(documents, summary_type)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            summary = response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
        
        return {
            "status": "success",
            "summary_type": summary_type,
            "documents_analyzed": len(documents),
            "summary": summary
        }
    
    def _build_context(self, retrieved_docs: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("filename", doc.get("source", "unknown"))
            text = doc.get("text", "")
            context_parts.append(f"[Document {i}: {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, retrieved_docs: List[Dict]) -> str:
        """Build prompt for Gemini"""
        prompt = f"""You are an internal knowledge navigator AI assistant. Your task is to help users find and understand information from their documents.

Use ONLY the provided context from the documents. If the information is not in the context, say so clearly.

=== CONTEXT FROM DOCUMENTS ===
{context}

=== USER QUERY ===
{query}

=== INSTRUCTIONS ===
1. Answer the query based on the provided context
2. If comparing documents, highlight key differences clearly
3. Include specific references to document names when relevant
4. Be concise but comprehensive
5. If the query asks for comparisons, create a structured comparison with:
   - Key differences
   - Similarities
   - Impact/Implications

Provide your answer:"""
        
        return prompt
    
    def _build_comparison_prompt(self, documents: List[Dict]) -> str:
        """Build prompt for document comparison"""
        doc_texts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get("metadata", {}).get("filename", f"Document {i}")
            text = doc.get("text", "")
            doc_texts.append(f"=== {source} ===\n{text}\n")
        
        prompt = f"""Compare the following documents and identify:
1. Key differences
2. Similarities
3. Changes or updates
4. Risk implications (if applicable)

{doc_texts[0] if doc_texts else ""}
{'=== COMPARED WITH ===' if len(doc_texts) > 1 else ''}
{chr(10).join(doc_texts[1:]) if len(doc_texts) > 1 else ''}

Provide a structured comparison:"""
        
        return prompt
    
    def _build_summary_prompt(self, documents: List[Dict], summary_type: str) -> str:
        """Build prompt for document summarization"""
        doc_text = "\n\n".join([doc.get("text", "") for doc in documents])
        
        if summary_type == "extractive":
            instruction = "Extract the most important sentences and key points from the document(s)."
        else:  # abstractive
            instruction = "Provide a concise summary of the main points and key information from the document(s)."
        
        prompt = f"""{instruction}

=== DOCUMENT(S) ===
{doc_text}

Provide your summary:"""
        
        return prompt

