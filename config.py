import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_TOKENS = 2048
TEMPERATURE = 0.7

SESSION_KEYS = {
    "logged_in": "logged_in",
    "user_info": "user_info",
    "chat_history": "chat_history",
    "uploaded_files_info": "uploaded_files_info",
    "last_response": "last_response",
    "response_timestamp": "response_timestamp",
    "processing_query": "processing_query",
    "upload_success_message": "upload_success_message"
}

ERROR_MESSAGES = {
    "no_files": "No files provided for upload.",
    "rag_unavailable": "RAG system is currently unavailable."
}

SUCCESS_MESSAGES = {
    "files_processed": "Successfully processed {count} files.",
    "data_cleared": "All processed data has been cleared."
}

