# PDF Table Extractor

> **Extract tables from any PDF** (digital or scanned) with AI-powered OCR, consolidate by schema, and export to a single Excel file with a single click.

A Python-based Streamlit web application that intelligently extracts bordered tables from PDF documents using advanced computer vision and OCR techniques, automatically groups tables with matching schemas, and exports everything to a professionally formatted Excel workbook.

---

## 🎯 Quick Start

Get the app running in 2 minutes:

```bash
# 1. Clone and navigate
git clone https://github.com/DIVIT-S/Pdf-table-extractor.git
cd Pdf-table-extractor

# 2. Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python -m streamlit run app.py
```

**That's it!** The app will open at `http://localhost:8501`

---

## 📋 Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **Memory**: 2GB minimum (4GB recommended for large PDFs)
- **Disk Space**: 500MB for dependencies

### Required External Software

#### Tesseract OCR (for scanned PDFs)

**macOS** (using Homebrew):
```bash
brew install tesseract
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows**:
1. Download installer from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR`)
3. The app will auto-detect the installation

**Verify installation**:
```bash
tesseract --version
```

---

## 🔧 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/DIVIT-S/Pdf-table-extractor.git
cd Pdf-table-extractor
```

### Step 2: Create Virtual Environment

Creating a virtual environment isolates project dependencies from your system Python:

```bash
python -m venv venv
```

Activate it:

**macOS/Linux**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **streamlit** - Web interface framework
- **pypdf** - PDF reading and manipulation
- **pdfplumber** - Digital PDF text extraction
- **pypdfium2** - PDF rendering to images
- **img2table** - Table detection from images
- **pytesseract** - OCR wrapper for Tesseract
- **openpyxl** - Excel file creation
- **pandas** - Data manipulation

### Step 4: Verify Installation

```bash
python -c "import streamlit, pypdf, img2table, pandas, openpyxl; print('✅ All dependencies installed!')"
```

---

## 🚀 Usage Guide

### Starting the Application

```bash
python -m streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

### Using the App (Step-by-Step)

#### **1. Upload a PDF**
- Click the file uploader in the sidebar
- Select any PDF file (digital or scanned)
- The app automatically detects the PDF type

#### **2. View Extraction Progress**
- The app shows:
  - Total pages processed
  - Number of tables found
  - Consolidation status
  - Summary metrics

#### **3. Preview Tables**
- Each extracted table appears as an interactive preview
- Shows table dimensions (rows × columns)
- Pages where the table was found
- Sample data

#### **4. Download Results**
- Click the **"📥 Download Excel"** button
- Gets all tables in a single Excel file
- Named as `extracted_tables_{timestamp}.xlsx`
- Opens in Excel or any spreadsheet application

### Example Usage

```python
# From Python (if using the library directly)
from extractor import extract_tables_from_page
from exporter import consolidate_tables, export_tables_to_excel
import pandas as pd

# Extract tables from a PDF page
tables = extract_tables_from_page(pdf_page_bytes, page_number=1)

# Consolidate tables with matching schemas
consolidated = consolidate_tables(tables)

# Export to Excel
excel_file = export_tables_to_excel([t["df"] for t in consolidated])

# Save to disk
with open("output.xlsx", "wb") as f:
    f.write(excel_file)
```

---

## 📁 Project Structure

```
Pdf-table-extractor/
├── app.py                    # Main Streamlit application (entry point)
├── extractor.py              # PDF table extraction engine
├── exporter.py               # Excel export & consolidation
├── requirements.txt          # Python dependencies with versions
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

### File Descriptions

#### **app.py** (Main Application - 11 KB)
The Streamlit web interface that orchestrates the entire workflow.

**Key Functions**:
- File upload handler
- Extraction pipeline management
- Table preview rendering
- Download button implementation

**Workflow**:
1. User uploads PDF → reads file bytes
2. Creates PdfReader object
3. Loops through each page:
   - Extracts single page as bytes
   - Calls `extract_tables_from_page()` from extractor.py
4. Consolidates all tables via `consolidate_tables()` from exporter.py
5. Generates Excel via `export_tables_to_excel()` from exporter.py
6. Renders download button with Excel bytes

**Key Code**:
```python
# Streamlit file upload
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# Process each page
reader = PdfReader(uploaded_pdf)
for page_idx in range(len(reader.pages)):
    page_bytes = extract_page_as_bytes(reader, page_idx)
    tables = extract_tables_from_page(page_bytes, page_idx + 1)
    all_tables.extend(tables)

# Download button
excel_bytes = export_tables_to_excel([t["df"] for t in consolidated])
st.download_button(
    label="📥 Download Excel",
    data=excel_bytes,
    file_name="extracted_tables.xlsx"
)
```

---

#### **extractor.py** (Extraction Engine - 5.3 KB)

The core engine that detects and extracts tables from PDF pages. Handles both digital and scanned PDFs intelligently.

**Key Functions**:

##### `extract_tables_from_page(page_bytes: bytes, page_number: int) -> List[Dict]`
**Purpose**: Main entry point. Extracts all tables from a single PDF page.

**Input**:
- `page_bytes`: Raw bytes of a PDF page
- `page_number`: Page number (for tracking)

**Output**: List of dictionaries:
```python
[
    {
        "df": DataFrame,      # Table data
        "page": int          # Source page number
    },
    ...
]
```

**Logic**:
1. Detects if page is digital or scanned
2. Routes to appropriate extraction method
3. Cleans and validates extracted tables
4. Returns list of valid DataFrames

**Example**:
```python
tables = extract_tables_from_page(page_bytes, page_number=1)
# Returns: [{"df": pd.DataFrame(...), "page": 1}, ...]
```

---

##### `_is_digital_pdf(page_bytes: bytes) -> bool`
**Purpose**: Detects if a PDF page contains extractable text (digital) or is scanned.

**Detection Method**:
- Uses pdfplumber to extract text
- Counts non-whitespace characters
- If > 20 chars found → Digital PDF
- Otherwise → Scanned PDF (needs OCR)

**Example**:
```python
if _is_digital_pdf(page_bytes):
    # Use img2table with implicit_rows=False (precise table detection)
else:
    # Use img2table with implicit_rows=True (OCR-friendly mode)
```

---

##### `_clean_df(df: pd.DataFrame) -> Optional[pd.DataFrame]`
**Purpose**: Removes empty rows/columns and validates table quality.

**Processing Steps**:
1. **Strip whitespace**: Removes leading/trailing spaces from all cells
2. **Remove empty rows**: Drops rows where all values are empty strings
3. **Remove empty columns**: Drops columns where all values are empty strings
4. **Validate minimum size**: Ensures table is at least 2×2
5. **Validate row count**: Ensures at least 2 rows (including header)

**Code**:
```python
# Strip whitespace from all cells
df = df.map(lambda x: str(x).strip() if isinstance(x, (str, int, float)) else x)

# Remove empty rows/cols
df = df[(df != '').any(axis=1)]  # Remove rows
df = df.loc[:, (df != '').any(axis=0)]  # Remove columns

# Validate
if df.shape[0] < 2 or df.shape[1] < 2:
    return None  # Too small
return df.reset_index(drop=True)
```

**Returns**: Cleaned DataFrame or None if invalid

---

##### `_pdf_to_png(page_bytes: bytes) -> bytes`
**Purpose**: Converts a PDF page to a high-resolution PNG image for table detection.

**Resolution**: 4x scale (384 DPI equivalent) for clear OCR

**Process**:
1. Creates PdfDocument from bytes
2. Renders page 0 at scale=4
3. Converts PIL image to PNG
4. Returns PNG bytes

**Why needed**: img2table works on images, not PDF text

---

#### **exporter.py** (Export & Consolidation - 5.9 KB)

Handles consolidating tables with matching schemas and generating formatted Excel files.

**Key Functions**:

##### `consolidate_tables(tables: List[Dict]) -> List[Dict]`
**Purpose**: Groups tables with identical schemas (same headers and column count) and merges their data rows.

**Logic**:
1. Extracts header from first row of each table: `tuple(df.iloc[0])`
2. Groups by header + column count combination
3. Concatenates DataFrames within each group
4. Assigns unique table numbers

**Input**: List of raw table dictionaries
```python
[
    {"df": DataFrame, "page": 1},
    {"df": DataFrame, "page": 2},
    ...
]
```

**Output**: Consolidated groups
```python
[
    {
        "table_num": 1,
        "hdr": ("Col1", "Col2", "Col3"),
        "cols": 3,
        "df": DataFrame,              # Merged data
        "pages": [1, 2, 5]            # Where it was found
    },
    ...
]
```

**Example**:
```python
# Two tables with same schema get merged
raw_tables = [
    {"df": pd.DataFrame([["Name", "Age"], ["Alice", "25"]]), "page": 1},
    {"df": pd.DataFrame([["Name", "Age"], ["Bob", "30"]]), "page": 2},
]
consolidated = consolidate_tables(raw_tables)
# Result: 1 table with 2 data rows (Alice and Bob merged)
```

---

##### `export_tables_to_excel(tables: List[pd.DataFrame]) -> bytes`
**Purpose**: Generates a professionally formatted Excel file with all tables.

**Format**:
- **Single sheet**: "All_Tables"
- **Per table**:
  - Title row: `"Table X (N rows × M cols)"`
  - Header row: Styled with background color and border
  - Data rows: Centered alignment, borders
  - Blank row: Separator between tables
  - Auto-fit columns to content

**Processing**:
1. Sanitizes cell values (removes XML-invalid characters)
2. Creates workbook and worksheet
3. Writes each table with formatting
4. Auto-fits column widths
5. Returns bytes

**Code**:
```python
def sanitize_cell_value(val):
    """Remove special chars that break Excel XML"""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    val_str = ''.join(c for c in val_str if ord(c) >= 32 or c in '\t\n\r')
    val_str = val_str.replace('\ufffe', '')  # Remove BOM
    return val_str

# Then write to Excel with openpyxl
wb = Workbook()
ws = wb.active
ws.title = "All_Tables"
# ... add rows with formatting ...
return wb.save(BytesIO()).getvalue()
```

**Returns**: Bytes of complete Excel file (can be saved or downloaded)

---

#### **requirements.txt** (Dependencies - 166 bytes)

Lists all Python packages with pinned versions for reproducibility.

**Key Dependencies**:

```
streamlit==1.40.2              # Web interface
pypdf==4.0.1                   # PDF reading/writing
pdfplumber==0.11.0             # Digital PDF text extraction
pypdfium2==4.30.0              # PDF rendering to images
img2table==2.0.5               # Table detection from images
pytesseract==0.3.10            # OCR (Tesseract wrapper)
openpyxl==3.1.2                # Excel file creation
pandas==2.2.0                  # Data manipulation
Pillow==10.2.0                 # Image processing
```

---

## 🔄 How It Works (Architecture)

### Overall Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER UPLOADS PDF                          │
│                    (via Streamlit UI)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           EXTRACT PAGES FROM PDF                             │
│      (pypdf splits into individual pages)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  FOR EACH PAGE:            │
        │                            │
        │  1. Convert to PNG         │
        │     (pypdfium2, 384 DPI)   │
        │                            │
        │  2. Detect PDF type        │
        │     (pdfplumber for text)  │
        │                            │
        └────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        │                          │
        ▼ DIGITAL                  ▼ SCANNED
    ┌─────────────────┐        ┌─────────────────┐
    │ img2table:      │        │ img2table:      │
    │ implicit_rows   │        │ implicit_rows   │
    │ =False          │        │ =True + OCR     │
    │ (precise)       │        │ (flexible)      │
    └────────┬────────┘        └────────┬────────┘
             │                         │
             │    Table Data Found     │
             └────────┬────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         CLEAN & VALIDATE TABLES                              │
│    (_clean_df: remove empty rows/cols, validate size)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│      CONSOLIDATE TABLES BY SCHEMA                            │
│ (Group tables with identical headers & column count)        │
│  Result: [Consolidated Table 1, Table 2, ...]              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│       GENERATE EXCEL FILE                                    │
│   (Format tables, add headers, auto-fit columns)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│        DOWNLOAD AS EXCEL                                     │
│    (Single .xlsx file with all tables)                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Example

```
INPUT PDF:
Page 1: Table(Name, Age, City) with 3 rows
Page 2: Table(Name, Age, City) with 2 rows
Page 3: Table(Product, Price) with 4 rows

         ↓ (EXTRACTION)

RAW TABLES:
[
  {"df": name_age_city_table, "page": 1},
  {"df": name_age_city_table, "page": 2},
  {"df": product_price_table, "page": 3}
]

         ↓ (CONSOLIDATION)

CONSOLIDATED:
[
  {
    "table_num": 1,
    "df": name_age_city_merged (5 rows),
    "pages": [1, 2]
  },
  {
    "table_num": 2,
    "df": product_price_table (4 rows),
    "pages": [3]
  }
]

         ↓ (EXPORT)

EXCEL FILE: extracted_tables.xlsx
  Sheet: "All_Tables"
    Table 1: (5 rows × 3 cols)
    Table 2: (4 rows × 2 cols)
```

---

## 🎨 Output Format

### Excel File Structure

**Single Sheet**: `All_Tables`

**Per Table**:
```
┌─────────────────────────────────────────┐
│  Table 1 (5 rows × 3 cols)              │  ← Title row
├─────────────────────────────────────────┤
│  Name          │ Age       │ City       │  ← Header row (styled)
├─────────────────────────────────────────┤
│  Alice         │ 25        │ New York   │
│  Bob           │ 30        │ London     │
│  Charlie       │ 28        │ Paris      │
│  David         │ 35        │ Berlin     │
│  Eve           │ 22        │ Tokyo      │
├─────────────────────────────────────────┤
│                                         │  ← Blank separator row
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Table 2 (3 rows × 2 cols)              │
├─────────────────────────────────────────┤
│  Product       │ Price                  │
├─────────────────────────────────────────┤
│  Laptop        │ $1200                  │
│  Mouse         │ $25                    │
│  Keyboard      │ $75                    │
└─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### "Command not found: streamlit"

The venv PATH may not be configured. Use Python module directly:

```bash
python -m streamlit run app.py
```

Or use full path:
```bash
/path/to/venv/bin/streamlit run app.py
```

### "No tables extracted from PDF"

**Possible causes**:
1. **No bordered tables**: App only detects bordered tables (not free-form layouts)
2. **Scanned PDF without Tesseract**: Install Tesseract (see Prerequisites)
3. **Complex table design**: App works best with simple grid tables

**Debug**:
```bash
python -c "from extractor import _is_digital_pdf; print(_is_digital_pdf(pdf_bytes))"
```

### "Tesseract not found" (for scanned PDFs)

**macOS**:
```bash
brew install tesseract
```

**Ubuntu**:
```bash
sudo apt-get install tesseract-ocr
```

**Windows**: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

Then verify:
```bash
tesseract --version
```

### "Excel file is corrupted"

**Cause**: Invalid XML characters in table data

**Solution**: Already fixed! The app sanitizes all cell values.

If you get this error:
1. Update the repo: `git pull origin main`
2. Reinstall: `pip install -r requirements.txt --upgrade`
3. Try again

### "Out of memory" on large PDFs

**Solutions**:
1. Process PDFs in chunks (split large files)
2. Increase available RAM
3. Use a machine with 4GB+ RAM

---

## ⚡ Performance Tips

### For Better Performance:

1. **Digital PDFs only** → Extract faster than scanned PDFs
2. **Smaller PDFs** → Process faster (< 100 pages ideal)
3. **High-quality scans** → Better OCR results
4. **Regular tables** → Easier detection than irregular layouts

### Typical Processing Times:

- 10-page digital PDF: ~5-10 seconds
- 10-page scanned PDF: ~30-60 seconds (OCR intensive)
- 100-page PDF: ~1-2 minutes

---

## 📦 Dependencies Explained

| Package | Purpose | Why Needed |
|---------|---------|-----------|
| **streamlit** | Web interface | UI for uploading & downloading |
| **pypdf** | PDF reading | Extract pages from PDF |
| **pdfplumber** | Text extraction | Detect digital vs scanned |
| **pypdfium2** | PDF rendering | Convert pages to images |
| **img2table** | Table detection | Find tables in images |
| **pytesseract** | OCR wrapper | Read text from scanned images |
| **openpyxl** | Excel creation | Generate Excel files |
| **pandas** | Data processing | Handle table data |
| **Pillow** | Image processing | Image conversions |

---

## 🤝 Contributing

Pull requests are welcome!

**Before submitting**:
1. Test your changes locally
2. Ensure code follows project structure
3. Update README if adding features
4. Test with multiple PDF types

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support

Found a bug? Have a suggestion?

1. Check existing [GitHub Issues](https://github.com/DIVIT-S/Pdf-table-extractor/issues)
2. Create new issue with:
   - PDF sample (if possible)
   - Error message
   - Your OS and Python version

---

## 🎓 What You're Getting

✅ **Intelligent PDF Table Extraction**
- Automatic digital vs scanned detection
- OCR for handwritten/scanned tables
- Precise bordered table detection

✅ **Schema-Based Consolidation**
- Groups identical tables across pages
- Merges data automatically
- Tracks source pages

✅ **Professional Excel Export**
- Formatted output
- Auto-fitted columns
- Single downloadable file

✅ **Simple Web Interface**
- No coding required
- Real-time preview
- One-click download

---

## 🚀 Next Steps

1. **Clone & Setup**: Follow Quick Start section
2. **Run the App**: `python -m streamlit run app.py`
3. **Upload a PDF**: Use the file uploader
4. **Download Results**: Click the download button
5. **Open in Excel**: View your extracted tables

**Happy extracting!** 🎉
