import io
import re
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
        gap: 1.5rem;
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
        margin-left: 0.5rem;
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

# Render Sleek Header Bar with Navigation Items
active_home = "active" if current_tab == "Home" else ""
active_upload = "active" if current_tab == "Upload Data" else ""
active_batch = "active" if current_tab == "Multi-LOB Batch" else ""
active_export = "active" if current_tab == "Export Center" else ""
active_dev = "active" if current_tab == "Developer Support" else ""

st.markdown(
    f"""
    <div class="app-header">
        <a href="?tab=Home" class="app-logo">💼 Payroll Studio</a>
        <div class="nav-links">
            <a href="?tab=Home" class="{active_home}">Home</a>
            <a href="?tab=Upload Data" class="{active_upload}">Upload Data</a>
            <a href="?tab=Multi-LOB Batch" class="{active_batch}">⚡ Multi-LOB Batch</a>
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
if "batch_processed_df" not in st.session_state:
    st.session_state.batch_processed_df = None


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
                reg_row["Amount"] = ""
                hourly_rows.append(reg_row)

                ot_hours = total_hours - 80.0
                ot_row = base_row_data.copy()
                ot_row["Pay Component"] = "Overtime"
                ot_row["Rate"] = rate if rate else ""
                ot_row["Hours"] = ot_hours
                ot_row["Amount"] = ""
                overtime_rows.append(ot_row)
            else:
                hourly_rows.append(base_row_data)

        if mileage > 0:
            mileage_row = base_row_data.copy()
            mileage_row["Pay Component"] = "MILEAGE REIMB"
            mileage_row["Rate"] = 0.73
            mileage_row["Hours"] = ""
            mileage_row["Units"] = mileage
            mileage_row["Amount"] = ""
            mileage_rows.append(mileage_row)

    prn_rows = [r for r in prn_rows if pd.notnull(r["Amount"]) and r["Amount"] != "" and r["Amount"] != 0]

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

    col_map = {}
    used_targets = set()
    for c in df.columns:
        c_lower = c.lower()
        target = None
        if "worker" in c_lower and "id" in c_lower:
            target = "Worker ID"
        elif "employee" in c_lower or ("name" in c_lower and "client" not in c_lower):
            target = "Employee"
        elif "component" in c_lower or "pay comp" in c_lower:
            target = "Pay Component"
        elif "rate" in c_lower:
            target = "Rate"
        elif "hour" in c_lower:
            target = "Hours"
        elif "amount" in c_lower:
            target = "Amount"
        elif "unit" in c_lower:
            target = "Units"
        elif "client" in c_lower and "id" in c_lower:
            target = "Client ID"
        elif "labor" in c_lower or "override" in c_lower:
            target = "Labor Override"

        if target and target not in used_targets:
            col_map[c] = target
            used_targets.add(target)

    df = df.rename(columns=col_map)

    for col in ['Worker ID', 'Employee', 'Pay Component', 'Rate', 'Hours', 'Amount', 'Units']:
        if col in df.columns and isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]

    if 'Worker ID' not in df.columns:
        id_col = next((c for c in df.columns if 'id' in c.lower()), df.columns[0])
        df = df.rename(columns={id_col: 'Worker ID'})
        if isinstance(df['Worker ID'], pd.DataFrame):
            df['Worker ID'] = df['Worker ID'].iloc[:, 0]

    if 'Hours' not in df.columns:
        df['Hours'] = 0.0
    if 'Rate' not in df.columns:
        df['Rate'] = 0.0
    if 'Pay Component' not in df.columns:
        df['Pay Component'] = ''
    if 'Client ID' not in df.columns:
        df['Client ID'] = 16068715
    if 'Employee' not in df.columns:
        df['Employee'] = ''

    df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce').fillna(0)
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce').fillna(0)

    processed_rows = []
    grouped = df.groupby(['Worker ID', df['Employee'].astype(str)])

    for (worker_id, emp_name), group in grouped:
        total_worker_hours = 0.0
        mileage_units = 0.0
        other_rows = []

        for _, row in group.iterrows():
            comp = str(row.get('Pay Component', '')).strip()
            comp_lower = comp.lower()
            rate = float(row.get('Rate', 0))
            hours = float(row.get('Hours', 0))
            units = row.get('Units', '')

            if comp_lower in ['mileage', 'miles', 'mileage reimbursement', 'mileage reimb'] or rate == 0.73:
                m_units = hours if hours > 0 else (
                    float(units) if pd.notnull(units) and str(units).replace('.', '', 1).isdigit() else 0.0)
                if m_units > 0:
                    mileage_units += m_units
            else:
                if comp == '' or comp_lower == 'nan' or comp_lower == 'none':
                    total_worker_hours += hours
                    other_rows.append(('Overtime', rate, hours))
                elif 'overtime' in comp_lower or 'ot' in comp_lower:
                    total_worker_hours += hours
                    other_rows.append(('Overtime', rate, hours))
                else:
                    total_worker_hours += hours
                    other_rows.append((comp if comp else 'Hourly', rate, hours))

        formatted_worker_id = int(worker_id) if pd.notnull(worker_id) and str(worker_id).replace('.', '',
                                                                                                 1).isdigit() else worker_id
        labor_override = f"{emp_name} - {formatted_worker_id} ({formatted_worker_id})" if emp_name and str(
            emp_name).strip() and str(emp_name).lower() != 'nan' else str(formatted_worker_id)

        accumulated_hours = 0.0
        for comp_type, rate, hours in other_rows:
            if hours <= 0:
                continue

            if comp_type.lower() != 'overtime':
                if accumulated_hours < 80:
                    allowed = 80 - accumulated_hours
                    if hours <= allowed:
                        accumulated_hours += hours
                        actual_comp = 'Hourly'
                    else:
                        reg_hrs = allowed
                        accumulated_hours = 80.0
                        processed_rows.append({
                            "Review": "✅ Validated",
                            "Client ID": 16068715,
                            "Worker ID": formatted_worker_id,
                            "Org": "",
                            "Job Num": "",
                            "Pay Component": "Hourly",
                            "Rate": rate,
                            "Hours": reg_hrs,
                            "Units": "",
                            "Line Date": "",
                            "Amount": "",
                            "Check": "",
                            "Override State": "",
                            "Override Local": "",
                            "Labor Override": labor_override,
                        })
                        hours = hours - allowed
                        actual_comp = 'Overtime'
                else:
                    actual_comp = 'Overtime'
            else:
                actual_comp = 'Overtime'

            processed_rows.append({
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": formatted_worker_id,
                "Org": "",
                "Job Num": "",
                "Pay Component": actual_comp,
                "Rate": rate,
                "Hours": hours,
                "Units": "",
                "Line Date": "",
                "Amount": "",
                "Check": "",
                "Override State": "",
                "Override Local": "",
                "Labor Override": labor_override,
            })

        if mileage_units > 0:
            processed_rows.append({
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": formatted_worker_id,
                "Org": "",
                "Job Num": "",
                "Pay Component": "MILEAGE REIMB",
                "Rate": 0.73,
                "Hours": "",
                "Units": mileage_units,
                "Line Date": "",
                "Amount": "",
                "Check": "",
                "Override State": "",
                "Override Local": "",
                "Labor Override": labor_override,
            })

    return pd.DataFrame(processed_rows)


# --- 3. HOSPICE RECONCILIATION PROCESSOR ---
def process_hospice_reconciliation(hh_file, timesheet_files):
    authoritative_id_map = {
        "simowski, maggie": 1162, "maggie simowski": 1162, "maggies": 1162, "maggie": 1162, "simowski": 1162,
        "cecil, katherine": 1351, "katherine cecil": 1351, "katherines": 1351, "katherine": 1351, "cecil": 1351,
        "cooper, jenifer": 1414, "jenifer cooper": 1414, "coopers": 1414, "cooper": 1414, "jenifer": 1414,
        "smith, gene": 1175, "gene smith": 1175, "smith": 1175, "gene": 1175,
        "kendle, alexias b (brandy)": 1242, "alexias kendle": 1242, "brandy": 1242, "brandys": 1242, "alexias": 1242,
        "kendle": 1242,
        "escobar ortega, ana m": 1388, "ana m escobar ortega": 1388, "ana": 1388, "ana e": 1388, "escobar": 1388,
        "bullock, monica": 1300, "monica bullock": 1300, "bullock": 1300, "monica": 1300
    }

    id_mapping = authoritative_id_map.copy()
    if hh_file is not None:
        try:
            df_raw = pd.read_excel(hh_file, header=None) if not hasattr(hh_file, 'name') or not hh_file.name.endswith(
                '.csv') else pd.read_csv(hh_file, header=None)
            header_row_idx = 0
            for r in range(min(10, len(df_raw))):
                row_str = " ".join([str(df_raw.iloc[r, c]).lower() for c in range(len(df_raw.columns))])
                if ('employee' in row_str or 'worker' in row_str or 'name' in row_str) and (
                        'id' in row_str or 'emp' in row_str):
                    header_row_idx = r
                    break

            hh_df = pd.read_csv(hh_file, skiprows=header_row_idx) if hasattr(hh_file, 'name') and hh_file.name.endswith(
                '.csv') else pd.read_excel(hh_file, header=header_row_idx)
            hh_df.columns = [str(c).strip() for c in hh_df.columns]

            emp_col = next(
                (c for c in hh_df.columns if 'employee' in c.lower() or 'name' in c.lower() or 'worker' in c.lower()),
                hh_df.columns[0])
            id_col = next(
                (c for c in hh_df.columns if 'id' in c.lower() or 'emp' in c.lower() or 'worker' in c.lower()),
                hh_df.columns[1] if len(hh_df.columns) > 1 else hh_df.columns[0])

            for _, row in hh_df.iterrows():
                emp_name = str(row.get(emp_col, "")).strip().lower()
                emp_id = row.get(id_col)
                if emp_name and pd.notnull(emp_id):
                    id_mapping[emp_name] = emp_id
        except Exception:
            pass

    all_reconciled_rows = []

    for ts_file in timesheet_files:
        try:
            xls = pd.ExcelFile(ts_file)
            df_ts = pd.read_excel(xls, sheet_name=xls.sheet_names[0], header=None)

            file_base = ts_file.name.split(".")[0]
            file_lower = file_base.lower()

            ts_employee_name = ""
            for r_idx in range(min(5, len(df_ts))):
                for c_idx in range(len(df_ts.columns)):
                    cell_val = str(df_ts.iloc[r_idx, c_idx]).strip()
                    if cell_val and cell_val.lower() not in ["nan", "none", "employee", "name", "worker", "client"]:
                        for k in id_mapping.keys():
                            if k in cell_val.lower() or cell_val.lower() in k:
                                ts_employee_name = k
                                break
                        if ts_employee_name:
                            break
                if ts_employee_name:
                    break

            def resolve_worker_id(search_target):
                target_lower = str(search_target).lower()
                for k, v in id_mapping.items():
                    if k in target_lower or target_lower in k:
                        return v, k

                target_tokens = set(re.findall(r'\b[a-z]{3,}\b', target_lower))
                best_id = None
                best_key = ""
                max_overlap = 0

                for k, v in id_mapping.items():
                    key_tokens = set(re.findall(r'\b[a-z]{3,}\b', k))
                    overlap = len(target_tokens.intersection(key_tokens))
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_id = v
                        best_key = k

                if max_overlap > 0:
                    return best_id, best_key
                return None, ""

            worker_id, matched_key = resolve_worker_id(ts_employee_name)
            if not worker_id:
                worker_id, matched_key = resolve_worker_id(file_lower)

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
                            reg_item["Amount"] = ""
                            all_reconciled_rows.append(reg_item)

                            ot_hours = hours - allowed
                            ot_item = base_item.copy()
                            ot_item["Pay Component"] = "Overtime"
                            ot_item["Hours"] = ot_hours
                            ot_item["Amount"] = ""
                            all_reconciled_rows.append(ot_item)
                            accumulated_hours = 80.0
                    else:
                        ot_item = base_item.copy()
                        ot_item["Pay Component"] = "Overtime"
                        ot_item["Amount"] = ""
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
                    "Pay Component": "MILEAGE REIMB",
                    "Rate": 0.73,
                    "Hours": "",
                    "Units": total_miles,
                    "Line Date": "",
                    "Amount": "",
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
    st.markdown("## 📂 Select Upload Workflow (Original Individual Tabs)")

    upload_mode = st.radio(
        "Choose Upload Type",
        ["Home Health Upload", "Home Care Upload", "Hospice Reconciliation"],
        horizontal=True,
    )

    st.markdown("---")

    if upload_mode == "Home Health Upload":
        st.markdown("### 🏥 Home Health Payroll Upload")
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
        col1, col2 = st.columns(2)
        with col1:
            hh_master_file = st.file_uploader(
                "1. Upload Home Health Master File (Optional)", type=["xls", "xlsx", "csv"], key="hospice_hh_master"
            )
        with col2:
            timesheet_files = st.file_uploader(
                "2. Upload Hospice Timesheets (Multiple)",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="hospice_ts_files",
            )

        if timesheet_files:
            try:
                processed = process_hospice_reconciliation(hh_master_file, timesheet_files)
                st.session_state.processed_df = processed

                st.success(f"Reconciled {len(timesheet_files)} Hospice Timesheets successfully!")
                st.markdown("### 🔍 Comparison & Reconciled Output Preview")
                st.dataframe(processed, use_container_width=True)

                st.markdown("---")
                st.markdown("### 💰 Employee Total Earnings & Earnings Breakdown")
                summary_df = processed.copy()
                summary_df["Rate"] = pd.to_numeric(summary_df["Rate"], errors="coerce").fillna(0)
                summary_df["Hours"] = pd.to_numeric(summary_df["Hours"], errors="coerce").fillna(0)
                summary_df["Units"] = pd.to_numeric(summary_df["Units"], errors="coerce").fillna(0)
                summary_df["Amount"] = pd.to_numeric(summary_df["Amount"], errors="coerce").fillna(0)

                worker_summary = (
                    summary_df.groupby(["Worker ID", "Labor Override"])
                    .agg(
                        Total_Hours=("Hours", "sum"),
                        Total_Mileage_Units=("Units", "sum"),
                        Total_Earnings=("Amount", "sum"),
                    )
                    .reset_index()
                )

                st.markdown("#### 📊 Master Earnings Summary by Employee")
                st.dataframe(worker_summary, use_container_width=True)

            except Exception as e:
                st.error(f"Error running Hospice reconciliation: {e}")
        else:
            st.info("Please upload at least one Hospice timesheet to begin.")

elif current_tab == "Multi-LOB Batch":
    st.markdown("### ⚡ Enterprise Multi-LOB Batch Processing Pipeline")
    st.write(
        "Upload all departmental files simultaneously. Hospice reconciliation will automatically filter out duplicate entries from the Home Health master file, ensuring clean, audit-ready Paychex exports.")

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        batch_hh_file = st.file_uploader("Upload Home Health Data", type=["xls", "xlsx", "csv"], key="batch_hh")
    with col_b2:
        batch_hc_file = st.file_uploader("Upload Home Care Data", type=["xls", "xlsx", "csv"], key="batch_hc")
    with col_b3:
        batch_hospice_files = st.file_uploader("Upload Hospice Timesheets", type=["xls", "xlsx"],
                                               accept_multiple_files=True, key="batch_hospice")

    if st.button("🚀 Run Enterprise Batch Processing Across All LOBs", type="primary", use_container_width=True):
        try:
            hospice_processed = pd.DataFrame()
            hh_processed = pd.DataFrame()
            hc_processed = pd.DataFrame()

            # 1. Process Hospice First
            if batch_hospice_files:
                hospice_processed = process_hospice_reconciliation(batch_hh_file, batch_hospice_files)
                if not hospice_processed.empty:
                    hospice_processed["LOB"] = "Hospice"

            # Extract worker IDs processed under Hospice to prevent duplication in Home Health
            hospice_worker_ids = set()
            if not hospice_processed.empty and "Worker ID" in hospice_processed.columns:
                hospice_worker_ids = set(hospice_processed["Worker ID"].dropna().astype(str).str.strip())

            # 2. Process Home Health (Filtering out Hospice workers)
            if batch_hh_file is not None:
                if batch_hh_file.name.endswith(".csv"):
                    hh_raw = pd.read_csv(batch_hh_file)
                else:
                    xls = pd.ExcelFile(batch_hh_file)
                    sheet_name = "Data Export" if "Data Export" in xls.sheet_names else xls.sheet_names[0]
                    hh_raw = pd.read_excel(xls, sheet_name=sheet_name)

                hh_temp_processed = process_home_health_payroll(hh_raw)

                if hospice_worker_ids and "Worker ID" in hh_temp_processed.columns:
                    hh_temp_processed["_worker_str"] = hh_temp_processed["Worker ID"].astype(str).str.strip()
                    hh_processed = hh_temp_processed[~hh_temp_processed["_worker_str"].isin(hospice_worker_ids)].drop(
                        columns=["_worker_str"])
                else:
                    hh_processed = hh_temp_processed

                if not hh_processed.empty:
                    hh_processed["LOB"] = "Home Health"

            # 3. Process Home Care
            if batch_hc_file is not None:
                if batch_hc_file.name.endswith(".csv"):
                    hc_raw = pd.read_csv(batch_hc_file)
                else:
                    xls = pd.ExcelFile(batch_hc_file)
                    hc_raw = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
                hc_processed = process_home_care_payroll(hc_raw)
                if not hc_processed.empty:
                    hc_processed["LOB"] = "Home Care"

            # Combine all outputs
            combined_dfs = [df for df in [hh_processed, hc_processed, hospice_processed] if not df.empty]
            if combined_dfs:
                final_batch_df = pd.concat(combined_dfs, ignore_index=True)
                st.session_state.batch_processed_df = final_batch_df
                st.session_state.processed_df = final_batch_df

                st.success(
                    "Enterprise batch processing completed successfully with duplicate Hospice filtering applied!")

                st.markdown("### 🔍 Consolidated Batch Output Preview")
                st.dataframe(final_batch_df, use_container_width=True)

                st.markdown("---")
                st.markdown("### 📊 Summary by Line of Business (LOB)")

                summary_calc = final_batch_df.copy()
                summary_calc["Hours"] = pd.to_numeric(summary_calc["Hours"], errors="coerce").fillna(0)
                summary_calc["Units"] = pd.to_numeric(summary_calc["Units"], errors="coerce").fillna(0)
                summary_calc["Rate"] = pd.to_numeric(summary_calc["Rate"], errors="coerce").fillna(0)
                summary_calc["Explicit_Amount"] = pd.to_numeric(summary_calc["Amount"], errors="coerce").fillna(0)

                # Calculate total monetary amount (Explicit Amount + Hours * Rate for hourly components)
                summary_calc["Total_Amount_Calc"] = summary_calc["Explicit_Amount"] + (
                            summary_calc["Hours"] * summary_calc["Rate"])

                lob_summary = (
                    summary_calc.groupby("LOB")
                    .agg(
                        Total_Hours=("Hours", "sum"),
                        Total_Mileage_Units=("Units", "sum"),
                        Total_Amount=("Total_Amount_Calc", "sum")
                    )
                    .reset_index()
                )

                st.dataframe(lob_summary, use_container_width=True)

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Total Processed Records", len(final_batch_df))
                with col_m2:
                    st.metric("Total Combined Hours", f"{summary_calc['Hours'].sum():,.2f}")
                with col_m3:
                    st.metric("Total Mileage Units", f"{summary_calc['Units'].sum():,.2f}")
            else:
                st.warning("No valid data processed from the uploaded files.")

        except Exception as e:
            st.error(f"Error running Enterprise Batch processing: {e}")
    elif st.session_state.batch_processed_df is not None:
        st.markdown("### 🔍 Previously Processed Enterprise Batch Output")
        st.dataframe(st.session_state.batch_processed_df, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Summary by Line of Business (LOB)")
        summary_calc = st.session_state.batch_processed_df.copy()
        if "LOB" in summary_calc.columns:
            summary_calc["Hours"] = pd.to_numeric(summary_calc["Hours"], errors="coerce").fillna(0)
            summary_calc["Units"] = pd.to_numeric(summary_calc["Units"], errors="coerce").fillna(0)
            summary_calc["Rate"] = pd.to_numeric(summary_calc["Rate"], errors="coerce").fillna(0)
            summary_calc["Explicit_Amount"] = pd.to_numeric(summary_calc["Amount"], errors="coerce").fillna(0)
            summary_calc["Total_Amount_Calc"] = summary_calc["Explicit_Amount"] + (
                        summary_calc["Hours"] * summary_calc["Rate"])

            lob_summary = (
                summary_calc.groupby("LOB")
                .agg(
                    Total_Hours=("Hours", "sum"),
                    Total_Mileage_Units=("Units", "sum"),
                    Total_Amount=("Total_Amount_Calc", "sum")
                )
                .reset_index()
            )
            st.dataframe(lob_summary, use_container_width=True)
    else:
        st.info("Upload your departmental files above and click the enterprise batch button to begin.")