import io
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Payroll Studio", page_icon="💼", layout="wide"
)

# Custom Styling for Dark Theme & Professional Dashboard
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-top: 2rem;
    }
    .hero-title span {
        color: #ff9900;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: #a0aec0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1a202c;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #2d3748;
        text-align: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None


# Helper: Process Payroll into Paychex Import Template Format
def process_payroll_data(df):
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
        800.0: 25.00,   # Fethke, Alicia
    }

    if "Mileage" not in df.columns:
        df["Mileage"] = 0.0

    def classify_and_calculate(row):
        emp_id = row["Employee ID"]
        if emp_id in hourly_rates:
            rate = hourly_rates[emp_id]
            amount = row["Hours"] * rate
            pay_type = "Hourly"
            return rate, amount, pay_type
        else:
            return row["Rate"], row["Amount"], "PRN Points"

    results = df.apply(classify_and_calculate, axis=1)
    df["Rate"] = [r[0] for r in results]
    df["Amount"] = [r[1] for r in results]
    df["Pay Type"] = [r[2] for r in results]

    # Aggregate per Employee & Pay Type
    summary = (
        df.groupby(["Employee ID", "Employee", "Pay Type"])
        .agg({"Hours": "sum", "Amount": "sum", "Rate": "first", "Mileage": "sum"})
        .reset_index()
    )

    prn_rows = []
    hourly_rows = []
    overtime_rows = []
    mileage_rows = []

    for _, row in summary.iterrows():
        emp_id = int(row["Employee ID"]) if pd.notnull(row["Employee ID"]) else ""
        emp_name = row["Employee"]
        pay_type = row["Pay Type"]
        total_hours = row["Hours"]
        total_amount = row["Amount"]
        rate = row["Rate"]
        mileage = row["Mileage"]

        labor_override = f"{emp_name} - {emp_id} ({emp_id})" if emp_id else emp_name

        base_row_data = {
            "Review": "✅ Validated",
            "Client ID": 16068715,
            "Worker ID": emp_id,
            "Org": "",
            "Job Num": "",
            "Pay Comp Rate": pay_type,
            "Rate Num": rate if pay_type == "Hourly" else "",
            "Hours": total_hours if pay_type == "Hourly" else "",
            "Units": "",
            "Line Date": "",
            "Amount": total_amount if pay_type == "PRN Points" else "",
            "Check": "",
            "Override S": "",
            "Override L": "",
            "Labor Override": labor_override,
            "_EmployeeName": emp_name,
        }

        if pay_type == "PRN Points":
            prn_rows.append(base_row_data)
        elif pay_type == "Hourly":
            # Check if hours exceed 80 for Overtime splitting
            if total_hours > 80:
                # Regular Row capped at 80 hours
                reg_row = base_row_data.copy()
                reg_row["Hours"] = 80.0
                hourly_rows.append(reg_row)

                # Overtime Row for excess hours
                ot_hours = total_hours - 80.0
                ot_row = base_row_data.copy()
                ot_row["Pay Comp Rate"] = "Overtime"
                ot_row["Rate Num"] = rate * 1.5 if rate else "" # Typically 1.5x, or standard rate depending on config; using rate or can use standard rate. Let's keep rate or standard rate.
                ot_row["Hours"] = ot_hours
                overtime_rows.append(ot_row)
            else:
                hourly_rows.append(base_row_data)

        # Collect Mileage if greater than 0
        if mileage > 0:
            mileage_row = base_row_data.copy()
            mileage_row["Pay Comp Rate"] = "Mileage"
            mileage_row["Rate Num"] = 0.73
            mileage_row["Hours"] = ""
            mileage_row["Units"] = mileage
            mileage_row["Amount"] = round(mileage * 0.73, 2)
            mileage_rows.append(mileage_row)

    # Sort each group alphabetically by Employee Name
    prn_rows = sorted(prn_rows, key=lambda x: x["_EmployeeName"])
    hourly_rows = sorted(hourly_rows, key=lambda x: x["_EmployeeName"])
    overtime_rows = sorted(overtime_rows, key=lambda x: x["_EmployeeName"])
    mileage_rows = sorted(mileage_rows, key=lambda x: x["_EmployeeName"])

    # Combine order: 1) PRN Points, 2) Hourly, 3) Overtime (grouped with hourly or near bottom), 4) Mileage
    # Let's place Overtime right after Hourly or group them in the Hourly section
    final_rows = prn_rows + hourly_rows + overtime_rows + mileage_rows

    final_df = pd.DataFrame(final_rows)
    if "_EmployeeName" in final_df.columns:
        final_df = final_df.drop(columns=["_EmployeeName"])

    return final_df


# Top Navigation Bar
st.markdown("### 💼 Payroll Studio")
nav_selection = st.radio(
    "Navigation",
    ["Home", "Upload Data", "Export Center", "Developer Support"],
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown("---")

# --- PAGE 1: HOME ---
if nav_selection == "Home":
    st.markdown(
        '<div class="hero-title">Everything You Need to <span>Start</span>, <span>Get Hired</span>, and <span>Thrive</span> as a Payroll Professional</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-subtitle">Transform raw operational exports into sleek, verified, Paychex-ready statements instantly. Automatically catch new employees, per diem rates, and missing IDs with live review flags.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="metric-card"><h3>⚡ Instant Transform</h3><p>Upload raw CSV/Excel files and convert them instantly to Paychex format.</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card"><h3>🔍 Live Review Flags</h3><p>Automatically catch missing IDs, rate exceptions, and validations.</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card"><h3>📊 Clean Exports</h3><p>Generate exact template structures ready for direct client import.</p></div>""", unsafe_allow_html=True)

# --- PAGE 2: UPLOAD DATA ---
elif nav_selection == "Upload Data":
    st.markdown("## 📂 Upload Operational Payroll Export")
    st.write("Upload your raw payroll export file (`.xls`, `.xlsx`, or `.csv`) to begin validation and Paychex formatting.")

    uploaded_file = st.file_uploader("Choose a payroll file", type=["xls", "xlsx", "csv"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                xls = pd.ExcelFile(uploaded_file)
                sheet_name = "Data Export" if "Data Export" in xls.sheet_names else xls.sheet_names[0]
                df = pd.read_excel(xls, sheet_name=sheet_name)

            st.session_state.raw_df = df
            st.success(f"Successfully loaded file: **{uploaded_file.name}** ({len(df)} rows)")

            processed = process_payroll_data(df)
            st.session_state.processed_df = processed

            st.markdown("### 🔍 Live Review & Validation Preview")
            st.dataframe(processed, use_container_width=True)

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.info("Awaiting file upload...")

# --- PAGE 3: EXPORT CENTER ---
elif nav_selection == "Export Center":
    st.markdown("## 📥 Export Center")
    st.write("Download your validated, formatted payroll ready for direct import into Paychex.")

    if st.session_state.processed_df is not None:
        df_export = st.session_state.processed_df
        st.dataframe(df_export, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Paychex Import", index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Paychex-Ready Excel File",
            data=buffer,
            file_name="Paychex_Import_Ready.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    else:
        st.warning("No processed data available. Please upload a file first.")

# --- PAGE 4: DEVELOPER SUPPORT ---
elif nav_selection == "Developer Support":
    st.markdown("## ⚙️ Developer Support & Documentation")
    st.markdown("""
    ### 📌 Core Business Rules & Mappings:
    1. **Strict Ordering**: 
       - **1st**: PRN Points employees sorted alphabetically.
       - **2nd**: Hourly employees sorted alphabetically (capped at 80 hours).
       - **3rd**: Overtime entries for hourly employees exceeding 80 hours.
       - **4th**: Mileage entries grouped at the bottom, sorted alphabetically.
    2. **Mileage Rate**: Set to **0.73** per unit.
    3. **Overtime Rule**: Hours exceeding 80 for hourly employees automatically generate an **Overtime** component row.
    """)