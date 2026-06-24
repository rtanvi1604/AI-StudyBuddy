# ==========================================
# utils/rag.py
# ==========================================
# This file handles the complete RAG pipeline:
#   1. Split text into chunks
#   2. Generate embeddings using Sentence Transformers
#   3. Store embeddings in FAISS vector database
#   4. Search FAISS for relevant chunks
#   5. Send context + question to IBM Granite (via Ollama - FREE & LOCAL)
#   6. Return the AI-generated answer

import os
import json
import requests
import numpy as np
import faiss
from dotenv import load_dotenv

# ------------------------------------------
# IMPORTANT: Force offline mode BEFORE importing
# sentence_transformers. Without this, the library
# tries to contact huggingface.co on every startup
# to check for model updates - which fails/hangs on
# unstable networks, VPNs, or restrictive firewalls.
# Once the model is cached locally, we don't need
# the internet for it at all.
# ------------------------------------------
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# ------------------------------------------
# Configuration
# ------------------------------------------

# Folder where FAISS index and chunks are saved
VECTORSTORE_PATH = "vectorstore"
INDEX_FILE = os.path.join(VECTORSTORE_PATH, "index.faiss")
CHUNKS_FILE = os.path.join(VECTORSTORE_PATH, "chunks.json")

# Chunk settings
CHUNK_SIZE = 500        # Number of words per chunk
CHUNK_OVERLAP = 50      # Overlapping words between chunks

# How many chunks to retrieve for answering
TOP_K = 4

# Embedding model (free, runs locally, no API needed)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ------------------------------------------
# Ollama Settings (FREE local Granite model)
# ------------------------------------------
# Ollama runs Granite locally on your machine - no API key,
# no billing, no internet required after the model is downloaded.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "granite4:small-h")

# Load the embedding model once (reused across calls)
print("Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
print("Embedding model ready.")


# ------------------------------------------
# Step 1: Split Text into Chunks
# ------------------------------------------
def split_into_chunks(text):
    """
    Split the extracted PDF text into smaller overlapping chunks.

    Why chunks?
    - LLMs have a token/context limit.
    - Smaller chunks allow precise retrieval.
    - Overlap ensures no information is cut off at boundaries.

    Args:
        text (str): Full extracted text from the PDF.

    Returns:
        list: A list of text chunk strings.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        # Take a slice of words as one chunk
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Move forward but keep some overlap
        start += CHUNK_SIZE - CHUNK_OVERLAP

    print(f"Text split into {len(chunks)} chunks.")
    return chunks


# ------------------------------------------
# Step 2 & 3: Build and Save FAISS Vector Store
# ------------------------------------------
def build_vectorstore(text):
    """
    Generate embeddings for all chunks and store them in FAISS.

    Steps:
      1. Split text into chunks.
      2. Generate an embedding vector for each chunk.
      3. Build a FAISS index from all vectors.
      4. Save the index and chunks to disk.

    Args:
        text (str): Full extracted PDF text.
    """
    # Step 1: Split into chunks
    chunks = split_into_chunks(text)

    # Step 2: Generate embeddings for all chunks
    print("Generating embeddings...")
    embeddings = embedder.encode(chunks, show_progress_bar=True)

    # Convert to float32 (required by FAISS)
    embeddings = np.array(embeddings, dtype=np.float32)

    # Step 3: Build FAISS index
    # IndexFlatL2 = exact search using Euclidean distance
    dimension = embeddings.shape[1]  # Size of each embedding vector
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"FAISS index built with {index.ntotal} vectors.")

    # Step 4: Save FAISS index and chunks to disk
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    faiss.write_index(index, INDEX_FILE)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    print("Vector store saved successfully.")


# ------------------------------------------
# Step 4: Search FAISS for Relevant Chunks
# ------------------------------------------
def search_vectorstore(question):
    """
    Search the FAISS index for the most relevant chunks
    based on the user's question.

    Args:
        question (str): The user's question.

    Returns:
        list: Top-K most relevant text chunks.

    Raises:
        FileNotFoundError: If no vector store exists yet.
    """
    # Check if vector store exists
    if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError("Vector store not found. Please upload a PDF first.")

    # Load saved FAISS index
    index = faiss.read_index(INDEX_FILE)

    # Load saved chunks
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Embed the question using the same model
    question_embedding = embedder.encode([question])
    question_embedding = np.array(question_embedding, dtype=np.float32)

    # Search for TOP_K most similar chunks
    distances, indices = index.search(question_embedding, TOP_K)

    # Retrieve the actual text chunks
    relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]

    print(f"Retrieved {len(relevant_chunks)} relevant chunks.")
    return relevant_chunks


# ------------------------------------------
# Step 5 & 6: Ask Granite (via Ollama) using RAG
# ------------------------------------------
def answer_question(question):
    """
    Answer a user question using the RAG pipeline.

    Steps:
      1. Search FAISS for relevant chunks.
      2. Combine chunks into a context string.
      3. Build a prompt with context + question.
      4. Send prompt to Granite (running locally via Ollama).
      5. Return the answer.

    Args:
        question (str): The user's question.

    Returns:
        str: The AI-generated answer.
    """
    # Step 1: Retrieve relevant chunks from FAISS
    relevant_chunks = search_vectorstore(question)

    # Step 2: Combine chunks into one context block
    context = "\n\n".join(relevant_chunks)

    # Step 3: Build the RAG prompt
    # We clearly instruct the model to only use the provided context
    prompt = f"""You are a helpful study assistant.
Use ONLY the context below to answer the student's question.
If the answer is not found in the context, respond exactly with:
"I couldn't find this information in your uploaded notes."

Context from uploaded notes:
{context}

Student's Question: {question}

Answer:"""

    # Step 4: Call Granite via Ollama (free & local)
    answer = call_ibm_granite(prompt)

    return answer


# ------------------------------------------
# Granite API Call (via Ollama - FREE, runs locally)
# ------------------------------------------
def call_ibm_granite(prompt, max_tokens=400):
    """
    Send a prompt to IBM Granite running locally via Ollama
    and return the response.

    Ollama exposes an OpenAI-compatible API at:
        http://localhost:11434/v1/chat/completions

    This is completely free - no API key, no billing,
    no internet connection needed after the model is downloaded.

    Args:
        prompt (str): The full prompt to send.
        max_tokens (int): Maximum length of the response.

    Returns:
        str: The model's text response.

    Raises:
        Exception: If Ollama is not running or the request fails.
    """
    try:
        # Using Ollama's native /api/chat endpoint (most stable, works on
        # all Ollama versions - the newer /v1/chat/completions OpenAI-style
        # endpoint is only available on recent Ollama versions).
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,          # Get the full response at once
                "options": {
                    "temperature": 0.3,   # Lower = more factual answers
                    "num_predict": max_tokens
                }
            },
            timeout=120  # Local models can take time on first load
        )

        response.raise_for_status()
        data = response.json()

        # Extract the generated text (native Ollama response shape)
        answer = data["message"]["content"]
        return answer.strip()

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Ollama. "
            "Please make sure Ollama is running in the background."
        )

    except requests.exceptions.Timeout:
        raise Exception(
            "Ollama took too long to respond. "
            "The model may still be loading - please try again."
        )

    except requests.exceptions.HTTPError as e:
        # Common cause: model name in .env doesn't match a pulled model
        raise Exception(
            f"Ollama returned an error ({response.status_code}). "
            f"Check that '{OLLAMA_MODEL}' matches a model from 'ollama list'. "
            f"Details: {str(e)}"
        )

    except Exception as e:
        raise Exception(f"Granite (Ollama) error: {str(e)}")


# ------------------------------------------
# Helper: Get Context for Summary/Quiz/Flashcards
# ------------------------------------------
def get_full_context(query="main topics and key concepts", top_k=6):
    """
    Retrieve relevant chunks for summary, quiz, and flashcard generation.
    Uses a general query to get a broad overview of the document.

    Args:
        query (str): A broad query to retrieve key content.
        top_k (int): Number of chunks to retrieve.

    Returns:
        str: Combined context string from top chunks.

    Raises:
        FileNotFoundError: If no vector store exists.
    """
    if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError("Vector store not found. Please upload a PDF first.")

    # Load index and chunks
    index = faiss.read_index(INDEX_FILE)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Embed the query
    query_embedding = embedder.encode([query])
    query_embedding = np.array(query_embedding, dtype=np.float32)

    # Search for top_k chunks
    _, indices = index.search(query_embedding, min(top_k, len(chunks)))
    relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]

    return "\n\n".join(relevant_chunks)