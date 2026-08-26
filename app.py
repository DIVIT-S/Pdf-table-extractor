import streamlit as st
from src.utils import get_pdf_page_count, slice_pdf_page
from src.table_extractor import TableExtractor
from src.table_processor import TableProcessor
from src.excel_exporter import export_tables_to_excel

# Configure page settings
st.set_page_config(
    page_title="PDF Table Extractor",
    page_icon="📄",
    layout="wide",
)

st.title("PDF Table Extractor")
st.write(
    "Upload any digital, scanned, or mixed PDF to automatically extract and reconstruct tables into a clean Excel spreadsheet."
)

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    pdf_bytes = uploaded_file.getvalue()
    
    try:
        total_pages = get_pdf_page_count(pdf_bytes)
        st.info(f"Loaded PDF: **{uploaded_file.name}** ({total_pages} page{'s' if total_pages != 1 else ''})")
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        total_pages = 0

    if total_pages > 0:
        if st.button("Extract Tables", type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            extractor = TableExtractor()
            raw_extracted_tables = []

            for page_idx in range(total_pages):
                current_page = page_idx + 1
                status_text.text(f"Processing page {current_page} of {total_pages}...")
                
                # In-memory page slicing to maintain bounded RAM usage
                page_buf = slice_pdf_page(pdf_bytes, page_idx)
                page_tables = extractor.extract_from_page(page_buf, page_number=current_page)
                
                if page_tables:
                    raw_extracted_tables.extend(page_tables)

                progress_bar.progress(current_page / total_pages)

            status_text.text("Cleaning and stitching tables...")
            final_tables = TableProcessor.process_and_stitch(raw_extracted_tables)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Store results in session state
            st.session_state["final_tables"] = final_tables
            st.session_state["total_pages_processed"] = total_pages
            st.session_state["processed_filename"] = uploaded_file.name

# Display results if available in session state
if "final_tables" in st.session_state:
    tables = st.session_state["final_tables"]
    total_pages = st.session_state["total_pages_processed"]
    orig_name = st.session_state.get("processed_filename", "document")
    base_name = orig_name.rsplit(".", 1)[0] if "." in orig_name else orig_name

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pages Processed", total_pages)
    with col2:
        st.metric("Total Tables Found", len(tables))

    if tables:
        excel_data = export_tables_to_excel(tables)
        
        st.download_button(
            label="📥 Download Excel (.xlsx)",
            data=excel_data,
            file_name=f"{base_name}_tables.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        st.subheader("Extracted Tables Preview")
        for i, df in enumerate(tables, start=1):
            with st.expander(f"Table {i} ({df.shape[0]} rows × {df.shape[1]} columns)", expanded=(i == 1)):
                st.dataframe(df)
    else:
        st.warning("No tables were detected in the uploaded PDF document.")
