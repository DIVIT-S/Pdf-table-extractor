import io
import math
from typing import Union
from pypdf import PdfReader, PdfWriter


def get_pdf_page_count(pdf_source: Union[bytes, io.BytesIO]) -> int:
    """Return total number of pages in a PDF stream or bytes."""
    stream = io.BytesIO(pdf_source) if isinstance(pdf_source, bytes) else pdf_source
    stream.seek(0)
    reader = PdfReader(stream)
    return len(reader.pages)


def slice_pdf_page(pdf_source: Union[bytes, io.BytesIO], page_index: int) -> io.BytesIO:
    """Slice a single page from a PDF into an isolated in-memory buffer."""
    stream = io.BytesIO(pdf_source) if isinstance(pdf_source, bytes) else pdf_source
    stream.seek(0)
    reader = PdfReader(stream)
    
    if page_index < 0 or page_index >= len(reader.pages):
        raise IndexError(f"Page index {page_index} out of range (0..{len(reader.pages) - 1})")
    
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])
    
    out_buffer = io.BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default value on ZeroDivisionError or invalid inputs."""
    if denominator == 0 or math.isnan(denominator) or math.isnan(numerator):
        return default
    return numerator / denominator


def clean_cell_str(val: object) -> str:
    """Normalize cell values to clean stripped strings."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null"):
        return ""
    # Normalize unicode whitespace
    s = " ".join(s.split())
    return s
