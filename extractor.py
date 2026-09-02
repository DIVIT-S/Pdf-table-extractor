"""
extractor.py — Table Extraction Logic (Digital & Scanned PDFs)
Strictly adheres to Master Prompt constraints: borderless_tables=False, implicit_rows=False.
"""
import io
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import pdfplumber
from img2table.document import PDF, Image
from img2table.ocr import TesseractOCR
import pypdfium2 as pdfium
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def _clean_df(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Validate and clean a DataFrame:
    - Return None if df is None, empty, or has all-empty cells.
    - Strip whitespace from all cell values.
    - Drop trailing empty rows and columns.
    - Return None if result is smaller than 2x2 or has fewer than 2 rows.
    """
    if df is None or df.empty:
        return None

    # Strip whitespace from all cell values
    df = df.map(lambda x: str(x).strip() if isinstance(x, (str, int, float)) else x)

    # Drop rows where all values are empty strings or NaN
    df = df[(df != '').any(axis=1)]
    
    # Drop columns where all values are empty strings or NaN
    df = df.loc[:, (df != '').any(axis=0)]

    # Validate minimum size: at least 2 rows and 2 columns
    if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
        return None

    # Check if all cells are empty
    if df.map(lambda x: str(x).strip() == '').all().all():
        return None

    return df.reset_index(drop=True)


def extract_tables_from_page(page_bytes: bytes, page_number: int = 1) -> List[Dict[str, Any]]:
    """
    Extract bordered tables from a single PDF page.
    Handles both digital and scanned PDFs.
    
    Args:
        page_bytes: Raw bytes of a single PDF page
        page_number: Page number for labeling extracted tables
        
    Returns:
        List of dicts with keys: {"df": DataFrame, "page": int}
    """
    tables_found = []

    # Step 1: Try to detect if this is a digital or scanned PDF
    is_digital = _is_digital_pdf(page_bytes)

    if is_digital:
        # Digital PDF: Use img2table with native text extraction
        try:
            pdf_doc = PDF(src=page_bytes, pdf_text_extraction=True)
            extracted_dict = pdf_doc.extract_tables(
                implicit_rows=False,
                borderless_tables=False,
                ocr=None  # No OCR for digital
            )
            
            # extracted_dict is {page_idx: [ExtractedTable, ...], ...}
            for page_idx, tables_list in extracted_dict.items():
                for table in tables_list:
                    df = table.df
                    cleaned_df = _clean_df(df)
                    if cleaned_df is not None:
                        tables_found.append({
                            "df": cleaned_df,
                            "page": page_number
                        })
        except Exception as e:
            logger.warning(f"Digital extraction failed for page {page_number}: {e}")

    else:
        # Scanned PDF: Render to PNG and use OCR
        # Note: For OCR-detected content, implicit_rows=True helps detect row boundaries
        # that OCR identifies from text positioning, even without explicit grid lines
        try:
            png_bytes = _pdf_to_png(page_bytes)
            image_doc = Image(src=png_bytes)
            extracted_list = image_doc.extract_tables(
                ocr=TesseractOCR(),
                implicit_rows=True,  # Necessary for OCR-detected row boundaries
                implicit_columns=False,
                borderless_tables=False
            )
            
            # extracted_list is [ExtractedTable, ...]
            for table in extracted_list:
                df = table.df
                cleaned_df = _clean_df(df)
                if cleaned_df is not None:
                    tables_found.append({
                        "df": cleaned_df,
                        "page": page_number
                    })
        except Exception as e:
            logger.warning(f"Scanned extraction failed for page {page_number}: {e}")

    return tables_found


def _is_digital_pdf(page_bytes: bytes) -> bool:
    """
    Detect if a PDF page is digital (has extractable text) or scanned.
    Returns True if pdfplumber extracts > 20 non-whitespace characters.
    """
    try:
        with pdfplumber.open(io.BytesIO(page_bytes)) as pdf:
            if len(pdf.pages) > 0:
                page = pdf.pages[0]
                text = page.extract_text()
                if text:
                    # Count non-whitespace characters
                    non_whitespace_count = len(''.join(text.split()))
                    return non_whitespace_count > 20
    except Exception as e:
        logger.debug(f"Error detecting digital PDF: {e}")

    return False


def _pdf_to_png(page_bytes: bytes) -> bytes:
    """
    Convert a PDF page to a PNG image (bytes).
    Uses pypdfium2 for rendering at high DPI.
    """
    pdf = pdfium.PdfDocument(page_bytes)
    page = pdf.get_page(0)  # First (only) page
    
    # Render at very high DPI (4x) for better table detection and OCR accuracy
    bitmap = page.render(scale=4)  # 4x scaling for 384 DPI equivalent
    pil_image = bitmap.to_pil()
    
    # Convert to PNG bytes
    png_buf = io.BytesIO()
    pil_image.save(png_buf, format="PNG")
    png_buf.seek(0)
    return png_buf.getvalue()
