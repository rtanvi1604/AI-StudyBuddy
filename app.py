# ==========================================
# AI Study Buddy - Main Flask Application
# ==========================================
# This file is the entry point of the app.
# It defines all the routes (URLs) that the
# frontend will call to use AI features.

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables from .env file
load_dotenv()

# Import our utility modules
from utils.pdf_reader import extract_text_from_pdf
from utils.rag import build_vectorstore, answer_question
from utils.summary import generate_summary
from utils.quiz import generate_quiz
from utils.flashcards import generate_flashcards

# ------------------------------------------
# App Configuration
# ------------------------------------------
app = Flask(__name__)
CORS(app)  # Allow frontend to talk to backend

# Folder where uploaded PDFs will be saved
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum file size: 20MB
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_FILE_SIZE_MB", 20)) * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {"pdf"}

# ------------------------------------------
# Helper Function
# ------------------------------------------
def allowed_file(filename):
    """Check if the uploaded file is a PDF."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------------------------
# Route 1: Home Page
# ------------------------------------------
@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


# ------------------------------------------
# Route 2: Upload PDF
# ------------------------------------------
@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Handles PDF upload.
    Steps:
      1. Receive the uploaded PDF file.
      2. Save it to the uploads/ folder.
      3. Extract text from the PDF.
      4. Build FAISS vector store from the text.
      5. Return success message.
    """
    # Check if a file was sent
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    # Check if a filename exists
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Check if it is a PDF
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        # Save the file safely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Step 1: Extract text from PDF
        text = extract_text_from_pdf(filepath)

        if not text.strip():
            return jsonify({"error": "Could not extract text from this PDF. Try another file."}), 400

        # Step 2: Build vector store (chunking + embeddings + FAISS)
        build_vectorstore(text)

        return jsonify({
            "success": True,
            "message": f"'{filename}' uploaded and processed successfully!",
            "pages": text.count("\n\n"),  # Rough page estimate
            "characters": len(text)
        })

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


# ------------------------------------------
# Route 3: Chat (Ask a Question)
# ------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles user questions using RAG.
    Steps:
      1. Receive user question.
      2. Search FAISS for relevant chunks.
      3. Send context + question to IBM Granite.
      4. Return the AI answer.
    """
    data = request.get_json()

    # Validate input
    if not data or "question" not in data:
        return jsonify({"error": "Please provide a question"}), 400

    question = data["question"].strip()

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    try:
        answer = answer_question(question)
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer
        })

    except FileNotFoundError:
        return jsonify({"error": "Please upload a PDF first before asking questions."}), 400

    except Exception as e:
        return jsonify({"error": f"Could not answer: {str(e)}"}), 500


# ------------------------------------------
# Route 4: Generate Summary
# ------------------------------------------
@app.route("/summary", methods=["POST"])
def summary():
    """
    Generates a concise summary of the uploaded PDF.
    """
    try:
        result = generate_summary()
        return jsonify({
            "success": True,
            "summary": result
        })

    except FileNotFoundError:
        return jsonify({"error": "Please upload a PDF first."}), 400

    except Exception as e:
        return jsonify({"error": f"Summary failed: {str(e)}"}), 500


# ------------------------------------------
# Route 5: Generate Quiz
# ------------------------------------------
@app.route("/quiz", methods=["POST"])
def quiz():
    """
    Generates 5 multiple-choice questions from the uploaded PDF.
    """
    try:
        result = generate_quiz()
        return jsonify({
            "success": True,
            "quiz": result
        })

    except FileNotFoundError:
        return jsonify({"error": "Please upload a PDF first."}), 400

    except Exception as e:
        return jsonify({"error": f"Quiz generation failed: {str(e)}"}), 500


# ------------------------------------------
# Route 6: Generate Flashcards
# ------------------------------------------
@app.route("/flashcards", methods=["POST"])
def flashcards():
    """
    Generates question-answer flashcards from the uploaded PDF.
    """
    try:
        result = generate_flashcards()
        return jsonify({
            "success": True,
            "flashcards": result
        })

    except FileNotFoundError:
        return jsonify({"error": "Please upload a PDF first."}), 400

    except Exception as e:
        return jsonify({"error": f"Flashcard generation failed: {str(e)}"}), 500


# ------------------------------------------
# Run the App
# ------------------------------------------
if __name__ == "__main__":
    # Create required folders if they don't exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("vectorstore", exist_ok=True)

    print("=" * 45)
    print("  AI Study Buddy is running!")
    print("  Open: http://localhost:5000")
    print("=" * 45)

    app.run(debug=os.getenv("FLASK_DEBUG", "True") == "True", port=5000)