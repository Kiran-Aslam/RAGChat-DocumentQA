# RAG Assistant - AI-Powered Document Analysis

A sophisticated Retrieval-Augmented Generation (RAG) application with a beautiful dark green theme, built using Flask and modern web technologies.

## Features

- **Document Processing**: Upload and process PDF, TXT, DOCX, and CSV files
- **AI-Powered Q&A**: Ask questions about your documents and get intelligent responses
- **Semantic Search**: Advanced vector similarity search using FAISS
- **Beautiful UI**: Dark green theme with glow effects and smooth animations
- **Real-time Chat**: Interactive chat interface with typing indicators
- **File Management**: Upload multiple files and track processing statistics

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Groq API (Llama3-8b-8192), Sentence Transformers, FAISS
- **Frontend**: HTML5, CSS3, JavaScript
- **Document Processing**: PyPDF2, python-docx, pandas

## Usage

1. **Login**: Enter your name, email, and age to access the application
2. **Upload Documents**: Click "Upload Documents" to add files to your knowledge base
3. **Ask Questions**: Type questions about your documents in the chat interface
4. **View Statistics**: Monitor your knowledge base stats in the sidebar
5. **Clear Data**: Use "Clear All Data" to reset your knowledge base

## File Structure

```
rag_app/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── main_logic.py       # RAG processing logic
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── templates/
│   ├── index.html      # Main chat interface
│   └── login.html      # Login page
└── README.md          # This file
```

## API Endpoints

- `GET /` - Main application interface
- `GET /login` - Login page
- `POST /login` - Process login
- `POST /upload` - Upload and process files
- `POST /query` - Send chat queries
- `POST /clear_data` - Clear knowledge base
- `GET /logout` - Logout user

## Configuration

The application uses the following configuration in `config.py`:

- **GROQ_API_KEY**: Your Groq API key for AI responses
- **EMBEDDING_MODEL_NAME**: Sentence transformer model for embeddings
- **CHUNK_SIZE**: Text chunk size for processing
- **CHUNK_OVERLAP**: Overlap between text chunks
- **MAX_TOKENS**: Maximum tokens for AI responses
- **TEMPERATURE**: AI response creativity level

## Features in Detail

### Document Processing
- Automatic text extraction from multiple file formats
- Intelligent text chunking with overlap
- Vector embedding generation using sentence transformers
- FAISS index creation for fast similarity search

### AI Integration
- Groq API integration for high-quality responses
- Context-aware question answering
- Source attribution for transparency
- Processing time tracking

### User Interface
- Responsive design for desktop and mobile
- Dark green theme with glow effects
- Smooth animations and hover effects
- Real-time chat with typing indicators
- File upload progress tracking

## Security Notes

- Session management for user authentication
- Input validation and sanitization
- File type and size restrictions
- Error handling and graceful degradation

## Troubleshooting

1. **Dependencies Error**: Ensure all packages are installed with `pip install -r requirements.txt`
2. **API Key Error**: Verify your Groq API key is correctly set in `config.py`
3. **File Upload Issues**: Check file format (PDF, TXT, DOCX, CSV) and size limits
4. **Performance**: For large documents, processing may take time during first upload

## License

This project is provided as-is for educational and demonstration purposes.

## Support

For issues or questions, please check the troubleshooting section or review the code comments for implementation details.

