import pandas as pd


def process_payroll(input_file_path, output_file_path):
    """
    Processes the home health payroll export:
    1. Loads the 'Data Export' sheet from the Excel file.
    2. Applies hardcoded hourly rates based on Employee ID.
    3. Retains exceptions (like Escobar and Figueroa) under PRN Points.
    4. Recalculates total amounts for hourly staff (Hours * Rate).
    5. Adds a 'Pay Type' column and exports the final workbook.
    """
    try:
        # Load Excel file and Data Export sheet
        xls = pd.ExcelFile(input_file_path)
        df = pd.read_excel(xls, sheet_name='Data Export')
    except Exception as e:
        print(f"Error loading input file: {e}")
        return

    # Hardcoded hourly rates mapping based on Employee ID
    hourly_rates = {
        1351.0: 30.00,  # Cecil, Katherine
        1331.0: 40.00,  # Conner, Autumn
        1175.0: 28.00,  # Gene, Smith
        1279.0: 45.00,  # Johann, Jasmine
        1307.0: 25.00,  # Kogn, Alay
        1067.0: 46.00,  # Seiger, Rachel
        1162.0: 50.00,  # Simowski, Maggie
        1389.0: 40.00,  # Webb, Detrecia
        1358.0: 40.00,  # Wright, Sarah
        800.0: 25.00  # Fethke, Alicia
    }

    def classify_and_calculate(row):
        emp_id = row['Employee ID']
        # Note: Escobar (1388) and Figueroa (1457) are explicitly excluded from hourly and retained under PRN Points
        if emp_id in hourly_rates:
            rate = hourly_rates[emp_id]
            amount = row['Hours'] * rate
            pay_type = 'Hourly'
            return rate, amount, pay_type
        else:
            return row['Rate'], row['Amount'], 'PRN Points'

    # Apply tagging and rate calculations row-by-row
    results = df.apply(classify_and_calculate, axis=1)
    df['Rate'] = [r[0] for r in results]
    df['Amount'] = [r[1] for r in results]
    df['Pay Type'] = [r[2] for r in results]

    # Export clean processed results to a new Excel file
    df.to_excel(output_file_path, index=False)
    print(f"Processed payroll saved successfully to '{output_file_path}'")


if __name__ == "__main__":
    input_file = '8.15 HH Payroll.xls'
    output_file = 'Processed_HH_Payroll.xlsx'

    process_payroll(input_file, output_file)