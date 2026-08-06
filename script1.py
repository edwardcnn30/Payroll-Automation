import streamlit as st
import pandas as pd
import openpyxl
import re

# Page Configuration
st.set_page_config(page_title="Payroll & Email Automation Hub", layout="wide")

st.title("📊 Payroll & Email Automation Hub")

# Create two tabs for the dashboards
tab1, tab2 = st.tabs(["Payroll Automation Dashboard", "Multi-Excel Paychex Converter"])

# ==========================================
# TAB 1: PAYROLL AUTOMATION DASHBOARD
# ==========================================
with tab1:
    st.header("Payroll Automation Dashboard")
    st.write("Upload your payroll spreadsheets below to process and automate your workflows.")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], key="payroll_uploader")

    if uploaded_file is not None:
        df_payroll = pd.read_excel(uploaded_file)
        st.success("Payroll file uploaded successfully!")
        st.dataframe(df_payroll)

        st.download_button(
            label="Download Processed Payroll Report",
            data=uploaded_file,
            file_name="Processed_Payroll.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==========================================
# TAB 2: MULTI-EXCEL PAYCHEX CONVERTER
# ==========================================
with tab2:
    st.header("Multi-Excel Timesheet to Paychex Converter")
    st.write(
        "Upload **10 to 15 Excel timesheets at once** to aggregate and format them into the standard Paychex import-ready template.")

    # File uploader accepting multiple Excel files
    uploaded_excels = st.file_uploader(
        "Upload Excel Timesheets (Select multiple files)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="multi_excel_uploader"
    )

    if uploaded_excels:
        all_paychex_rows = []

        with st.spinner(f"Processing {len(uploaded_excels)} Excel files..."):
            for file in uploaded_excels:
                try:
                    df = pd.read_excel(file)
                    file_name_lower = file.name.lower()

                    # Loop through rows to extract record details
                    for index, row in df.iterrows():
                        row_text = " ".join([str(val) for val in row.values]).lower()
                        combined_text = file_name_lower + " " + row_text

                        # Determine Category & Pay Code based on file name or content
                        category = "Time Sheet"
                        pay_code = "REG"

                        if any(k in combined_text for k in ["mile", "travel", "mileage"]):
                            category = "Mileage"
                            pay_code = "MIL"
                        elif any(k in combined_text for k in ["case manager", "cm hours", "casemanager"]):
                            category = "Case Manager Hours"
                            pay_code = "CM_HRS"
                        elif any(k in combined_text for k in ["train", "course", "training"]):
                            category = "Training"
                            pay_code = "TRN"

                        # Extract employee name and numeric hours/units if available
                        emp_name = "Employee"
                        units_val = 0.00

                        string_vals = [str(val) for val in row.values if
                                       isinstance(val, str) and len(str(val).strip()) > 2]
                        numeric_vals = [val for val in row.values if isinstance(val, (int, float)) and val > 0]

                        if string_vals:
                            emp_name = string_vals[0]
                        if numeric_vals:
                            units_val = numeric_vals[0]

                        # Only add rows that have meaningful numbers/hours
                        if units_val > 0:
                            all_paychex_rows.append({
                                "Employee ID": "",
                                "Employee Name": emp_name,
                                "Pay Code": pay_code,
                                "Units/Hours": units_val,
                                "Category Description": category,
                                "Source File": file.name
                            })
                except Exception as ex:
                    st.warning(f"Could not parse file {file.name}: {ex}")

        if all_paychex_rows:
            df_paychex_master = pd.DataFrame(all_paychex_rows)
            st.success(
                f"Successfully aggregated {len(uploaded_excels)} files into {len(df_paychex_master)} Paychex import rows!")
            st.dataframe(df_paychex_master, use_container_width=True)

            # Consolidated download button
            csv_output = df_paychex_master.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Master Paychex Import CSV",
                data=csv_output,
                file_name="Master_Paychex_Import.csv",
                mime="text/csv"
            )
        else:
            st.info("Uploaded files were processed, but no valid hours or units were detected in the sheets.")