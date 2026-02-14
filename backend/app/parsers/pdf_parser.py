"""PDF document parser using PyMuPDF."""

import fitz  # PyMuPDF


def parse_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)


def parse_pdf_bytes(data: bytes) -> str:
    """Extract text content from PDF bytes."""
    doc = fitz.open(stream=data, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)
