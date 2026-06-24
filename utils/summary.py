# ==========================================
# utils/summary.py
# ==========================================
# This file generates a concise summary of
# the uploaded PDF notes using IBM Granite.
#
# Flow:
#   1. Retrieve relevant chunks from FAISS
#   2. Build a summarization prompt
#   3. Send prompt to IBM Granite
#   4. Return the generated summary

from utils.rag import get_full_context, call_ibm_granite


# ------------------------------------------
# Main Function: Generate Summary
# ------------------------------------------
def generate_summary():
    """
    Generate a concise summary of the uploaded PDF notes.

    Steps:
      1. Retrieve the most relevant chunks from
         the FAISS vector store using a broad query.
      2. Combine chunks into a single context block.
      3. Build a clear summarization prompt.
      4. Send the prompt to IBM Granite.
      5. Return the clean summary text.

    Returns:
        str: A well-structured summary of the notes.

    Raises:
        FileNotFoundError: If no PDF has been uploaded yet.
        Exception: If summary generation fails.
    """

    # Step 1: Get relevant content from FAISS
    # We use a broad query to pull the most important chunks
    context = get_full_context(
        query="main topics, key concepts, important points, summary",
        top_k=6
    )

    # Step 2: Build the summarization prompt
    # We instruct Granite to be concise and well-structured
    prompt = f"""You are a helpful study assistant.
Read the study notes below and write a clear, concise summary.

Instructions:
- Start with a one-sentence overview of the main topic.
- List the key concepts and important points.
- Keep the summary easy to understand for a student.
- Use simple, clear language.
- Do NOT add any information that is not in the notes.

Study Notes:
{context}

Summary:"""

    # Step 3: Call IBM Granite to generate the summary
    # We use more tokens here since summaries can be longer
    summary = call_ibm_granite(prompt, max_tokens=600)

    # Step 4: Clean and return the summary
    summary = summary.strip()

    if not summary:
        raise Exception(
            "The AI returned an empty summary. Please try again."
        )

    return summary