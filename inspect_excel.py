import openpyxl

wb = openpyxl.load_workbook("test_output.xlsx")
ws = wb.active
print(f"Sheet Name: {ws.title}")
for row in ws.iter_rows(values_only=True):
    print(row)
