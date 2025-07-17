"""
Utility functions for RAG Assistant App
"""

import base64
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import SESSION_KEYS, ERROR_MESSAGES, SUCCESS_MESSAGES

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        SESSION_KEYS["logged_in"]: False,
        SESSION_KEYS["user_info"]: {},
        SESSION_KEYS["chat_history"]: [],
        SESSION_KEYS["uploaded_files_info"]: [],
        SESSION_KEYS["last_response"]: "",
        SESSION_KEYS["response_timestamp"]: 0,
        SESSION_KEYS["processing_query"]: False,
        SESSION_KEYS["upload_success_message"]: ""
    }
    
    for key, default_value in defaults.items():
        # In a Flask app, session management is different. 
        # We'll handle this in app.py using Flask's session object or a custom state management.
        # For now, this function will be a placeholder or adapted for Flask context.
        pass

def validate_email(email: str) -> bool:
    """Validate email format"""
    return "@" in email and "." in email

def validate_age(age_str: str) -> tuple[bool, Optional[int]]:
    """Validate age input"""
    try:
        age_int = int(age_str)
        if 1 <= age_int <= 120:
            return True, age_int
        return False, None
    except ValueError:
        return False, None

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type"""
    extension = "." + filename.split(".").pop().lower()
    return extension in [f".{ext}" for ext in allowed_types]

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size"""
    return file_size <= max_size

def encode_file_content(file_content: bytes) -> str:
    """Encode file content to base64"""
    return base64.b64encode(file_content).decode("utf-8")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def add_chat_message(chat_history: List, role: str, content: str):
    """Add message to chat history"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    chat_history.append(message)

def get_current_time() -> str:
    """Get current time formatted"""
    return datetime.now().strftime("%H:%M")

def prepare_files_data(uploaded_files) -> tuple[bool, List[Dict], str]:
    """Prepare files data for processing"""
    if not uploaded_files:
        return False, [], ERROR_MESSAGES["no_files"]
    
    files_data = []
    for uploaded_file in uploaded_files:
        try:
            # Validate file type
            if not validate_file_type(uploaded_file.filename, ["pdf", "txt", "docx", "csv"]):
                return False, [], f"Invalid file type: {uploaded_file.filename}"
            
            # Read and validate file content
            file_content = uploaded_file.read()
            
            # Validate file size
            if not validate_file_size(len(file_content), 10 * 1024 * 1024):  # 10MB
                return False, [], f"File too large: {uploaded_file.filename}"
            
            # Encode file content
            file_base64 = encode_file_content(file_content)
            
            files_data.append({
                "name": uploaded_file.filename,
                "size": len(file_content),
                "content": file_base64,
                "type": uploaded_file.content_type
            })
        except Exception as e:
            return False, [], f"Error reading file {uploaded_file.filename}: {str(e)}"
    
    return True, files_data, ""

def format_processing_time(processing_time: float) -> str:
    """Format processing time"""
    return f"\n\n⏱️ *Processing time: {processing_time:.2f}s*"

def create_user_info(name: str, age: int, email: str) -> Dict[str, Any]:
    """Create user info dictionary"""
    return {
        "name": name,
        "age": age,
        "email": email,
        "login_time": datetime.now().isoformat()
    }

def get_user_avatar(name: str) -> str:
    """Get user avatar letter"""
    return name[0].upper() if name else "U"

def convert_to_js_format(data: Any) -> str:
    """Convert Python data to JavaScript format"""
    return json.dumps(data)

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.split(".")[-1].lower() if "." in filename else ""

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    return re.sub(r"[^\w\-_\.]", "_", filename)
