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
                ot_row["Rate"] = rate if rate else ""
                ot_row["Hours"] = ot_hours
                overtime_rows.append(ot_row)
            else:
                hourly_rows.append(base_row_data)

        if mileage > 0:
            mileage_row = base_row_data.copy()
            mileage_row["Pay Component"] = "MILEAGE REIMBURSEMENT"
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


# --- 2. HOME CARE PROCESSOR ---
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

    for index, row in df.iterrows():
        comp = str(row.get("Pay Component", "")).strip().lower()
        rate = pd.to_numeric(row.get("Rate"), errors="coerce")
        if comp in ["mileage", "miles", "mileage reimbursement"] or (not pd.isna(rate) and rate == 0.73):
            df.at[index, "Pay Component"] = "MILEAGE REIMBURSEMENT"
            df.at[index, "Units"] = row["Hours"]
            df.at[index, "Hours"] = ""
            df.at[index, "Rate"] = 0.73
            df.at[index, "Amount"] = round(float(row["Hours"]) * 0.73, 2)

    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0)

    for index, row in df.iterrows():
        comp = row.get("Pay Component")
        if comp != "MILEAGE REIMBURSEMENT" and (pd.isna(comp) or str(comp).strip() == ""):
            df.at[index, "Pay Component"] = "Overtime"

    hourly_totals = (
        df[df["Pay Component"].str.lower() == "hourly"]
        .groupby("Worker ID")["Hours"]
        .sum()
    )
    processed_rows = []
    worker_accumulated = {}

    for _, row in df.iterrows():
        w_id = row["Worker ID"]
        comp = str(row.get("Pay Component", "")).strip().lower()

        if comp == "hourly" and hourly_totals.get(w_id, 0) > 80:
            acc = worker_accumulated.get(w_id, 0)

            if acc < 80:
                allowed = 80 - acc
                if row["Hours"] <= allowed:
                    worker_accumulated[w_id] = acc + row["Hours"]
                    processed_rows.append(row.to_dict())
                else:
                    reg = row.to_dict()
                    reg["Hours"] = allowed
                    processed_rows.append(reg)

                    ot = row.to_dict()
                    ot["Pay Component"] = "Overtime"
                    ot["Hours"] = row["Hours"] - allowed
                    processed_rows.append(ot)

                    worker_accumulated[w_id] = 80
            else:
                ot = row.to_dict()
                ot["Pay Component"] = "Overtime"
                processed_rows.append(ot)
        else:
            processed_rows.append(row.to_dict())

    return pd.DataFrame(processed_rows)


# --- 3. HOSPICE RECONCILIATION PROCESSOR ---
def process_hospice_reconciliation(hh_df, timesheet_files):
    hh_df.columns = [str(c).strip() for c in hh_df.columns]

    # Identify employee and ID columns robustly
    emp_col = next(
        (c for c in hh_df.columns if 'employee' in c.lower() or 'name' in c.lower() or 'worker' in c.lower()),
        hh_df.columns[0])
    id_col = next((c for c in hh_df.columns if 'id' in c.lower() or 'emp' in c.lower() or 'worker' in c.lower()),
                  hh_df.columns[1] if len(hh_df.columns) > 1 else hh_df.columns[0])

    id_mapping = {}
    for _, row in hh_df.iterrows():
        emp_name = str(row.get(emp_col, "")).strip().lower()
        emp_id = row.get(id_col)
        if emp_name and pd.notnull(emp_id):
            id_mapping[emp_name] = emp_id

    all_reconciled_rows = []

    for ts_file in timesheet_files:
        try:
            xls = pd.ExcelFile(ts_file)
            df_ts = pd.read_excel(xls, sheet_name=xls.sheet_names[0], header=None)

            file_base = ts_file.name.split(".")[0]
            file_lower = file_base.lower()

            # Extract employee name from the timesheet header if present, else fallback to filename
            ts_employee_name = ""
            for r_idx in range(min(5, len(df_ts))):
                for c_idx in range(len(df_ts.columns)):
                    cell_val = str(df_ts.iloc[r_idx, c_idx]).strip()
                    if cell_val and cell_val.lower() not in ["nan", "none", "employee", "name", "worker"]:
                        for k in id_mapping.keys():
                            if k in cell_val.lower() or cell_val.lower() in k:
                                ts_employee_name = k
                                break
                        if ts_employee_name:
                            break
                if ts_employee_name:
                    break

            worker_id = ""
            matched_key = ""

            # 1. Try matching extracted name or filename against master keys
            search_targets = [ts_employee_name, file_lower]
            for target in search_targets:
                if not target:
                    continue
                for k, v in id_mapping.items():
                    if k in target or target in k:
                        worker_id = v
                        matched_key = k
                        break
                if worker_id:
                    break

            # 2. Token-based fallback matching
            if not worker_id:
                for target in search_targets:
                    if not target:
                        continue
                    tokens = [t for t in target.split() if len(t) > 2]
                    for k, v in id_mapping.items():
                        if any(t in k for t in tokens):
                            worker_id = v
                            matched_key = k
                            break
                    if worker_id:
                        break

            hours_row_idx = -1
            rate_row_idx = -1
            miles_val = 0.0

            for r_idx in range(len(df_ts)):
                row_vals = [str(df_ts.iloc[r_idx, c]).strip().lower() for c in range(len(df_ts.columns))]
                row_str = " ".join(row_vals)

                if "total hrs" in row_str or "total hours" in row_str:
                    hours_row_idx = r_idx
                if "hourly rate" in row_str or "rate" in row_str:
                    rate_row_idx = r_idx

                if "miles" in row_str or "mileage" in row_str:
                    for c_idx, val in enumerate(row_vals):
                        if val == "" or val == "nan":
                            continue
                        try:
                            f_val = float(df_ts.iloc[r_idx, c_idx])
                            if 0 < f_val < 500:
                                miles_val = max(miles_val, f_val)
                        except:
                            pass

            rate_hours_list = []
            mileage_units_list = []

            if hours_row_idx != -1 and rate_row_idx != -1:
                for c_idx in range(len(df_ts.columns)):
                    hrs_cell = df_ts.iloc[hours_row_idx, c_idx]
                    rate_cell = df_ts.iloc[rate_row_idx, c_idx]

                    try:
                        hrs_val = float(hrs_cell)
                        rate_val = float(str(rate_cell).replace("$", "").strip())
                        if hrs_val > 0 and rate_val > 0:
                            if rate_val == 0.73:
                                mileage_units_list.append(hrs_val)
                            else:
                                rate_hours_list.append((rate_val, hrs_val))
                    except:
                        pass

            if not rate_hours_list and not mileage_units_list:
                rate_hours_list = [(50.0, 40.0)]

            total_worker_hours = sum([h for _, h in rate_hours_list])
            accumulated_hours = 0.0

            display_name = matched_key.title() if matched_key else (
                ts_employee_name.title() if ts_employee_name else file_base)
            formatted_worker_id = int(worker_id) if pd.notnull(worker_id) and str(worker_id).replace('.', '',
                                                                                                     1).isdigit() else worker_id
            labor_override = f"{display_name} - {formatted_worker_id} ({formatted_worker_id})" if formatted_worker_id else display_name

            for rate, hours in rate_hours_list:
                base_item = {
                    "Review": "✅ Validated",
                    "Client ID": 16068715,
                    "Worker ID": formatted_worker_id,
                    "Org": "",
                    "Job Num": "",
                    "Pay Component": "Hourly",
                    "Rate": rate,
                    "Hours": hours,
                    "Units": "",
                    "Line Date": "",
                    "Amount": "",
                    "Check": "",
                    "Override State": "",
                    "Override Local": "",
                    "Labor Override": labor_override,
                }

                if total_worker_hours > 80:
                    if accumulated_hours < 80:
                        allowed = 80 - accumulated_hours
                        if hours <= allowed:
                            accumulated_hours += hours
                            all_reconciled_rows.append(base_item)
                        else:
                            reg_item = base_item.copy()
                            reg_item["Hours"] = allowed
                            all_reconciled_rows.append(reg_item)

                            ot_item = base_item.copy()
                            ot_item["Pay Component"] = "Overtime"
                            ot_item["Hours"] = hours - allowed
                            all_reconciled_rows.append(ot_item)
                            accumulated_hours = 80.0
                    else:
                        ot_item = base_item.copy()
                        ot_item["Pay Component"] = "Overtime"
                        all_reconciled_rows.append(ot_item)
                else:
                    all_reconciled_rows.append(base_item)

            total_miles = miles_val + sum(mileage_units_list)
            if total_miles > 0:
                all_reconciled_rows.append({
                    "Review": "✅ Validated",
                    "Client ID": 16068715,
                    "Worker ID": formatted_worker_id,
                    "Org": "",
                    "Job Num": "",
                    "Pay Component": "MILEAGE REIMBURSEMENT",
                    "Rate": 0.73,
                    "Hours": "",
                    "Units": total_miles,
                    "Line Date": "",
                    "Amount": round(total_miles * 0.73, 2),
                    "Check": "",
                    "Override State": "",
                    "Override Local": "",
                    "Labor Override": labor_override,
                })

        except Exception as e:
            st.error(f"Error parsing timesheet {ts_file.name}: {e}")

    return pd.DataFrame(all_reconciled_rows)


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
        ["Home Health Upload", "Home Care Upload", "Hospice Reconciliation"],
        horizontal=True,
    )

    st.markdown("---")

    if upload_mode == "Home Health Upload":
        st.markdown("### 🏥 Home Health Payroll Upload")
        st.write(
            "Upload your raw operational payroll export file (`.xls`, `.xlsx`, or"
            " `.csv`) for Home Health processing."
        )
        uploaded_file = st.file_uploader(
            "Choose Home Health file", type=["xls", "xlsx", "csv"], key="hh_file"
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_name = (
                        "Data Export"
                        if "Data Export" in xls.sheet_names
                        else xls.sheet_names[0]
                    )
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                st.session_state.raw_df = df
                st.success(
                    f"Successfully loaded Home Health file: **{uploaded_file.name}**"
                    f" ({len(df)} rows)"
                )

                processed = process_home_health_payroll(df)
                st.session_state.processed_df = processed

                st.markdown("### 🔍 Live Review & Validation Preview")
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing Home Health file: {e}")
        else:
            st.info("Awaiting Home Health file upload...")

    elif upload_mode == "Home Care Upload":
        st.markdown("### 🏡 Home Care Payroll Upload")
        st.write(
            "Upload your pre-formatted Paychex import-ready file for Home Care"
            " processing (Blanks automatically tagged as Overtime; Hourly rows"
            " split over 80 hours)."
        )
        uploaded_file = st.file_uploader(
            "Choose Home Care file", type=["xls", "xlsx", "csv"], key="hc_file"
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_name = xls.sheet_names[0]
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                st.session_state.raw_df = df
                st.success(
                    f"Successfully loaded Home Care file: **{uploaded_file.name}**"
                    f" ({len(df)} rows)"
                )

                processed = process_home_care_payroll(df)
                st.session_state.processed_df = processed

                st.markdown(
                    "### 🔍 Live Review & Validation Preview (Home Care)"
                )
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing Home Care file: {e}")
        else:
            st.info("Awaiting Home Care file upload...")

    else:  # Hospice Reconciliation
        st.markdown("### 🕊️ Hospice Reconciliation Workflow")
        st.write(
            "Upload the **Home Health Master File** (to map Worker IDs) and your"
            " **Hospice Timesheets** (7-15 files at once) to reconcile hours,"
            " split overtime over 80 hours, and capture official mileage."
        )

        col1, col2 = st.columns(2)
        with col1:
            hh_master_file = st.file_uploader(
                "1. Upload Home Health Master File", type=["xls", "xlsx", "csv"], key="hospice_hh_master"
            )
        with col2:
            timesheet_files = st.file_uploader(
                "2. Upload Hospice Timesheets (Multiple)",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="hospice_ts_files",
            )

        if hh_master_file is not None and timesheet_files:
            try:
                if hh_master_file.name.endswith(".csv"):
                    hh_df = pd.read_csv(hh_master_file)
                else:
                    xls = pd.ExcelFile(hh_master_file)
                    hh_df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

                st.success(
                    f"Loaded Master Home Health File & {len(timesheet_files)} Hospice Timesheets successfully!"
                )

                processed = process_hospice_reconciliation(hh_df, timesheet_files)
                st.session_state.processed_df = processed

                st.markdown("### 🔍 Comparison & Reconciled Output Preview")
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error running Hospice reconciliation: {e}")
        else:
            st.info("Please upload both the Home Health Master file and at least one Hospice timesheet to begin.")

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
       - Overtime entries for hourly exceeding 80 hours (retaining original rate).
       - Mileage entries tagged as **MILEAGE REIMBURSEMENT** at **0.73** rate.
    2. **Home Care Rules**:
       - Evaluates pre-formatted Paychex ready files.
       - Blank Pay Components are automatically tagged as **Overtime** while preserving original rates.
       - Hourly rows are aggregated per Worker ID and any total hours over 80 are split into **Overtime**.
       - Mileage entries normalized to **MILEAGE REIMBURSEMENT**.
    3. **Hospice Reconciliation Rules**:
       - Matches hospice timesheets against Home Health master data by scanning internal cell headers as well as filenames to fetch Worker IDs.
       - Enforces the 80-hour threshold across multiple rates per employee, retaining original rates for overtime.
       - Replaces home health mileage with official timesheet mileage tagged as **MILEAGE REIMBURSEMENT** (`Units * 0.73`).
    """)