# ==========================================
# utils/pdf_reader.py
# ==========================================
# This file handles extracting text from
# uploaded PDF files using PyMuPDF (fitz).
#
# PyMuPDF is fast, accurate, and works well
# with most PDF types including scanned ones.

import os
import fitz  # PyMuPDF library (imported as fitz)


# ------------------------------------------
# Main Function: Extract Text from PDF
# ------------------------------------------
def extract_text_from_pdf(filepath):
    """
    Extract all text from a PDF file, page by page.

    Steps:
      1. Open the PDF file using PyMuPDF.
      2. Loop through every page.
      3. Extract text from each page.
      4. Clean and combine all text.
      5. Return the full text as one string.

    Args:
        filepath (str): Full path to the uploaded PDF file.

    Returns:
        str: All extracted text from the PDF.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        Exception: If the PDF cannot be read or is corrupted.
    """

    # Check if the file actually exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDF file not found: {filepath}")

    # Check if the file is empty
    if os.path.getsize(filepath) == 0:
        raise Exception("The uploaded PDF file is empty.")

    try:
        # Open the PDF using PyMuPDF
        pdf_document = fitz.open(filepath)

        # Check if PDF has any pages
        if pdf_document.page_count == 0:
            raise Exception("The PDF has no pages.")

        print(f"PDF opened: {pdf_document.page_count} pages found.")

        # Store text from all pages
        all_text = []

        # Loop through every page
        for page_number in range(pdf_document.page_count):

            # Get the current page
            page = pdf_document[page_number]

            # Extract text from this page
            page_text = page.get_text()

            # Only add if the page has actual content
            if page_text.strip():
                all_text.append(page_text)

        # Close the PDF document to free memory
        pdf_document.close()

        # Combine all pages into one big string
        full_text = "\n\n".join(all_text)

        # Clean the extracted text
        full_text = clean_text(full_text)

        print(f"Text extracted: {len(full_text)} characters.")
        return full_text

    except fitz.FileDataError:
        raise Exception(
            "Could not read the PDF. "
            "The file may be corrupted or password-protected."
        )

    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")


# ------------------------------------------
# Helper Function: Clean Extracted Text
# ------------------------------------------
def clean_text(text):
    """
    Clean the raw extracted text by removing
    unwanted characters and extra whitespace.

    Args:
        text (str): Raw extracted text from PDF.

    Returns:
        str: Cleaned and normalized text.
    """
    # Replace null bytes and special control characters
    text = text.replace("\x00", "")

    # Replace multiple blank lines with just two newlines
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)

    # Strip leading and trailing whitespace
    text = text.strip()

    return text


# ------------------------------------------
# Helper Function: Get PDF Info
# ------------------------------------------
def get_pdf_info(filepath):
    """
    Get basic information about the uploaded PDF.
    Useful for displaying file details to the user.

    Args:
        filepath (str): Full path to the PDF file.

    Returns:
        dict: Dictionary with page_count and file_size.
    """
    try:
        pdf_document = fitz.open(filepath)
        info = {
            "page_count": pdf_document.page_count,
            "file_size_kb": round(os.path.getsize(filepath) / 1024, 1)
        }
        pdf_document.close()
        return info

    except Exception:
        return {"page_count": 0, "file_size_kb": 0}