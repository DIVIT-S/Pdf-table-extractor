import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from src.utils import clean_cell_str, safe_division

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "the", "and", "that", "with", "for", "are", "is", "of",
    "in", "to", "from", "this", "have", "has", "an", "by", "as",
    "which", "should", "would", "their", "there", "they", "been",
    "other", "these", "such", "than", "will", "more", "also"
}

SHORT_CONNECTING_WORDS = {
    "to", "a", "in", "on", "the", "for", "it", "or", "and", "bit",
    "eat", "new", "what", "you", "how", "do", "just", "being",
    "polite", "else", "up", "at", "my", "me", "if"
}


def is_questionnaire_or_mcq(df: pd.DataFrame) -> bool:
    """Detect if matrix is multiple-choice questions or options (e.g. a), b), c), d), 1., 2.)."""
    total_rows = df.shape[0]
    if total_rows == 0:
        return False
    col0_vals = [str(df.iloc[r, 0]).strip() for r in range(total_rows)]
    mcq_markers = sum(1 for x in col0_vals if re.match(r"^(\(?[a-dA-D]\)|[a-dA-D][\.\)]|\d+[\.\)])$", x))
    if safe_division(mcq_markers, total_rows) >= 0.30:
        return True
    return False


def is_broken_sentence_table(df: pd.DataFrame) -> bool:
    """Detect if columns are just individual words of a wrapped sentence sliced apart."""
    single_word_cols = 0
    for r in range(df.shape[0]):
        row_vals = [str(df.iloc[r, c]).strip().lower() for c in range(df.shape[1]) if str(df.iloc[r, c]).strip()]
        if len(row_vals) >= 2:
            connectors = sum(
                1 for v in row_vals
                if v in SHORT_CONNECTING_WORDS or (len(v.split()) == 1 and len(v) <= 3 and not v.isdigit())
            )
            if connectors >= 2 or (len(row_vals) == 2 and any(v in SHORT_CONNECTING_WORDS for v in row_vals)):
                single_word_cols += 1
    if df.shape[0] > 0 and safe_division(single_word_cols, df.shape[0]) >= 0.30:
        return True
    return False


def is_toc_or_figure_list(df: pd.DataFrame) -> bool:
    """Check if table is a Table of Contents or List of Figures with dot leaders."""
    dot_leader_rows = 0
    total_rows = df.shape[0]
    for r in range(total_rows):
        row_text = " ".join(str(df.iloc[r, c]).strip() for c in range(df.shape[1]))
        if re.search(r"\.\s*\.\s*\.\s*\.", row_text) or re.search(r"\b(Figure|Table\s+ES|Chapter)\s+\d+", row_text, re.I):
            dot_leader_rows += 1
    if total_rows > 0 and safe_division(dot_leader_rows, total_rows) >= 0.25:
        return True
    return False


def is_numbered_list(df: pd.DataFrame) -> bool:
    """Check if a 2-column table is actually a numbered list (e.g. 1. text; 2. text)."""
    if df.shape[1] != 2:
        return False
    col0 = [str(x).strip() for x in df.iloc[:, 0]]
    list_num_count = sum(1 for x in col0 if re.match(r"^\d+[\.\)]?$", x))
    if safe_division(list_num_count, len(col0)) >= 0.50:
        return True
    return False


def is_footnote_or_citation(df: pd.DataFrame) -> bool:
    """Detect if a 2-column block is a footnote, reference, or citation list."""
    if df.shape[1] != 2:
        return False

    col0_vals = [str(x).strip() for x in df.iloc[:, 0]]
    col1_vals = [str(x).strip() for x in df.iloc[:, 1]]

    is_num_col0 = sum(1 for x in col0_vals if x.isdigit() or (len(x) <= 4 and x.endswith(".")))
    if is_num_col0 >= len(col0_vals) * 0.50:
        citations = sum(
            1 for x in col1_vals
            if any(k in x.lower() for k in ("http", "201", "200", "bank", "unep", "cpi", "bnef", "mnre", "al."))
        )
        if citations >= len(col1_vals) * 0.40:
            return True
    return False


def is_prose_or_section_block(df: pd.DataFrame) -> bool:
    """
    Detect if a 2-column or 3-column table is actually narrative article paragraphs,
    bullet lists, or section headings.
    """
    if df.shape[1] > 3:
        return False

    full_text = " ".join(str(df.iloc[r, c]).strip() for r in range(df.shape[0]) for c in range(df.shape[1]))
    if re.search(r"\b\d+\.\d+\.\s+[A-Z]", full_text):
        return True

    prose_rows = 0
    total_valid = 0

    for r in range(df.shape[0]):
        row_str = " ".join(str(df.iloc[r, c]).strip().lower() for c in range(df.shape[1]))
        words = re.findall(r"[a-z]+", row_str)
        if not words:
            continue
        total_valid += 1

        stop_cnt = sum(1 for w in words if w in STOP_WORDS)
        if len(words) > 6 and safe_division(stop_cnt, len(words)) > 0.18:
            prose_rows += 1

    if total_valid > 0 and safe_division(prose_rows, total_valid) >= 0.35:
        return True
    return False


def clean_dataframe(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Clean and validate a raw DataFrame extracted from a PDF table.
    
    - Normalizes cell strings and strips whitespace.
    - Drops empty rows and empty columns.
    - Eliminates MCQs, questionnaires, TOCs, numbered lists, footnotes, chart artifacts, and prose.
    - Returns None if the candidate is not an authentic data table.
    """
    if df is None or df.empty:
        return None

    # Clean all cells
    cleaned = df.copy()
    cleaned = cleaned.map(clean_cell_str)

    # Drop completely empty rows and columns
    temp = cleaned.replace("", float("nan")).dropna(how="all", axis=0).dropna(how="all", axis=1)

    if temp.empty or temp.shape[0] < 2 or temp.shape[1] < 2:
        return None

    cleaned = cleaned.iloc[temp.index, temp.columns].reset_index(drop=True)

    # 1. Reject Multiple Choice Questionnaires / Option Lists
    if is_questionnaire_or_mcq(cleaned):
        return None

    # 2. Reject Broken Sentence Column Fragments
    if is_broken_sentence_table(cleaned):
        return None

    # 3. Reject Table of Contents & Figure listings
    if is_toc_or_figure_list(cleaned):
        return None

    # 4. Reject Numbered Lists
    if is_numbered_list(cleaned):
        return None

    # 5. Reject Footnotes & References
    if is_footnote_or_citation(cleaned):
        return None

    # 6. Reject Prose & Multi-column Text Paragraphs
    if is_prose_or_section_block(cleaned):
        return None

    # 7. Reject Chart Over-segmented Grids & Low-density Matrix Artifacts
    total_cells = cleaned.shape[0] * cleaned.shape[1]
    non_blank = sum(1 for c in cleaned.columns for v in cleaned[c] if str(v).strip())
    density = safe_division(non_blank, total_cells)

    if cleaned.shape[1] > 8 and density < 0.40:
        return None

    if density < 0.30 and cleaned.shape[0] < 8:
        return None

    if non_blank < 4:
        return None

    cleaned.columns = range(cleaned.shape[1])
    return cleaned


def extract_header_signature(df: pd.DataFrame) -> List[str]:
    """Extract normalized signature from the first row of a DataFrame."""
    if df.empty or df.shape[0] == 0:
        return []
    first_row = df.iloc[0].tolist()
    return [str(c).strip().lower() for c in first_row]


def calculate_header_similarity(header_a: List[str], header_b: List[str]) -> float:
    """Calculate normalized similarity ratio between two header row signatures."""
    if not header_a or not header_b:
        return 0.0
    if len(header_a) != len(header_b):
        return 0.0

    matches = 0
    non_empty_pairs = 0

    for a, b in zip(header_a, header_b):
        if a or b:
            non_empty_pairs += 1
            if a == b:
                matches += 1

    if non_empty_pairs == 0:
        return 0.0

    return safe_division(matches, non_empty_pairs, default=0.0)


def check_table_continuation(
    prev_table: Dict[str, Any], curr_table: Dict[str, Any]
) -> Tuple[bool, bool]:
    """
    Determine if curr_table is a continuation of prev_table across consecutive pages.
    """
    prev_page = prev_table.get("page", 0)
    curr_page = curr_table.get("page", 0)
    prev_df: pd.DataFrame = prev_table.get("df")
    curr_df: pd.DataFrame = curr_table.get("df")

    if curr_page != prev_page + 1:
        return False, False

    if prev_df.shape[1] != curr_df.shape[1]:
        return False, False

    prev_header = extract_header_signature(prev_df)
    curr_header = extract_header_signature(curr_df)

    similarity = calculate_header_similarity(prev_header, curr_header)

    if similarity >= 0.70:
        return True, True

    return False, False


def promote_header_if_suitable(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Promote first row to columns if it represents valid headers;
    otherwise assign clean Col_1, Col_2 column names.
    Filter out any candidate that fails quality checks after header promotion.
    """
    if df is None or df.empty or df.shape[1] < 2:
        return None

    first_row = df.iloc[0].tolist()
    non_empty_first_row = sum(1 for c in first_row if str(c).strip())

    if non_empty_first_row >= safe_division(len(first_row), 2, 1.0) and df.shape[0] > 1:
        headers = [str(c).strip() if str(c).strip() else f"Col_{i+1}" for i, c in enumerate(first_row)]
        
        seen: Dict[str, int] = {}
        unique_headers: List[str] = []
        for h in headers:
            if h not in seen:
                seen[h] = 1
                unique_headers.append(h)
            else:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")

        candidate_df = df.iloc[1:].copy()
        candidate_df.columns = unique_headers
        candidate_df = candidate_df.reset_index(drop=True)
    else:
        candidate_df = df.copy()
        candidate_df.columns = [f"Col_{i+1}" for i in range(df.shape[1])]
        candidate_df = candidate_df.reset_index(drop=True)

    # Re-verify candidate after header promotion
    if is_questionnaire_or_mcq(candidate_df):
        return None
    if is_broken_sentence_table(candidate_df):
        return None

    # Require at least 2 valid data rows with at least 2 non-empty cells each
    valid_rows: List[int] = []
    for r in range(candidate_df.shape[0]):
        row_vals = [str(candidate_df.iloc[r, c]).strip() for c in range(candidate_df.shape[1])]
        non_empty = sum(1 for v in row_vals if v and v.lower() not in ("nan", "none", ""))
        if non_empty >= 2:
            valid_rows.append(r)

    if len(valid_rows) < 2:
        return None

    final_df = candidate_df.iloc[valid_rows].reset_index(drop=True)

    # Drop columns that became entirely blank in data rows
    final_df = final_df.replace("", float("nan")).dropna(how="all", axis=1)
    if final_df.empty or final_df.shape[1] < 2:
        return None

    total_data_cells = final_df.shape[0] * final_df.shape[1]
    total_non_blank = sum(1 for c in final_df.columns for v in final_df[c] if str(v).strip())

    if total_non_blank < 4:
        return None

    if safe_division(total_non_blank, total_data_cells) < 0.35 and final_df.shape[0] < 6:
        return None

    final_df = final_df.fillna("")
    return final_df


class TableProcessor:
    """Processes, cleans, deduplicates, and stitches extracted tables."""

    @staticmethod
    def process_and_stitch(raw_page_tables: List[Dict[str, Any]]) -> List[pd.DataFrame]:
        """
        Takes raw page-by-page table extractions, validates them,
        intelligently stitches multi-page tables, and returns clean DataFrames.
        """
        # Step 1: Clean and validate individual tables
        cleaned_entries: List[Dict[str, Any]] = []
        for entry in raw_page_tables:
            cleaned_df = clean_dataframe(entry.get("df"))
            if cleaned_df is not None:
                cleaned_entries.append({
                    "df": cleaned_df,
                    "page": entry.get("page", 1),
                    "bbox": entry.get("bbox"),
                    "title": entry.get("title"),
                })

        if not cleaned_entries:
            return []

        # Step 2: Deduplicate identical extractions on the same page
        unique_entries: List[Dict[str, Any]] = []
        for entry in cleaned_entries:
            is_dup = False
            for existing in unique_entries:
                if existing["page"] == entry["page"] and existing["df"].equals(entry["df"]):
                    is_dup = True
                    break
            if not is_dup:
                unique_entries.append(entry)

        # Step 3: Multi-page table stitching
        stitched_tables: List[Dict[str, Any]] = []
        for entry in unique_entries:
            if not stitched_tables:
                stitched_tables.append(entry)
                continue

            last_table = stitched_tables[-1]
            is_cont, has_repeated_hdr = check_table_continuation(last_table, entry)

            if is_cont:
                curr_df = entry["df"]
                if has_repeated_hdr and curr_df.shape[0] > 1:
                    append_df = curr_df.iloc[1:].copy()
                else:
                    append_df = curr_df.copy()

                append_df.columns = last_table["df"].columns
                merged_df = pd.concat([last_table["df"], append_df], ignore_index=True)
                last_table["df"] = merged_df
                last_table["page"] = entry["page"]
            else:
                stitched_tables.append(entry)

        # Step 4: Finalize DataFrames (promote headers, drop empty data rows, reset indices)
        final_dfs: List[pd.DataFrame] = []
        for item in stitched_tables:
            final_df = promote_header_if_suitable(item["df"])
            if final_df is not None and not final_df.empty:
                final_dfs.append(final_df)

        return final_dfs
