import io
import logging
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
import pandas as pd
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image
from img2table.document import Image as ImgDoc, PDF
from img2table.ocr import TesseractOCR

logger = logging.getLogger(__name__)


def preprocess_scanned_image(pil_img: Image.Image) -> Image.Image:
    """Preprocess scanned page with Otsu binarization to enhance faint lines and text."""
    cv_img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


class TableExtractor:
    """Hybrid PDF table extraction engine for digital, scanned, and mixed PDFs."""

    def __init__(self, lang: str = "eng", n_threads: int = 2) -> None:
        self.ocr: Optional[TesseractOCR] = None
        try:
            self.ocr = TesseractOCR(n_threads=n_threads, lang=lang)
        except Exception as e:
            logger.warning(f"Tesseract OCR initialization failed: {e}. Scanned pages may not have OCR.")

    def extract_from_page(
        self, page_buffer: io.BytesIO, page_number: int
    ) -> List[Dict[str, Any]]:
        """
        Extract all tables from a single sliced PDF page.
        Uses vector analysis for digital pages and enhanced OCR for scanned pages.
        """
        page_bytes = page_buffer.getvalue()
        if not page_bytes:
            return []

        extracted_tables: List[Dict[str, Any]] = []

        # 1. Determine if page has digital text using pdfplumber
        has_digital_text = False
        pl_page = None
        try:
            pl_pdf = pdfplumber.open(io.BytesIO(page_bytes))
            if pl_pdf.pages:
                pl_page = pl_pdf.pages[0]
                text = pl_page.extract_text() or ""
                if len(text.strip()) > 30:
                    has_digital_text = True
        except Exception as e:
            logger.debug(f"pdfplumber text check error on page {page_number}: {e}")

        # 2. Strategy A: Digital / Selectable PDF page
        if has_digital_text and pl_page is not None:
            # Step A1: Extract vector tables via pdfplumber
            try:
                pl_tables = pl_page.extract_tables()
                for tbl_matrix in pl_tables:
                    if tbl_matrix and len(tbl_matrix) >= 2 and len(tbl_matrix[0]) >= 2:
                        df = pd.DataFrame(tbl_matrix)
                        extracted_tables.append({
                            "df": df,
                            "page": page_number,
                            "bbox": None,
                            "title": None,
                            "source": "digital_vector",
                        })
            except Exception as e:
                logger.debug(f"pdfplumber extraction error on page {page_number}: {e}")

            # Step A2: Extract borderless / semi-bordered tables via img2table digital mode
            try:
                doc = PDF(src=page_bytes, pdf_text_extraction=True)
                i2t_dict = doc.extract_tables(ocr=None, implicit_rows=True, borderless_tables=True)
                for page_tbls in i2t_dict.values():
                    for tbl in page_tbls:
                        if tbl.df is not None and not tbl.df.empty:
                            # Avoid duplicates if table was already extracted by vector parser
                            is_duplicate = False
                            for existing in extracted_tables:
                                if existing["df"].shape == tbl.df.shape:
                                    is_duplicate = True
                                    break
                            if not is_duplicate:
                                extracted_tables.append({
                                    "df": tbl.df.copy(),
                                    "page": page_number,
                                    "bbox": getattr(tbl, "bbox", None),
                                    "title": getattr(tbl, "title", None),
                                    "source": "digital_img2table",
                                })
            except Exception as e:
                logger.debug(f"img2table digital extraction error on page {page_number}: {e}")

        # 3. Strategy B: Scanned / Image-based PDF page
        else:
            try:
                pdfium_doc = pdfium.PdfDocument(page_bytes)
                if len(pdfium_doc) > 0:
                    pil_img = pdfium_doc[0].render(scale=2).to_pil()
                    preproc_img = preprocess_scanned_image(pil_img)
                    img_buf = io.BytesIO()
                    preproc_img.save(img_buf, format="PNG")
                    img_bytes = img_buf.getvalue()

                    img_doc = ImgDoc(src=img_bytes)
                    ocr_tables = img_doc.extract_tables(
                        ocr=self.ocr,
                        implicit_rows=True,
                        borderless_tables=True,
                    )
                    for tbl in ocr_tables:
                        if tbl.df is not None and not tbl.df.empty:
                            extracted_tables.append({
                                "df": tbl.df.copy(),
                                "page": page_number,
                                "bbox": getattr(tbl, "bbox", None),
                                "title": getattr(tbl, "title", None),
                                "source": "scanned_ocr",
                            })
            except Exception as e:
                logger.error(f"OCR extraction error on page {page_number}: {e}")

        return extracted_tables
