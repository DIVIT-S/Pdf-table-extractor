import pandas as pd
from exporter import export_to_excel

# Create mock raw tables
raw_tables = [
    {
        "page": 1,
        "table_on_page": 1,
        "df": pd.DataFrame([
            ["Name", "Age", "City"],
            ["Alice", "24", "New York"],
            ["Bob", "30", "London"]
        ])
    },
    {
        "page": 2,
        "table_on_page": 1,
        "df": pd.DataFrame([
            ["Name", "Age", "City"],
            ["Charlie", "28", "Paris"],
            ["David", "35", "Berlin"]
        ])
    },
    {
        "page": 2,
        "table_on_page": 2,
        "df": pd.DataFrame([
            ["Product", "Price"],
            ["Laptop", "1000"],
            ["Mouse", "50"]
        ])
    }
]

excel_bytes = export_to_excel(raw_tables)
with open("test_output.xlsx", "wb") as f:
    f.write(excel_bytes)
print("Excel generated.")
