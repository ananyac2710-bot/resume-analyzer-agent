"""
pdf_parser.py - Tool for extracting text from PDF files.

This is a pure utility tool (no LLM calls). It uses PyMuPDF (fitz) to
read PDF pages and extract their text content.
"""

import pymupdf as fitz  # PyMuPDF — aliased as 'fitz' for convenience
import logging

logger = logging.getLogger("resume_analyzer")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.

    This tool handles several error cases:
    - Corrupt or unreadable PDFs
    - Empty PDFs (no text content)
    - Password-protected PDFs

    Args:
        pdf_bytes: The raw bytes of the uploaded PDF file.

    Returns:
        The extracted text from all pages of the PDF.

    Raises:
        ValueError: If the PDF cannot be read, is empty, or is protected.
    """
    try:
        # Open the PDF from bytes (not a file path, since Streamlit gives us bytes)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(
            f"Could not open the PDF file. It may be corrupt or not a valid PDF. "
            f"Error: {str(e)}"
        )

    # Check if the PDF is encrypted/password-protected
    if doc.is_encrypted:
        doc.close()
        raise ValueError(
            "This PDF is password-protected. Please upload an unprotected PDF."
        )

    # Extract text from each page
    all_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()

        if page_text.strip():  # Only add non-empty pages
            all_text.append(page_text)

    doc.close()

    # Combine all pages
    full_text = "\n\n".join(all_text)

    # Check if we actually got any text
    if not full_text.strip():
        raise ValueError(
            "The PDF appears to be empty or contains only images/scanned content. "
            "This tool requires text-based PDFs. If your resume is a scanned image, "
            "please convert it to a text-based PDF first."
        )

    logger.info(f"Extracted {len(full_text)} characters from {len(all_text)} pages")
    return full_text
