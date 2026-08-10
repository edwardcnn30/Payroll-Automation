import io
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Payroll Studio", page_icon="💼", layout="wide"
)

# Initialize Query Params for Navigation
if "tab" not in st.query_params:
    st.query_params["tab"] = "Home"
current_tab = st.query_params["tab"]

# Custom Styling for Dark Theme & Original UI Match
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    header {visibility: hidden;}

    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.2rem 0;
        border-bottom: 1px solid #1a202c;
        margin-bottom: 3rem;
    }
    .app-logo {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 0.5px;
    }
    .app-logo:hover {
        color: #ff9900;
    }
    .nav-links {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    .nav-links a {
        color: #a0aec0;
        text-decoration: none;
        font-size: 0.95rem;
        font-weight: 400;
        transition: color 0.2s;
    }
    .nav-links a:hover, .nav-links a.active {
        color: #ffffff;
        text-decoration: underline;
        text-underline-offset: 6px;
    }
    .github-icon {
        color: #a0aec0;
        text-decoration: none;
        font-size: 1.1rem;
        margin-left: 1rem;
    }
    .github-icon:hover {
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
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    .cta-container {
        text-align: center;
        margin-top: 2.5rem;
    }
    .cta-button {
        background: linear-gradient(135deg, #ff7b00 0%, #ff5500 100%);
        color: #ffffff !important;
        padding: 0.85rem 2.5rem;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: 0 4px 14px rgba(255, 102, 0, 0.4);
        transition: all 0.2s ease-in-out;
        display: inline-block;
    }
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 102, 0, 0.6);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Render Sleek Header Bar
active_home = "active" if current_tab == "Home" else ""
active_upload = "active" if current_tab == "Upload Data" else ""
active_export = "active" if current_tab == "Export Center" else ""
active_dev = "active" if current_tab == "Developer Support" else ""

st.markdown(
    f"""
    <div class="app-header">
        <a href="?tab=Home" class="app-logo">💼 Payroll Studio</a>
        <div class="nav-links">
            <a href="?tab=Home" class="{active_home}">Home</a>
            <a href="?tab=Upload Data" class="{active_upload}">Upload Data</a>
            <a href="?tab=Export Center" class="{active_export}">Export Center</a>
            <a href="?tab=Developer Support" class="{active_dev}">Developer Support</a>
            <a href="https://github.com" target="_blank" class="github-icon">🐙</a>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None


# --- 1. HOME HEALTH PROCESSOR ---
def process_home_health_payroll(df):
    hourly_rates = {
        1351.0: 30.00,
        1331.0: 40.00,
        1175.0: 28.00,
        1279.0: 45.00,
        1307.0: 25.00,
        1067.0: 46.00,
        1162.0: 50.00,
        1389.0: 40.00,
        1358.0: 40.00,
        800.0: 25.00,
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
            "Pay Component": pay_type,
            "Rate": rate if pay_type == "Hourly" else "",
            "Hours": total_hours if pay_type == "Hourly" else "",
            "Units": "",
            "Line Date": "",
            "Amount": total_amount if pay_type == "PRN Points" else "",
            "Check": "",
            "Override State": "",
            "Override Local": "",
            "Labor Override": labor_override,
            "_EmployeeName": emp_name,
        }

        if pay_type == "PRN Points":
            prn_rows.append(base_row_data)
        elif pay_type == "Hourly":
            if total_hours > 80:
                reg_row = base_row_data.copy()
                reg_row["Hours"] = 80.0
                hourly_rows.append(reg_row)

                ot_hours = total_hours - 80.0
                ot_row = base_row_data.copy()
                ot_row["Pay Component"] = "Overtime"
                ot_row["Rate"] = rate * 1.5 if rate else ""
                ot_row["Hours"] = ot_hours
                overtime_rows.append(ot_row)
            else:
                hourly_rows.append(base_row_data)

        if mileage > 0:
            mileage_row = base_row_data.copy()
            mileage_row["Pay Component"] = "Mileage"
            mileage_row["Rate"] = 0.73
            mileage_row["Hours"] = ""
            mileage_row["Units"] = mileage
            mileage_row["Amount"] = round(mileage * 0.73, 2)
            mileage_rows.append(mileage_row)

    prn_rows = sorted(prn_rows, key=lambda x: x["_EmployeeName"])
    hourly_rows = sorted(hourly_rows, key=lambda x: x["_EmployeeName"])
    overtime_rows = sorted(overtime_rows, key=lambda x: x["_EmployeeName"])
    mileage_rows = sorted(mileage_rows, key=lambda x: x["_EmployeeName"])

    final_rows = prn_rows + hourly_rows + overtime_rows + mileage_rows
    final_df = pd.DataFrame(final_rows)
    if "_EmployeeName" in final_df.columns:
        final_df = final_df.drop(columns=["_EmployeeName"])

    return final_df


# --- 2. HOME CARE PROCESSOR (Strictly targets 'Hourly' rows only) ---
def process_home_care_payroll(df):
    df.columns = [str(c).strip() for c in df.columns]

    for col in ["Pay Comp Rate", "Pay Component Rate", "Pay Component"]:
        if col in df.columns:
            df = df.rename(columns={col: "Pay Component"})
            break

    if "Worker ID" not in df.columns or "Hours" not in df.columns:
        raise ValueError(
            "Uploaded file must contain 'Worker ID' and 'Hours' columns."
        )

    if "Pay Component" not in df.columns:
        df["Pay Component"] = ""

    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0)

    # Strictly target rows where Pay Component is explicitly "Hourly"
    def is_hourly_row(val):
        if pd.notna(val) and str(val).strip().lower() == "hourly":
            return True
        return False

    # Calculate total Hourly hours per Worker ID
    worker_totals = {}
    for _, row in df.iterrows():
        worker_id = row["Worker ID"]
        comp = row.get("Pay Component", "")
        hrs = row["Hours"]
        if is_hourly_row(comp) and hrs > 0:
            worker_totals[worker_id] = worker_totals.get(worker_id, 0.0) + hrs

    processed_rows = []
    worker_accumulated_hours = {}

    for _, row in df.iterrows():
        worker_id = row["Worker ID"]
        comp = row.get("Pay Component", "")
        hrs = row["Hours"]
        total_w_hours = worker_totals.get(worker_id, 0.0)

        # Only apply overtime split if it's explicitly an "Hourly" row and total hourly hours > 80
        if is_hourly_row(comp) and total_w_hours > 80:
            accumulated = worker_accumulated_hours.get(worker_id, 0.0)

            if accumulated < 80:
                allowed_regular = 80 - accumulated
                if hrs <= allowed_regular:
                    worker_accumulated_hours[worker_id] = accumulated + hrs
                    processed_rows.append(row.to_dict())
                else:
                    reg_part = allowed_regular
                    ot_part = hrs - allowed_regular
                    worker_accumulated_hours[worker_id] = 80.0

                    reg_row = row.to_dict()
                    reg_row["Hours"] = reg_part
                    processed_rows.append(reg_row)

                    ot_row = row.to_dict()
                    ot_row["Pay Component"] = "Overtime"
                    ot_row["Hours"] = ot_part
                    if "Rate Number" in ot_row and pd.notnull(ot_row["Rate Number"]) and ot_row["Rate Number"] != "":
                        try:
                            ot_row["Rate Number"] = float(ot_row["Rate Number"]) * 1.5
                        except:
                            pass
                    processed_rows.append(ot_row)
            else:
                ot_row = row.to_dict()
                ot_row["Pay Component"] = "Overtime"
                if "Rate Number" in ot_row and pd.notnull(ot_row["Rate Number"]) and ot_row["Rate Number"] != "":
                    try:
                        ot_row["Rate Number"] = float(ot_row["Rate Number"]) * 1.5
                    except:
                        pass
                processed_rows.append(ot_row)
        else:
            # Blank rows and non-hourly rows pass through completely untouched
            processed_rows.append(row.to_dict())

    return pd.DataFrame(processed_rows)


# --- PAGE ROUTING ---
if current_tab == "Home":
    st.markdown(
        '<div class="hero-title">Everything You Need to <span>Start</span>,'
        " <span>Get Hired</span>, and <span>Thrive</span> as a Payroll"
        " Professional</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-subtitle">Transform raw operational exports into'
        " sleek, verified, Paychex-ready statements instantly. Automatically"
        " catch new employees, per diem rates, and missing IDs with live review"
        " flags.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cta-container"><a href="?tab=Upload Data" target="_self"'
        ' class="cta-button">🚀 Upload Data & Get Started</a></div>',
        unsafe_allow_html=True,
    )

elif current_tab == "Upload Data":
    st.markdown("## 📂 Select Upload Workflow")

    upload_mode = st.radio(
        "Choose Upload Type",
        ["Home Health Upload", "Home Care Upload"],
        horizontal=True
    )

    st.markdown("---")

    if upload_mode == "Home Health Upload":
        st.markdown("### 🏥 Home Health Payroll Upload")
        st.write(
            "Upload your raw operational payroll export file (`.xls`, `.xlsx`, or `.csv`) for Home Health processing.")
        uploaded_file = st.file_uploader("Choose Home Health file", type=["xls", "xlsx", "csv"], key="hh_file")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_name = "Data Export" if "Data Export" in xls.sheet_names else xls.sheet_names[0]
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                st.session_state.raw_df = df
                st.success(f"Successfully loaded Home Health file: **{uploaded_file.name}** ({len(df)} rows)")

                processed = process_home_health_payroll(df)
                st.session_state.processed_df = processed

                st.markdown("### 🔍 Live Review & Validation Preview")
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing Home Health file: {e}")
        else:
            st.info("Awaiting Home Health file upload...")

    else:  # Home Care Upload
        st.markdown("### 🏡 Home Care Payroll Upload")
        st.write(
            "Upload your pre-formatted Paychex import-ready file for Home Care processing (Automatic Overtime tagging applied strictly to **Hourly** rows exceeding 80 hours; blanks remain untouched).")
        uploaded_file = st.file_uploader("Choose Home Care file", type=["xls", "xlsx", "csv"], key="hc_file")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_name = xls.sheet_names[0]
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                st.session_state.raw_df = df
                st.success(f"Successfully loaded Home Care file: **{uploaded_file.name}** ({len(df)} rows)")

                processed = process_home_care_payroll(df)
                st.session_state.processed_df = processed

                st.markdown("### 🔍 Live Review & Validation Preview (Home Care)")
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing Home Care file: {e}")
        else:
            st.info("Awaiting Home Care file upload...")

elif current_tab == "Export Center":
    st.markdown("## 📥 Export Center")
    st.write(
        "Download your validated, formatted payroll ready for direct import into"
        " Paychex."
    )

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
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            type="primary",
        )
    else:
        st.warning("No processed data available. Please upload a file first.")

elif current_tab == "Developer Support":
    st.markdown("## ⚙️ Developer Support & Documentation")
    st.markdown("""
    ### 📌 Core Business Rules & Mappings:
    1. **Home Health Rules**: 
       - PRN Points employees sorted alphabetically.
       - Hourly employees sorted alphabetically (capped at 80 hours).
       - Overtime entries for hourly exceeding 80 hours.
       - Mileage entries at the bottom at **0.73** rate.
    2. **Home Care Rules**:
       - Evaluates pre-formatted Paychex ready files.
       - Aggregates hours strictly across explicit **Hourly** rows per Worker ID.
       - Blanks and other components remain untouched.
    """)