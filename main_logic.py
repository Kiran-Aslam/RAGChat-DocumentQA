# main_logic.py
"""
Core RAG functionality for document processing, embedding, and AI response generation.
"""
import base64
import io
import time
from typing import List, Dict, Any

# Attempt to import dependencies
try:
    from groq import Groq
    import PyPDF2
    import docx
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    import pandas as pd
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

from config import (
    GROQ_API_KEY, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, MAX_TOKENS, TEMPERATURE
)

class RAGAssistant:
    """A class that encapsulates the entire RAG pipeline."""

    def __init__(self):
        """Initializes the RAG Assistant."""
        self.dependencies_available = DEPENDENCIES_AVAILABLE
        self.import_error = IMPORT_ERROR if not DEPENDENCIES_AVAILABLE else None
        
        self.groq_client = None
        self.embedding_model = None
        self.documents = []
        self.faiss_index = None

        if self.dependencies_available:
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            except Exception as e:
                self.dependencies_available = False
                self.import_error = f"Failed to initialize models: {e}"

    def _extract_text(self, file_name: str, file_content_b64: str) -> str:
        """Extracts text from a base64 encoded file based on its extension."""
        file_bytes = base64.b64decode(file_content_b64)
        text = ""
        try:
            if file_name.lower().endswith('.pdf'):
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
            elif file_name.lower().endswith('.docx'):
                doc = docx.Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif file_name.lower().endswith('.txt'):
                text = file_bytes.decode('utf-8', errors='ignore')
            elif file_name.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
                text = df.to_string()
        except Exception as e:
            return f"Error extracting text from {file_name}: {e}"
        return text

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Splits text into overlapping chunks."""
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = " ".join(words[i:i + CHUNK_SIZE])
            chunks.append(chunk)
        return chunks

    def process_files(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes uploaded files, extracts text, creates chunks, and builds a FAISS index."""
        if not self.dependencies_available:
            return {"success": False, "message": f"Dependencies missing: {self.import_error}"}

        self.documents = []
        processed_files_count = 0
        for file_info in files_data:
            text = self._extract_text(file_info['name'], file_info['content'])
            if text and not text.startswith("Error"):
                chunks = self._split_text_into_chunks(text)
                for i, chunk_content in enumerate(chunks):
                    self.documents.append({
                        "filename": file_info['name'],
                        "chunk_id": i,
                        "content": chunk_content
                    })
                processed_files_count += 1
        
        if not self.documents:
            return {"success": False, "message": "Could not extract any text from the provided files."}

        # Create embeddings and FAISS index
        try:
            embeddings = self.embedding_model.encode([doc['content'] for doc in self.documents], show_progress_bar=True)
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dimension)
            self.faiss_index.add(embeddings.astype('float32'))
        except Exception as e:
            return {"success": False, "message": f"Failed to create search index: {e}"}

        return {"success": True, "message": f"Successfully processed {processed_files_count} files."}

    def _search_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches for the most relevant document chunks for a given query."""
        if not self.faiss_index:
            return []
        
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.faiss_index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                doc = self.documents[idx]
                # Convert L2 distance to a similarity score (0-1)
                similarity = max(0, 1 - (distances[0][i] / 2))
                doc['similarity'] = similarity
                results.append(doc)
        return results

    def query(self, user_query: str) -> Dict[str, Any]:
        """Handles a user query by performing RAG."""
        if not self.dependencies_available:
            return {"success": False, "response": f"Dependencies missing: {self.import_error}"}
        if not self.faiss_index:
            return {"success": False, "response": "No documents have been processed. Please upload files first."}

        relevant_chunks = self._search_similar_chunks(user_query)
        context = "\n\n".join([f"Source: {chunk['filename']} (Chunk {chunk['chunk_id']})\nContent: {chunk['content']}" for chunk in relevant_chunks])
        
        prompt = f"""
        You are an expert AI assistant. Answer the user's question based on the provided context from their documents.
        If the context does not contain the answer, state that the information is not available in the provided documents.
        
        Context:
        {context}
        
        User Question: {user_query}
        
        Answer:
        """
        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as e:
            return {"success": False, "response": f"Error generating AI response: {e}"}

        return {
            "success": True,
            "response": response_text
        }

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the current knowledge base."""
        if not self.documents:
            return {"total_documents": 0, "total_chunks": 0, "files": []}
        
        file_names = {doc['filename'] for doc in self.documents}
        return {
            "total_documents": len(file_names),
            "total_chunks": len(self.documents),
            "files": list(file_names)
        }

    def clear_data(self):
        """Clears all processed data."""
        self.documents = []
        self.faiss_index = None


