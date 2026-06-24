# ==========================================
# utils/quiz.py
# ==========================================
# This file generates multiple-choice quiz
# questions from the uploaded PDF notes.
#
# Flow:
#   1. Retrieve relevant chunks from FAISS
#   2. Build a prompt asking Granite for MCQs
#   3. Parse the response into structured data
#   4. Return a clean list of questions

import json
import re
from utils.rag import get_full_context, call_ibm_granite


# ------------------------------------------
# Main Function: Generate Quiz
# ------------------------------------------
def generate_quiz():
    """
    Generate 5 multiple-choice questions from the uploaded PDF.

    Steps:
      1. Get relevant context from FAISS vector store.
      2. Send context to IBM Granite with a quiz prompt.
      3. Parse the JSON response into a list of questions.
      4. Return the structured quiz data.

    Returns:
        list: A list of 5 quiz question dictionaries.
              Each dict has: question, options (A-D), answer.

    Raises:
        FileNotFoundError: If no PDF has been uploaded yet.
        Exception: If quiz generation or parsing fails.
    """

    # Step 1: Get context from FAISS
    # We use a broad query to get the most important content
    context = get_full_context(
        query="important concepts, definitions, key facts",
        top_k=6
    )

    # Step 2: Build the quiz prompt
    # We ask Granite to return strict JSON so we can parse it easily
    prompt = f"""You are an expert quiz generator for students.
Read the study material below and generate exactly 5 multiple-choice questions.

Rules:
- Each question must have exactly 4 options labeled A, B, C, D.
- Only one option should be correct.
- Base all questions strictly on the provided study material.
- Return ONLY a valid JSON array. No extra text or explanation.

Return format:
[
  {{
    "question": "Your question here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "answer": "A"
  }}
]

Study Material:
{context}

JSON Output:"""

    # Step 3: Call IBM Granite
    # Using a higher token budget since 5 MCQ questions with 4 options
    # each is a lot of structured JSON for smaller local models to produce
    raw_response = call_ibm_granite(prompt, max_tokens=1800)

    # Debug: print raw response so we can see exactly what the model
    # returned if parsing fails. Remove this once everything is stable.
    print("=" * 50)
    print("RAW QUIZ RESPONSE FROM GRANITE:")
    print(raw_response)
    print("=" * 50)

    # Step 4: Parse the response into structured data
    quiz_data = parse_quiz_response(raw_response)

    return quiz_data


# ------------------------------------------
# Helper: Parse Quiz JSON Response
# ------------------------------------------
def parse_quiz_response(raw_response):
    """
    Extract and parse the JSON quiz data from Granite's response.

    Sometimes the model adds extra text around the JSON.
    This function finds and extracts just the JSON array.

    Args:
        raw_response (str): Raw text response from IBM Granite.

    Returns:
        list: Parsed list of quiz question dictionaries.

    Raises:
        Exception: If valid JSON cannot be extracted.
    """
    try:
        # First attempt: direct JSON parse
        quiz_data = json.loads(raw_response.strip())
        return validate_quiz(quiz_data)

    except json.JSONDecodeError:
        pass

    # Second attempt: find JSON array using regex
    # This handles cases where Granite adds text before/after JSON
    try:
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if match:
            quiz_data = json.loads(match.group())
            return validate_quiz(quiz_data)

    except (json.JSONDecodeError, AttributeError):
        pass

    # Third attempt: repair common small-model JSON mistakes
    # (trailing commas, single quotes) then retry parsing
    try:
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if match:
            repaired = repair_json(match.group())
            quiz_data = json.loads(repaired)
            return validate_quiz(quiz_data)

    except (json.JSONDecodeError, AttributeError):
        pass

    # If all attempts fail, raise a clear error
    raise Exception(
        "Could not parse quiz response. "
        "The AI response was not in the expected format. "
        "Please try again."
    )


# ------------------------------------------
# Helper: Repair Common Small-Model JSON Mistakes
# ------------------------------------------
def repair_json(text):
    """
    Fix common JSON formatting mistakes that small local models
    sometimes make, so the response can still be parsed.

    Fixes:
      - Missing opening quote on a value, e.g. "A": Wildlife Conservation"
        (small models sometimes forget the opening quote but keep the
        closing one - this was the exact bug seen with granite4:micro)
      - Trailing commas before ] or }

    Note: We deliberately do NOT do a global single-quote -> double-quote
    replacement here. That would also corrupt legitimate apostrophes
    inside correctly-quoted strings (e.g. "one's body"), turning valid
    JSON into broken JSON. It's safer to fail and retry than to mangle
    good text.

    Args:
        text (str): Raw JSON-like string that failed to parse.

    Returns:
        str: Repaired JSON string (still needs to be parsed).
    """
    # Fix missing opening quote: "A": Some text"  ->  "A": "Some text"
    # Matches a JSON key like "A": followed by a value that starts with
    # a letter (no opening quote) but still has a closing quote.
    text = re.sub(
        r'("[A-Za-z0-9_]+"\s*:\s*)([A-Za-z][^"]*?)(")',
        r'\1"\2\3',
        text
    )

    # Remove trailing commas like [1, 2, 3,] or {"a": 1,}
    text = re.sub(r',(\s*[\]}])', r'\1', text)

    return text


# ------------------------------------------
# Helper: Validate Quiz Structure
# ------------------------------------------
def validate_quiz(quiz_data):
    """
    Validate that the quiz data has the correct structure.
    Fixes minor issues and ensures all required fields exist.

    Args:
        quiz_data (list): Parsed quiz list from JSON.

    Returns:
        list: Validated and cleaned quiz data.

    Raises:
        Exception: If the data structure is invalid.
    """
    if not isinstance(quiz_data, list):
        raise Exception("Quiz data must be a list of questions.")

    validated = []

    for i, item in enumerate(quiz_data):
        # Check required fields exist
        if not isinstance(item, dict):
            continue

        question = item.get("question", "").strip()
        options = item.get("options", {})
        answer = item.get("answer", "").strip().upper()

        # Skip items missing required fields
        if not question or not options or not answer:
            continue

        # Ensure options has A, B, C, D
        if not all(k in options for k in ["A", "B", "C", "D"]):
            continue

        # Ensure answer is one of A, B, C, D
        if answer not in ["A", "B", "C", "D"]:
            answer = "A"  # Default fallback

        validated.append({
            "question": question,
            "options": {
                "A": options.get("A", "").strip(),
                "B": options.get("B", "").strip(),
                "C": options.get("C", "").strip(),
                "D": options.get("D", "").strip()
            },
            "answer": answer
        })

    # Make sure we have at least 1 valid question
    if not validated:
        raise Exception(
            "No valid questions could be generated. "
            "Please try again or upload a different PDF."
        )

    return validated