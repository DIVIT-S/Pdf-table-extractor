# PDF Table Extractor

A Python-based Streamlit application for extracting tables from PDF files (both digital and scanned), consolidating them by schema, and exporting them to Excel.

## Features

- **PDF Table Extraction**: Extract bordered tables from digital and scanned PDFs
- **Digital PDF Support**: Extracts tables from text-based PDFs using `img2table`
- **Scanned PDF Support**: Uses OCR (Tesseract) for image-based PDFs
- **Schema Consolidation**: Automatically groups and merges tables with matching schemas
- **Excel Export**: Downloads all extracted tables in a single Excel file
- **Web Interface**: User-friendly Streamlit interface for easy uploads and downloads

## Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR (for scanned PDF support)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/DIVIT-S/Pdf-table-extractor.git
cd Pdf-table-extractor
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract (if needed for OCR):
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download installer from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

Then:
1. Upload a PDF file
2. Preview the extracted tables
3. Click "Download" to get all tables in Excel format

## Project Structure

```
├── app.py              # Streamlit application
├── extractor.py        # PDF table extraction logic
├── exporter.py         # Excel file generation & consolidation
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Key Components

### extractor.py
- `extract_tables_from_page()`: Main extraction function
- Detects digital vs scanned PDFs automatically
- Returns DataFrames for each extracted table

### exporter.py
- `consolidate_tables()`: Groups tables by schema
- `export_tables_to_excel()`: Generates formatted Excel file

### app.py
- Streamlit UI
- File upload handler
- Preview display
- Download button

## Troubleshooting

**Streamlit command not found?**

If you get `command not found: streamlit`, try one of these:

```bash
# Option 1: Use Python module
python -m streamlit run app.py

# Option 2: Use full path
/path/to/venv/bin/streamlit run app.py

# Option 3: Deactivate and reactivate venv
deactivate
source venv/bin/activate
streamlit run app.py
```

## Dependencies

- `streamlit` - Web interface
- `pypdf` - PDF reading
- `pdfplumber` - Text extraction
- `pypdfium2` - PDF rendering
- `img2table` - Table detection
- `pytesseract` - OCR for scanned PDFs
- `openpyxl` - Excel file creation
- `pandas` - Data manipulation

See `requirements.txt` for complete list with versions.

## Known Limitations

- Scanned PDF OCR quality depends on image resolution
- Tesseract must be installed separately for OCR functionality
- Very large PDFs (1000+ pages) may take time to process

## License

MIT License

## Contributing

Pull requests welcome! Please ensure tests pass before submitting.
