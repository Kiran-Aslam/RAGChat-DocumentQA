from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from main_logic import RAGAssistant
from utils import (
    initialize_session_state, validate_email, validate_age, prepare_files_data,
    add_chat_message, get_user_avatar, convert_to_js_format,
    format_processing_time
)
from config import SESSION_KEYS, ERROR_MESSAGES, SUCCESS_MESSAGES
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24) # Replace with a strong, randomly generated key in production

rag_assistant = RAGAssistant()

@app.before_request
def before_request():
    # Initialize session state for new sessions
    if not session.get(SESSION_KEYS["logged_in"]):
        session[SESSION_KEYS["logged_in"]] = False
        session[SESSION_KEYS["user_info"]] = {}
        session[SESSION_KEYS["chat_history"]] = []
        session[SESSION_KEYS["uploaded_files_info"]] = []

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get(SESSION_KEYS["logged_in"]):
        return redirect(url_for("login"))

    user_name = session[SESSION_KEYS["user_info"]].get("name", "User")
    chat_history = session[SESSION_KEYS["chat_history"]]
    uploaded_files_info = session[SESSION_KEYS["uploaded_files_info"]]

    # RAG status
    rag_status = {"available": rag_assistant.dependencies_available}
    if not rag_assistant.dependencies_available:
        rag_status["error"] = rag_assistant.import_error

    # Prepare stats for JS
    stats = rag_assistant.get_stats()
    # Add chunk count to each file info for display
    for uploaded_file in uploaded_files_info:
        file_name = uploaded_file["name"]
        chunk_count = sum(1 for doc in rag_assistant.documents if doc["filename"] == file_name)
        uploaded_file["chunks"] = chunk_count
    stats["files"] = uploaded_files_info

    # Handle query from JS
    query_param = request.args.get("chat_query")
    if query_param:
        user_query = query_param
        add_chat_message(chat_history, "user", user_query)

        if not rag_assistant.dependencies_available:
            response_text = f"❌ RAG system is currently unavailable: {rag_assistant.import_error}"
            add_chat_message(chat_history, "bot", response_text)
            return redirect(url_for("index", response=response_text))

        if not rag_assistant.faiss_index:
            response_text = "No documents have been processed. Please upload files first."
            add_chat_message(chat_history, "bot", response_text)
            return redirect(url_for("index", response=response_text))

        ai_response = rag_assistant.query(user_query)
        if ai_response["success"]:
            response_text = ai_response["response"]
            response_text += format_processing_time(ai_response["processing_time"])
            add_chat_message(chat_history, "bot", response_text)
            return redirect(url_for("index", response=response_text))
        else:
            response_text = f"Error: {ai_response['response']}"
            add_chat_message(chat_history, "bot", response_text)
            return redirect(url_for("index", error=response_text))

    # Handle file upload from JS
    upload_param = request.args.get("upload_files")
    if upload_param == "true":
        # This is a placeholder. Actual file upload will happen via a separate endpoint or form submission.
        # For now, we just redirect back to clear the param.
        return redirect(url_for("index"))

    # Handle clear data from JS
    clear_data_param = request.args.get("clear_data")
    if clear_data_param == "true":
        rag_assistant.clear_data()
        session[SESSION_KEYS["uploaded_files_info"]] = []
        session[SESSION_KEYS["chat_history"]] = [] # Clear chat history on data clear
        add_chat_message(session[SESSION_KEYS["chat_history"]], "system", SUCCESS_MESSAGES["data_cleared"])
        return redirect(url_for("index", upload_success=SUCCESS_MESSAGES["data_cleared"]))

    return render_template(
        "index.html",
        user_name=user_name,
        user_avatar=get_user_avatar(user_name),
        chat_history_json=convert_to_js_format(chat_history),
        stats_json=convert_to_js_format(stats),
        rag_status_json=convert_to_js_format(rag_status),
        current_time=lambda: datetime.now().strftime("%H:%M")
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_name = request.form["user_name"]
        user_email = request.form["user_email"]
        user_age = request.form["user_age"]

        if not user_name:
            return render_template("login.html", error="Name cannot be empty.")
        if not validate_email(user_email):
            return render_template("login.html", error="Invalid email format.")
        is_valid_age, age_int = validate_age(user_age)
        if not is_valid_age:
            return render_template("login.html", error="Age must be a number between 1 and 120.")

        session[SESSION_KEYS["logged_in"]] = True
        session[SESSION_KEYS["user_info"]] = {"name": user_name, "email": user_email, "age": age_int}
        session[SESSION_KEYS["chat_history"]] = [] # Clear chat history on new login
        add_chat_message(session[SESSION_KEYS["chat_history"]], "system", f"Welcome, {user_name}! You are now logged in.")
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    if not session.get(SESSION_KEYS["logged_in"]):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if not rag_assistant.dependencies_available:
        return jsonify({"success": False, "message": f"RAG system unavailable: {rag_assistant.import_error}"}), 503

    if "files[]" not in request.files:
        return jsonify({"success": False, "message": ERROR_MESSAGES["no_files"]}), 400

    uploaded_files = request.files.getlist("files[]")
    success, files_data, error_message = prepare_files_data(uploaded_files)

    if not success:
        return jsonify({"success": False, "message": error_message}), 400

    process_result = rag_assistant.process_files(files_data)

    if process_result["success"]:
        try:
            # Update session with new uploaded file info
            for file_data in files_data:
                session[SESSION_KEYS["uploaded_files_info"]].append({"name": file_data["name"], "size": file_data["size"]})
            session.modified = True # Mark session as modified to save changes

            message = SUCCESS_MESSAGES["files_processed"].format(count=len(files_data))
            add_chat_message(session[SESSION_KEYS["chat_history"]], "system", message)
            return jsonify({"success": True, "message": str(message)})
        except Exception as e:
            return jsonify({"success": False, "message": f"Error processing upload: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "message": process_result["message"]}), 500

@app.route("/query", methods=["POST"])
def query():
    if not session.get(SESSION_KEYS["logged_in"]):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if not rag_assistant.dependencies_available:
        return jsonify({"success": False, "message": f"RAG system unavailable: {rag_assistant.import_error}"}), 503

    data = request.get_json()
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"success": False, "message": "Query cannot be empty"}), 400

    add_chat_message(session[SESSION_KEYS["chat_history"]], "user", user_query)

    ai_response = rag_assistant.query(user_query)
    if ai_response["success"]:
        try:
            response_text = str(ai_response["response"])
            if "processing_time" in ai_response:
                response_text += format_processing_time(ai_response["processing_time"])
            add_chat_message(session[SESSION_KEYS["chat_history"]], "bot", response_text)
            session.modified = True
            return jsonify({"success": True, "response": response_text})
        except Exception as e:
            return jsonify({"success": False, "message": f"Error processing response: {str(e)}"}), 500
    else:
        error_message = f"Error: {ai_response['response']}"
        add_chat_message(session[SESSION_KEYS["chat_history"]], "bot", error_message)
        session.modified = True
        return jsonify({"success": False, "message": error_message}), 500

@app.route("/clear_data", methods=["POST"])
def clear_data():
    if not session.get(SESSION_KEYS["logged_in"]):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if not rag_assistant.dependencies_available:
        return jsonify({"success": False, "message": f"RAG system unavailable: {rag_assistant.import_error}"}), 503

    rag_assistant.clear_data()
    session[SESSION_KEYS["uploaded_files_info"]] = []
    session[SESSION_KEYS["chat_history"]] = []
    add_chat_message(session[SESSION_KEYS["chat_history"]], "system", SUCCESS_MESSAGES["data_cleared"])
    session.modified = True
    return jsonify({"success": True, "message": SUCCESS_MESSAGES["data_cleared"]})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=7860)