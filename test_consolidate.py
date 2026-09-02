import pandas as pd
from exporter import consolidate_tables

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
    }
]

c1 = consolidate_tables(raw_tables)
c2 = consolidate_tables(raw_tables)

print("C1:")
print(c1[0]["df"])
print("C2:")
print(c2[0]["df"])
