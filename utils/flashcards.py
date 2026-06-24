# ==========================================
# utils/flashcards.py
# ==========================================
# This file generates question-answer
# flashcards from the uploaded PDF notes
# using IBM Granite.
#
# Flow:
#   1. Retrieve relevant chunks from FAISS
#   2. Build a flashcard generation prompt
#   3. Parse the JSON response from Granite
#   4. Return a clean list of flashcards

import json
import re
from utils.rag import get_full_context, call_ibm_granite


# ------------------------------------------
# Main Function: Generate Flashcards
# ------------------------------------------
def generate_flashcards():
    """
    Generate question-answer flashcards from
    the uploaded PDF notes.

    Steps:
      1. Get relevant context from FAISS vector store.
      2. Send context to IBM Granite with a flashcard prompt.
      3. Parse the JSON response into a list of flashcards.
      4. Return the structured flashcard data.

    Returns:
        list: A list of flashcard dictionaries.
              Each dict has: question, answer.

    Raises:
        FileNotFoundError: If no PDF has been uploaded yet.
        Exception: If flashcard generation or parsing fails.
    """

    # Step 1: Get context from FAISS
    # Use a broad query to retrieve key concept chunks
    context = get_full_context(
        query="key concepts, definitions, important terms, facts",
        top_k=6
    )

    # Step 2: Build the flashcard prompt
    # We ask Granite to return strict JSON for easy parsing
    prompt = f"""You are an expert study assistant creating flashcards for students.
Read the study material below and generate exactly 6 flashcards.

Rules:
- Each flashcard must have a clear, specific question.
- Each answer must be concise and accurate (1-3 sentences).
- Base all flashcards strictly on the provided study material.
- Cover different topics from the material.
- Return ONLY a valid JSON array. No extra text or explanation.

Return format:
[
  {{
    "question": "Your question here?",
    "answer": "Your concise answer here."
  }}
]

Study Material:
{context}

JSON Output:"""

    # Step 3: Call IBM Granite
    raw_response = call_ibm_granite(prompt, max_tokens=1000)

    # Step 4: Parse the response into structured data
    flashcards_data = parse_flashcards_response(raw_response)

    return flashcards_data


# ------------------------------------------
# Helper: Parse Flashcards JSON Response
# ------------------------------------------
def parse_flashcards_response(raw_response):
    """
    Extract and parse the JSON flashcard data
    from Granite's raw response.

    Sometimes the model adds extra text around
    the JSON. This function handles that safely.

    Args:
        raw_response (str): Raw text response from IBM Granite.

    Returns:
        list: Parsed list of flashcard dictionaries.

    Raises:
        Exception: If valid JSON cannot be extracted.
    """

    try:
        # First attempt: direct JSON parse
        flashcards_data = json.loads(raw_response.strip())
        return validate_flashcards(flashcards_data)

    except json.JSONDecodeError:
        pass

    # Second attempt: find JSON array using regex
    # Handles cases where Granite adds text before/after JSON
    try:
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if match:
            flashcards_data = json.loads(match.group())
            return validate_flashcards(flashcards_data)

    except (json.JSONDecodeError, AttributeError):
        pass

    # If both attempts fail, raise a clear error
    raise Exception(
        "Could not parse flashcard response. "
        "The AI response was not in the expected format. "
        "Please try again."
    )


# ------------------------------------------
# Helper: Validate Flashcards Structure
# ------------------------------------------
def validate_flashcards(flashcards_data):
    """
    Validate that the flashcard data has the
    correct structure and all required fields.

    Skips any incomplete cards instead of crashing.

    Args:
        flashcards_data (list): Parsed flashcard list from JSON.

    Returns:
        list: Validated and cleaned flashcard data.

    Raises:
        Exception: If no valid flashcards are found.
    """

    if not isinstance(flashcards_data, list):
        raise Exception("Flashcard data must be a list.")

    validated = []

    for item in flashcards_data:

        # Skip if not a dictionary
        if not isinstance(item, dict):
            continue

        question = item.get("question", "").strip()
        answer   = item.get("answer", "").strip()

        # Skip cards missing question or answer
        if not question or not answer:
            continue

        validated.append({
            "question": question,
            "answer":   answer
        })

    # Make sure we have at least 1 valid flashcard
    if not validated:
        raise Exception(
            "No valid flashcards could be generated. "
            "Please try again or upload a different PDF."
        )

    return validated