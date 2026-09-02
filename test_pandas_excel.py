import pandas as pd
import io

def export_to_excel_pandas(groups) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not groups:
            pd.DataFrame([["No bordered tables were detected in this document."]]).to_excel(
                writer, sheet_name="All_Tables", index=False, header=False
            )
        else:
            startrow = 0
            for g in groups:
                df = g["df"]
                n_rows, n_cols = df.shape
                idx = g["table_num"]
                
                # Title
                pd.DataFrame([[f"Table {idx} ({n_rows} rows x {n_cols} cols)"]]).to_excel(
                    writer, sheet_name="All_Tables", startrow=startrow, index=False, header=False
                )
                startrow += 1
                
                # Data
                df.to_excel(writer, sheet_name="All_Tables", startrow=startrow, index=False, header=False)
                
                # Format the header row (which is the first row of df)
                worksheet = writer.sheets['All_Tables']
                
                startrow += n_rows + 1 # +1 for blank row

            # Auto-fit columns roughly
            for ws in writer.sheets.values():
                for col in ws.columns:
                    max_length = 0
                    column = col[0].column_letter # Get the column name
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column].width = adjusted_width
                    
                    # Also wrap text and top align
                    for cell in col:
                        cell.alignment = cell.alignment.copy(wrapText=True, vertical='top')

    output.seek(0)
    return output.getvalue()

raw = [
    {"table_num": 1, "df": pd.DataFrame([["Header1", "Header2"], ["val1\nmultiline", "val2"], ["val3", None]])}
]
with open("test_out2.xlsx", "wb") as f:
    f.write(export_to_excel_pandas(raw))
print("Done")
