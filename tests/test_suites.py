"""
tests/test_suites.py — Mandatory Test Suites + Schema Consolidation Tests
"""
import io
import os
import pandas as pd
import pytest
from PIL import Image, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from extractor import extract_tables_from_page
from exporter import consolidate_tables, export_tables_to_excel
from extractor import extract_tables_from_page, _clean_df


# ── PDF Generation Helpers ───────────────────────────────────────────────────

def make_digital_table_pdf() -> bytes:
    """Generate a digital PDF with a single bordered table."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    data = [
        ["ID", "Product", "Price"],
        ["101", "Laptop", "$1200"],
        ["102", "Mouse", "$25"],
        ["103", "Keyboard", "$75"],
    ]
    t = Table(data, colWidths=[100, 150, 100])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    doc.build([t])
    return buf.getvalue()


def make_borderless_text_pdf() -> bytes:
    """Generate a PDF with borderless spaced columns and narrative text."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Executive Summary and Report Overview", styles["Heading1"]),
        Paragraph("This document contains multi-column narrative text without ruling lines.", styles["Normal"]),
        Paragraph("Column 1                   Column 2                   Column 3", styles["Normal"]),
        Paragraph("Value Alpha                Value Beta                 Value Gamma", styles["Normal"]),
        Paragraph("Value Delta                Value Epsilon              Value Zeta", styles["Normal"]),
        Paragraph("End of narrative section with standard paragraph structure.", styles["Normal"]),
    ]
    doc.build(story)
    return buf.getvalue()


def make_chart_pdf() -> bytes:
    """Generate a PDF with a bar chart and axis lines (no closed grid table)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "Quarterly Revenue Breakdown Chart")
    c.line(100, 400, 100, 700)
    c.line(100, 400, 500, 400)
    c.line(100, 500, 500, 500)
    c.line(100, 600, 500, 600)
    c.rect(130, 400, 40, 150, fill=1, stroke=0)
    c.rect(200, 400, 40, 220, fill=1, stroke=0)
    c.rect(270, 400, 40, 180, fill=1, stroke=0)
    c.rect(340, 400, 40, 260, fill=1, stroke=0)
    c.drawString(130, 385, "Q1")
    c.drawString(200, 385, "Q2")
    c.drawString(270, 385, "Q3")
    c.drawString(340, 385, "Q4")
    c.save()
    return buf.getvalue()


def make_scanned_table_pdf() -> bytes:
    """Generate an image-only (scanned) PDF with a bordered table."""
    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([50, 50, 550, 200], outline="black", width=2)
    draw.line([50, 100, 550, 100], fill="black", width=2)
    draw.line([50, 150, 550, 150], fill="black", width=2)
    draw.line([200, 50, 200, 200], fill="black", width=2)
    draw.line([380, 50, 380, 200], fill="black", width=2)

    draw.text((70, 70), "Item", fill="black")
    draw.text((220, 70), "Qty", fill="black")
    draw.text((400, 70), "Price", fill="black")

    draw.text((70, 120), "Apples", fill="black")
    draw.text((220, 120), "10", fill="black")
    draw.text((400, 120), "5.00", fill="black")

    draw.text((70, 170), "Oranges", fill="black")
    draw.text((220, 170), "20", fill="black")
    draw.text((400, 170), "8.00", fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def make_3page_mixed_schema_pdf() -> bytes:
    """Generate a 3-page PDF: Pages 1 & 2 share schema (same table continued), Page 3 has different schema."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    # Page 1: Schema (ID, Item, Cost)
    c.drawString(50, 750, "Page 1 - Inventory Part 1")
    x0, y0, w, h = 50, 500, 450, 150
    c.rect(x0, y0, w, h, stroke=1, fill=0)
    c.line(x0, y0 + 50, x0 + w, y0 + 50)
    c.line(x0, y0 + 100, x0 + w, y0 + 100)
    c.line(x0 + 150, y0, x0 + 150, y0 + h)
    c.line(x0 + 300, y0, x0 + 300, y0 + h)
    c.drawString(x0 + 20, y0 + 115, "ID")
    c.drawString(x0 + 170, y0 + 115, "Item")
    c.drawString(x0 + 320, y0 + 115, "Cost")
    c.drawString(x0 + 20, y0 + 65, "101")
    c.drawString(x0 + 170, y0 + 65, "Pen")
    c.drawString(x0 + 320, y0 + 65, "10")
    c.drawString(x0 + 20, y0 + 15, "102")
    c.drawString(x0 + 170, y0 + 15, "Notebook")
    c.drawString(x0 + 320, y0 + 15, "25")
    c.showPage()

    # Page 2: Same Schema (ID, Item, Cost) -> should merge with Page 1 into Table 1
    c.drawString(50, 750, "Page 2 - Inventory Part 2")
    c.rect(x0, y0, w, h, stroke=1, fill=0)
    c.line(x0, y0 + 50, x0 + w, y0 + 50)
    c.line(x0, y0 + 100, x0 + w, y0 + 100)
    c.line(x0 + 150, y0, x0 + 150, y0 + h)
    c.line(x0 + 300, y0, x0 + 300, y0 + h)
    c.drawString(x0 + 20, y0 + 115, "ID")
    c.drawString(x0 + 170, y0 + 115, "Item")
    c.drawString(x0 + 320, y0 + 115, "Cost")
    c.drawString(x0 + 20, y0 + 65, "103")
    c.drawString(x0 + 170, y0 + 65, "Eraser")
    c.drawString(x0 + 320, y0 + 65, "5")
    c.drawString(x0 + 20, y0 + 15, "104")
    c.drawString(x0 + 170, y0 + 15, "Ruler")
    c.drawString(x0 + 320, y0 + 15, "15")
    c.showPage()

    # Page 3: Different Schema (Dept, Manager) -> should become Table 2
    c.drawString(50, 750, "Page 3 - Department Summary")
    c.rect(x0, y0, 300, 100, stroke=1, fill=0)
    c.line(x0, y0 + 50, x0 + 300, y0 + 50)
    c.line(x0 + 150, y0, x0 + 150, y0 + 100)
    c.drawString(x0 + 20, y0 + 65, "Dept")
    c.drawString(x0 + 170, y0 + 65, "Manager")
    c.drawString(x0 + 20, y0 + 15, "Finance")
    c.drawString(x0 + 170, y0 + 15, "Sarah")
    c.showPage()

    c.save()
    return buf.getvalue()


def make_zero_table_pdf() -> bytes:
    """Generate a PDF with only regular text and zero bordered tables."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, "This is a document with no tables whatsoever.")
    c.drawString(100, 680, "Just standard text sentences spanning multiple lines.")
    c.save()
    return buf.getvalue()


# ── Test Suites ──────────────────────────────────────────────────────────────

def test_suite_1_digital_extraction():
    """Digital PDF with a visible grid table is correctly extracted."""
    pdf_bytes = make_digital_table_pdf()
    tables = extract_tables_from_page(pdf_bytes, page_number=1)
    assert len(tables) == 1
    assert tables[0]["page"] == 1
    df = tables[0]["df"]
    assert df.shape[0] >= 3
    assert df.shape[1] == 3


def test_suite_2_anti_hallucination():
    """PDF with borderless spaced tables / narrative text produces no output."""
    pdf_bytes = make_borderless_text_pdf()
    tables = extract_tables_from_page(pdf_bytes, page_number=1)
    assert len(tables) == 0


def test_suite_3_chart_rejection():
    """PDF containing a chart with axis gridlines produces no false table output."""
    pdf_bytes = make_chart_pdf()
    tables = extract_tables_from_page(pdf_bytes, page_number=1)
    assert len(tables) == 0


def test_suite_4_scanned_ocr():
    """Scanned image-only PDF with bordered table is extracted via OCR path."""
    pdf_bytes = make_scanned_table_pdf()
    tables = extract_tables_from_page(pdf_bytes, page_number=1)
    assert len(tables) == 1
    df = tables[0]["df"]
    assert df.shape[0] >= 2
    assert df.shape[1] >= 2


def test_suite_5_schema_consolidation_and_export():
    """Verify tables with matching headers merge across pages, while distinct schemas create separate tables in single sheet."""
    from pypdf import PdfReader, PdfWriter
    pdf_bytes = make_3page_mixed_schema_pdf()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 3

    all_raw = []
    for idx, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        pbuf = io.BytesIO()
        writer.write(pbuf)
        tables = extract_tables_from_page(pbuf.getvalue(), page_number=idx + 1)
        all_raw.extend(tables)

    assert len(all_raw) == 3

    # Consolidation step
    consolidated = consolidate_tables(all_raw)
    assert len(consolidated) == 2, "Page 1 and 2 should merge into Table 1, Page 3 should be Table 2"
    assert consolidated[0]["table_num"] == 1
    assert consolidated[0]["pages"] == [1, 2]
    assert consolidated[0]["df"].shape[0] == 5  # 1 header + 2 data rows from P1 + 2 data rows from P2
    assert consolidated[0]["df"].shape[1] == 3

    assert consolidated[1]["table_num"] == 2
    assert consolidated[1]["pages"] == [3]
    assert consolidated[1]["df"].shape[0] == 2  # 1 header + 1 data row
    assert consolidated[1]["df"].shape[1] == 2

    # Export to Excel step
    dfs_to_export = [g["df"] for g in consolidated]
    excel_bytes = export_tables_to_excel(dfs_to_export)
    assert len(excel_bytes) > 0

    xl = pd.ExcelFile(io.BytesIO(excel_bytes), engine="openpyxl")
    assert xl.sheet_names == ["All_Tables"]

    df_out = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="All_Tables", header=None)
    col0 = [str(x) for x in df_out[0]]
    assert any("Table 1" in s for s in col0)
    assert any("Table 2" in s for s in col0)


def test_suite_6_null_set_handler():
    """PDF with zero bordered tables outputs exact null message without fabricating tables."""
    pdf_bytes = make_zero_table_pdf()
    tables = extract_tables_from_page(pdf_bytes, page_number=1)
    assert len(tables) == 0

    excel_bytes = export_tables_to_excel(tables)
    df_out = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="All_Tables", header=None)
    assert df_out.shape == (1, 1)
    assert df_out.iloc[0, 0] == "No bordered tables were detected in this document."


def test_clean_df_logic():
    """Verify DataFrame cleaning drops empty rows/cols and rejects < 2x2 candidates."""
    assert _clean_df(None) is None
    assert _clean_df(pd.DataFrame()) is None
    assert _clean_df(pd.DataFrame([["", ""], ["", ""]])) is None
    assert _clean_df(pd.DataFrame([["Single row", "Value"]])) is None

    valid_df = pd.DataFrame([
        [" Header 1 ", " Header 2 "],
        ["Val 1", "Val 2"],
        ["", ""],
    ])
    cleaned = _clean_df(valid_df)
    assert cleaned is not None
    assert cleaned.shape == (2, 2)
    assert cleaned.iloc[0, 0] == "Header 1"
