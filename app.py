"""
app.py — PDF Table Extractor (Lite)
Streamlit UI + orchestration loop with multi-page table consolidation.
"""
import base64
import io
import logging
import re
import streamlit as st
from pypdf import PdfReader, PdfWriter
from extractor import extract_tables_from_page
from exporter import consolidate_tables, export_tables_to_excel

logging.basicConfig(level=logging.WARNING)

st.set_page_config(
    page_title="PDF Table Extractor",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Styling (Modern / Glassmorphic) ───────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .main-header {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.12) 100%);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.4);
        margin-bottom: 8px;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .download-card {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
        <span class="badge">Consolidated Extraction Engine</span>
        <h1 style="margin: 4px 0 8px 0; font-size: 2.2rem;">📑 PDF Table Extractor</h1>
        <p style="margin: 0; color: #94a3b8; font-size: 1rem; line-height: 1.5;">
            Extracts <strong>bordered tables</strong> across digital and scanned PDF pages.
            Tables with identical schemas across pages are <strong>automatically combined into unified tables</strong> in one single Excel sheet.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar Configuration & Info ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Engine Specs")
    st.markdown(
        """
        - **Detection Strategy:** Strictly bordered lattice grids
        - **Digital Pipeline:** Native vector text via `img2table`
        - **Scanned Pipeline:** `pypdfium2` + Tesseract OCR
        - **Consolidation:** Matching schema (headers & column count) merged into unified `Table 1`, `Table 2`...
        - **Output Structure:** Single `.xlsx` file (`All_Tables` worksheet)
        """
    )
    st.divider()
    st.markdown("### 🛡️ Schema-Based Merging")
    st.markdown(
        """
        - Tables with identical column headings and column count across pages are combined.
        - Tables with differing schemas are created as distinct sequential tables (`Table 1`, `Table 2`...).
        - All output is structured into **one single Excel worksheet**.
        """
    )

# ── File Upload Section ───────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Choose a PDF file to extract tables from",
    type=["pdf"],
    help="Accepts digital, scanned, or mixed PDF files.",
)

if uploaded is None:
    st.session_state.pop("raw_tables", None)
    st.session_state.pop("consolidated_tables", None)
    st.session_state.pop("excel_bytes", None)
    st.session_state.pop("current_file", None)
    st.info("👆 Upload a PDF file above to begin extraction.")
    st.stop()

# Reset state if a new file is uploaded
if st.session_state.get("current_file") != uploaded.name:
    st.session_state["current_file"] = uploaded.name
    st.session_state.pop("raw_tables", None)
    st.session_state.pop("consolidated_tables", None)
    st.session_state.pop("excel_bytes", None)

pdf_bytes = uploaded.getvalue()

try:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
except Exception as exc:
    st.error(f"❌ Error loading PDF: {exc}")
    st.stop()

col_info1, col_info2 = st.columns([3, 1])
with col_info1:
    st.markdown(f"**Document:** `{uploaded.name}` ({len(pdf_bytes) / 1024:.1f} KB)")
with col_info2:
    st.markdown(f"**Pages Detected:** `{total_pages}`")

# ── Extraction Action ─────────────────────────────────────────────────────────
if st.button("🚀 Extract & Consolidate Tables", type="primary", use_container_width=True):
    raw_tables = []
    progress_bar = st.progress(0.0, text="Initializing extraction engine…")
    status_box = st.empty()

    for page_idx in range(total_pages):
        page_num = page_idx + 1
        status_box.info(f"⏳ Processing Page {page_num} of {total_pages}…")

        writer = PdfWriter()
        writer.add_page(reader.pages[page_idx])
        page_buf = io.BytesIO()
        writer.write(page_buf)
        page_bytes_slice = page_buf.getvalue()

        tables_on_page = extract_tables_from_page(page_bytes_slice, page_number=page_num)
        raw_tables.extend(tables_on_page)

        progress_bar.progress(page_num / total_pages, text=f"Processed Page {page_num}/{total_pages}")

    progress_bar.empty()
    status_box.empty()

    # Consolidate tables and pre-generate Excel bytes immediately
    consolidated = consolidate_tables(raw_tables)
    dfs_to_export = [g["df"] for g in consolidated]
    excel_bytes = export_tables_to_excel(dfs_to_export)

    st.session_state["raw_tables"] = raw_tables
    st.session_state["consolidated_tables"] = consolidated
    st.session_state["filename"] = uploaded.name
    st.session_state["total_pages"] = total_pages

# ── Results Presentation ──────────────────────────────────────────────────────
if "consolidated_tables" in st.session_state:
    consolidated = st.session_state["consolidated_tables"]
    filename = st.session_state.get("filename", "document.pdf")
    base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
    safe_name = re.sub(r"[^\w\-_\.]", "_", base_name)
    download_filename = f"{safe_name}_tables.xlsx"
    total_p = st.session_state.get("total_pages", 1)

    # Generate fresh excel_bytes every time to ensure latest export logic is applied
    dfs_to_export = [g["df"] for g in consolidated] if consolidated else []
    excel_bytes = export_tables_to_excel(dfs_to_export)

    st.divider()

    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{total_p}</div>'
            f'<div class="metric-label">Pages Processed</div></div>',
            unsafe_allow_html=True,
        )
    with mcol2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(consolidated)}</div>'
            f'<div class="metric-label">Consolidated Tables</div></div>',
            unsafe_allow_html=True,
        )
    with mcol3:
        total_cells = sum(t["df"].shape[0] * t["df"].shape[1] for t in consolidated)
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{total_cells}</div>'
            f'<div class="metric-label">Total Data Cells</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    if not consolidated:
        st.warning("⚠️ No bordered tables were detected in this document.")
    else:
        st.success(f"✅ Extracted and compiled **{len(consolidated)} consolidated table{'s' if len(consolidated) != 1 else ''}** into one Excel sheet.")

    # Primary download button
    st.download_button(
        label="📥 Download Consolidated Excel (.xlsx)",
        data=excel_bytes,
        file_name=download_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
        key="download_excel_btn",
    )

    # Base64 Direct Download Fallback Link
    b64_data = base64.b64encode(excel_bytes).decode()
    st.markdown(
        f"""
        <div class="download-card">
            <span style="color: #94a3b8; font-size: 0.9rem;">Having trouble with the button? </span>
            <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}"
               download="{download_filename}"
               style="color: #818cf8; font-weight: 600; text-decoration: underline;">
               Click here for Direct Browser Download ({download_filename})
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if consolidated:
        st.markdown("### 🔍 Consolidated Tables Preview")
        for entry in consolidated:
            pages_str = ", ".join(str(p) for p in entry["pages"])
            label = (
                f"📊 Table {entry['table_num']} — {entry['df'].shape[0]} rows × {entry['df'].shape[1]} cols "
                f"(Source: Page{'s' if len(entry['pages']) > 1 else ''} {pages_str})"
            )
            with st.expander(label, expanded=True):
                st.dataframe(entry["df"], use_container_width=True, hide_index=True)
