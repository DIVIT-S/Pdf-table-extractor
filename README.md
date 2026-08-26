# PDF Table Extractor

A local, high-precision Streamlit web application designed to automatically detect, reconstruct, stitch, and export tables from any PDF document (selectable digital text, scanned images, or mixed layouts) into clean Excel (`.xlsx`) workbooks.

---

## Key Features

- **Hybrid Extraction Engine**:
  - **Selectable / Digital PDFs**: Fast vector table extraction with `pdfplumber` combined with digital `img2table` parsing to capture both bordered and borderless (spaced) tables.
  - **Scanned / Image PDFs**: Enhanced with Otsu image binarization and `TesseractOCR` fallback to accurately detect faint borders and line-item matrices.
- **Anti-Hallucination & Quality Filtering**:
  - Automatically detects and discards non-table structures (multiple-choice questionnaires, quiz options, Table of Contents with dot leaders, numbered/bulleted lists, footnotes, and multi-column narrative article layouts).
  - Eliminates empty matrices and single-header artifacts (requires at least 2 valid data rows and ≥ 35% non-blank cell density).
- **In-Memory Processing**:
  - Uses `pypdf` to stream and slice documents page-by-page in-memory (`io.BytesIO`), maintaining a bounded RAM footprint even for large (100+ page) documents.
- **Intelligent Multi-Page Stitching**:
  - Recognizes continuous tables spanning consecutive pages, validates schema alignment, strips repeated header rows, and merges data smoothly.
- **Formatted Excel Export**:
  - Generates downloadable multi-sheet `.xlsx` files with styled headers, thin gridlines, and auto-adjusted column widths via `openpyxl`.

---

## Project Structure

```text
Tableextract/
├── app.py                  # Streamlit web interface, progress tracking, and file I/O
├── requirements.txt        # Python package dependencies
├── README.md               # Setup and usage documentation
├── .gitignore              # Git ignore configuration
└── src/
    ├── __init__.py         # Package initialization
    ├── table_extractor.py  # Page-by-page hybrid extraction engine (pdfplumber + img2table + OCR)
    ├── table_processor.py  # Cleaning, anti-hallucination filtering, and multi-page stitching
    ├── excel_exporter.py   # openpyxl / pandas multi-sheet Excel generator
    └── utils.py            # Memory buffers, safe math, and cell cleaning helpers
```

---

## System Prerequisites

1. **Python 3.10+**
2. **Tesseract OCR** (Required for scanned/image-based PDFs):
   - **macOS**: `brew install tesseract`
   - **Ubuntu / Debian**: `sudo apt-get install -y tesseract-ocr`
   - **Windows**: Install via [UB-Mannheim Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) and ensure it is in your system PATH.

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Tableextract
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

Launch the Streamlit application locally:

```bash
streamlit run app.py
```

The app will start and open automatically in your browser at:
`http://localhost:8501`

---

## How It Works

1. **Upload**: Select or drag-and-drop any PDF document into the file uploader.
2. **Process**: Click the **Extract Tables** button.
3. **Monitor**: Real-time progress bar tracks page-by-page extraction and stitching.
4. **Preview & Download**: Inspect interactive previews of each extracted table with dimensions and download the consolidated `_tables.xlsx` file.

---

