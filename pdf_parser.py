import io
from pypdf import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts raw text content from uploaded PDF byte stream."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()