import pandas as pd
from exporter import export_tables_to_excel
import openpyxl
import io

# Mock tables exactly like what they'd see
t1 = pd.DataFrame([
    ["Content Type", "Description", "Limitation"],
    ["Project-Based", "Directly teaches building\nprojects using LangGraph", "None"]
])
t2 = pd.DataFrame([
    ["Model", "Cost", "Latency"],
    ["GPT-4", "$0.03/1k", "High"],
    ["Claude 3", "$0.015/1k", "Medium"]
])

# Create the excel file
excel_bytes = export_tables_to_excel([t1, t2])
with open(".gemini/scratch/demo.xlsx", "wb") as f:
    f.write(excel_bytes)

# Read it back and format as markdown
wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
ws = wb["All_Tables"]

print("### Excel Output Preview (Sheet: All_Tables)\n")
for row in ws.iter_rows(values_only=True):
    # Format each row beautifully
    row_str = " | ".join(str(cell) if cell is not None else " " for cell in row)
    print(f"| {row_str} |")
