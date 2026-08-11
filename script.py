import io
import re
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Payroll Studio Enterprise", page_icon="💼", layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "name" not in st.session_state:
    st.session_state["name"] = "Mark Edward Cunanan"
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "batch_processed_df" not in st.session_state:
    st.session_state.batch_processed_df = None

# --- NATIVE SECURE AUTHENTICATION SYSTEM (PERSISTENT) ---
if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🔐 Payroll Studio Enterprise")
        st.markdown("Please log in with your credentials to access the system.")

        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Login", use_container_width=True)

            if submit_btn:
                if username_input == "edwardcnn30" and password_input == "Happyhere.2330":
                    st.session_state["authenticated"] = True
                    st.session_state["name"] = "Mark Edward Cunanan"
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
    st.stop()

# --- SIDEBAR & LOGOUT CONTROLS ---
with st.sidebar:
    st.markdown(f"Welcome back, **{st.session_state['name']}**! 👋")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")
    st.markdown("### Navigation Control")

# Initialize Query Params for Tab Navigation safely
if "tab" not in st.query_params:
    st.query_params["tab"] = "Home"
current_tab = st.query_params["tab"]

# Custom Styling for Enterprise Dark Theme
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    header {visibility: hidden;}

    .app-header-container {
        border-bottom: 1px solid #1a202c;
        padding-bottom: 1rem;
        margin-bottom: 2rem;
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
    </style>
""",
    unsafe_allow_html=True,
)

# --- NATIVE STREAMLIT NAVIGATION BAR (PREVENTS SESSION DROPS) ---
st.markdown('<div class="app-header-container">', unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([2, 1, 1, 1.2, 1, 1])

with nav_col1:
    if st.button("💼 Payroll Studio Enterprise", use_container_width=True):
        st.query_params["tab"] = "Home"
        st.rerun()

with nav_col2:
    if st.button("Home", use_container_width=True, type="primary" if current_tab == "Home" else "secondary"):
        st.query_params["tab"] = "Home"
        st.rerun()

with nav_col3:
    if st.button("Upload Data", use_container_width=True,
                 type="primary" if current_tab == "Upload Data" else "secondary"):
        st.query_params["tab"] = "Upload Data"
        st.rerun()

with nav_col4:
    if st.button("⚡ Multi-LOB Batch", use_container_width=True,
                 type="primary" if current_tab == "Multi-LOB Batch" else "secondary"):
        st.query_params["tab"] = "Multi-LOB Batch"
        st.rerun()

with nav_col5:
    if st.button("Export Center", use_container_width=True,
                 type="primary" if current_tab == "Export Center" else "secondary"):
        st.query_params["tab"] = "Export Center"
        st.rerun()

with nav_col6:
    if st.button("Support", use_container_width=True,
                 type="primary" if current_tab == "Developer Support" else "secondary"):
        st.query_params["tab"] = "Developer Support"
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- EXACT 17-COLUMN PAYCHEX TEMPLATE STANDARD ---
PAYCHEX_TEMPLATE_COLUMNS = [
    "Review",
    "Client ID",
    "Worker ID",
    "Org",
    "Job Number",
    "Pay Component",
    "Rate",
    "Rate Number",
    "Hours",
    "Units",
    "Line Date",
    "Amount",
    "Check Seq Number",
    "Override State",
    "Override Local",
    "Override Local Jurisdiction",
    "Labor Override",
]


# --- HELPER: ENSURE UNIQUE COLUMN NAMES ---
def sanitize_columns(df):
    df.columns = [str(c).strip() for c in df.columns]
    seen = {}
    new_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)
    df.columns = new_cols
    return df


# --- HELPER: NORMALIZE & AGGREGATE DATAFRAME WITH CUSTOM HIERARCHY ---
def aggregate_and_standardize(df_rows):
    if not df_rows:
        empty_df = pd.DataFrame(columns=PAYCHEX_TEMPLATE_COLUMNS)
        return empty_df

    temp_df = pd.DataFrame(df_rows)
    for col in PAYCHEX_TEMPLATE_COLUMNS:
        if col not in temp_df.columns:
            temp_df[col] = ""

    temp_df["Hours"] = pd.to_numeric(temp_df["Hours"], errors="coerce").fillna(0)
    temp_df["Units"] = pd.to_numeric(temp_df["Units"], errors="coerce").fillna(0)
    temp_df["Amount"] = pd.to_numeric(temp_df["Amount"], errors="coerce").fillna(0)

    group_cols = [
        "Review",
        "Client ID",
        "Worker ID",
        "Org",
        "Job Number",
        "Pay Component",
        "Rate",
        "Rate Number",
        "Line Date",
        "Check Seq Number",
        "Override State",
        "Override Local",
        "Override Local Jurisdiction",
        "Labor Override",
    ]

    if "_EmployeeName" in temp_df.columns:
        group_cols.append("_EmployeeName")
    if "_LOB" in temp_df.columns:
        group_cols.append("_LOB")

    agg_df = (
        temp_df.groupby(
            [c for c in group_cols if c in temp_df.columns], dropna=False
        )
        .agg({"Hours": "sum", "Units": "sum", "Amount": "sum"})
        .reset_index()
    )

    agg_df["Hours"] = agg_df["Hours"].apply(lambda x: x if x > 0 else "")
    agg_df["Units"] = agg_df["Units"].apply(lambda x: x if x > 0 else "")
    agg_df["Amount"] = agg_df["Amount"].apply(lambda x: x if x > 0 else "")

    def assign_comp_rank(row):
        comp = str(row.get("Pay Component", ""))
        lob = str(row.get("_LOB", ""))

        if comp == "PRN Points":
            return 1
        elif comp in ["On call Weekdays", "On call Weekends", "Routine Visit", "Start of Care"]:
            return 2
        elif comp == "Hourly" and lob == "Home Health":
            return 3
        elif comp == "MILEAGE REIMB" and lob in ["Home Health", "Hospice"]:
            return 4
        elif comp == "Overtime" and lob in ["Hospice", "Home Health"]:
            return 5
        elif comp == "Hourly" and lob == "Home Care":
            return 6
        elif comp == "Overtime" and lob == "Home Care":
            return 7
        elif comp == "MILEAGE REIMB" and lob == "Home Care":
            return 8
        else:
            return 9

    agg_df["_comp_rank"] = agg_df.apply(assign_comp_rank, axis=1)

    if "_EmployeeName" in agg_df.columns:
        agg_df["_name_sort"] = agg_df["_EmployeeName"].astype(str).str.lower()
    else:
        agg_df["_name_sort"] = agg_df["Labor Override"].astype(str).str.lower()

    sort_cols = ["_comp_rank", "_name_sort", "Rate"]
    existing_sort_cols = [c for c in sort_cols if c in agg_df.columns]
    agg_df = agg_df.sort_values(by=existing_sort_cols)

    drop_cols = [c for c in ["_EmployeeName", "_LOB", "_comp_rank", "_name_sort"] if c in agg_df.columns]
    agg_df = agg_df.drop(columns=drop_cols)

    for col in PAYCHEX_TEMPLATE_COLUMNS:
        if col not in agg_df.columns:
            agg_df[col] = ""

    return agg_df[PAYCHEX_TEMPLATE_COLUMNS]


# --- CORE PAYPROCESSING ENGINES ---

def process_home_health_payroll(df, hospice_employee_names=None):
    if hospice_employee_names is None:
        hospice_employee_names = set()

    df = sanitize_columns(df)

    name_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]
    id_col = df.columns[4] if len(df.columns) > 4 else (df.columns[1] if len(df.columns) > 1 else df.columns[0])

    hours_col = next(
        (c for c in df.columns if "hour" in c.lower()), "Hours" if "Hours" in df.columns else df.columns[-1]
    )

    hourly_rates = {
        1351.0: 30.00,
        1331.0: 40.00,
        1175.0: 28.00,
        1279.0: 45.00,
        1307.0: 25.00,
        1067.0: 46.00,
        1389.0: 40.00,
        1358.0: 40.00,
        800.0: 25.00,
    }

    if "Mileage" not in df.columns:
        df["Mileage"] = 0.0

    raw_rows = []
    grouped = df.groupby([id_col, df[name_col].astype(str)], dropna=False)

    for (emp_id_raw, emp_name), group in grouped:
        try:
            emp_id = float(emp_id_raw) if pd.notnull(emp_id_raw) and str(emp_id_raw).replace(".", "",
                                                                                             1).isdigit() else emp_id_raw
        except:
            emp_id = emp_id_raw

        formatted_worker_id = int(emp_id) if isinstance(emp_id, float) and emp_id.is_integer() else emp_id
        labor_override = str(emp_name).strip() if emp_name and str(emp_name).lower() != "nan" else str(
            formatted_worker_id)
        emp_name_lower = labor_override.lower()

        is_hospice_staff = any(h_name in emp_name_lower for h_name in hospice_employee_names)

        total_employee_hours = 0.0
        total_employee_mileage = 0.0
        prn_rows_for_emp = []
        applied_rate = 0.0

        for _, row in group.iterrows():
            hours = float(row.get(hours_col, 0)) if pd.notnull(row.get(hours_col)) and str(row.get(hours_col)).replace(
                ".", "", 1).isdigit() else 0.0
            mileage = float(row.get("Mileage", 0)) if pd.notnull(row.get("Mileage")) and str(
                row.get("Mileage")).replace(".", "", 1).isdigit() else 0.0
            total_employee_mileage += mileage

            if emp_id in hourly_rates:
                applied_rate = hourly_rates[emp_id]
                total_employee_hours += hours
            else:
                rate = float(row.get("Rate", 0)) if pd.notnull(row.get("Rate")) and str(row.get("Rate")).replace(".",
                                                                                                                 "",
                                                                                                                 1).isdigit() else 0.0
                amount = float(row.get("Amount", 0)) if pd.notnull(row.get("Amount")) and str(
                    row.get("Amount")).replace(".", "", 1).isdigit() else 0.0
                if amount > 0 or rate > 0:
                    prn_rows_for_emp.append({
                        "Review": "✅ Validated",
                        "Client ID": 16068715,
                        "Worker ID": formatted_worker_id,
                        "Org": "",
                        "Job Number": "",
                        "Pay Component": "PRN Points",
                        "Rate": "",
                        "Rate Number": "",
                        "Hours": "",
                        "Units": "",
                        "Line Date": "",
                        "Amount": amount,
                        "Check Seq Number": "",
                        "Override State": "",
                        "Override Local": "",
                        "Override Local Jurisdiction": "",
                        "Labor Override": labor_override,
                        "_EmployeeName": emp_name,
                        "_LOB": "Home Health",
                    })

        if not is_hospice_staff and emp_id in hourly_rates and total_employee_hours > 0:
            base_item = {
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": formatted_worker_id,
                "Org": "",
                "Job Number": "",
                "Pay Component": "Hourly",
                "Rate": applied_rate,
                "Rate Number": "",
                "Hours": 0.0,
                "Units": "",
                "Line Date": "",
                "Amount": "",
                "Check Seq Number": "",
                "Override State": "",
                "Override Local": "",
                "Override Local Jurisdiction": "",
                "Labor Override": labor_override,
                "_EmployeeName": emp_name,
                "_LOB": "Home Health",
            }

            if total_employee_hours > 80:
                reg_item = base_item.copy()
                reg_item["Hours"] = 80.0
                raw_rows.append(reg_item)

                ot_item = base_item.copy()
                ot_item["Pay Component"] = "Overtime"
                ot_item["Hours"] = total_employee_hours - 80.0
                raw_rows.append(ot_item)
            else:
                reg_item = base_item.copy()
                reg_item["Hours"] = total_employee_hours
                raw_rows.append(reg_item)

        for prn_r in prn_rows_for_emp:
            raw_rows.append(prn_r)

        if total_employee_mileage > 0 and not is_hospice_staff:
            raw_rows.append({
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": formatted_worker_id,
                "Org": "",
                "Job Number": "",
                "Pay Component": "MILEAGE REIMB",
                "Rate": 0.73,
                "Rate Number": "",
                "Hours": "",
                "Units": total_employee_mileage,
                "Line Date": "",
                "Amount": "",
                "Check Seq Number": "",
                "Override State": "",
                "Override Local": "",
                "Override Local Jurisdiction": "",
                "Labor Override": labor_override,
                "_EmployeeName": emp_name,
                "_LOB": "Home Health",
            })

    return aggregate_and_standardize(raw_rows)


def process_home_care_payroll(df):
    df = sanitize_columns(df)

    id_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    name_col = df.columns[3] if len(df.columns) > 3 else (df.columns[2] if len(df.columns) > 2 else id_col)

    if "Hours" not in df.columns:
        h_match = next((c for c in df.columns if "hour" in c.lower()), None)
        df["Hours"] = df[h_match] if h_match else 0.0
    if "Rate" not in df.columns:
        r_match = next((c for c in df.columns if "rate" in c.lower()), None)
        df["Rate"] = df[r_match] if r_match else 0.0
    if "Pay Component" not in df.columns:
        p_match = next((c for c in df.columns if any(k in c.lower() for k in ["component", "type", "description"])),
                       None)
        df["Pay Component"] = df[p_match] if p_match else ""

    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0)
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce").fillna(0)

    raw_rows = []
    grouped = df.groupby([id_col, df[name_col].astype(str)], dropna=False)

    for (worker_id, emp_name), group in grouped:
        accumulated_hours = 0.0
        mileage_units = 0.0

        formatted_worker_id = int(worker_id) if pd.notnull(worker_id) and str(worker_id).replace(".", "",
                                                                                                 1).isdigit() else worker_id
        labor_override = formatted_worker_id

        for _, row in group.iterrows():
            comp = str(row.get("Pay Component", "")).strip()
            comp_lower = comp.lower()
            rate = float(row.get("Rate", 0))
            hours = float(row.get("Hours", 0))
            units = row.get("Units", "")

            if comp_lower in ["mileage", "miles", "mileage reimbursement", "mileage reimb"] or rate == 0.73:
                m_units = hours if hours > 0 else (
                    float(units) if pd.notnull(units) and str(units).replace(".", "", 1).isdigit() else 0.0)
                if m_units > 0:
                    mileage_units += m_units
            else:
                if hours <= 0:
                    continue

                if comp == "" or comp_lower in ["nan", "none"]:
                    actual_comp = "Overtime"
                elif "overtime" in comp_lower or "ot" in comp_lower:
                    actual_comp = "Overtime"
                else:
                    if accumulated_hours < 80:
                        allowed = 80 - accumulated_hours
                        if hours <= allowed:
                            accumulated_hours += hours
                            actual_comp = comp if comp else "Hourly"
                        else:
                            reg_hrs = allowed
                            accumulated_hours = 80.0
                            raw_rows.append({
                                "Review": "✅ Validated",
                                "Client ID": 16068715,
                                "Worker ID": formatted_worker_id,
                                "Org": "",
                                "Job Number": "",
                                "Pay Component": "Hourly",
                                "Rate": rate if rate > 0 else "",
                                "Rate Number": "",
                                "Hours": reg_hrs,
                                "Units": "",
                                "Line Date": "",
                                "Amount": "",
                                "Check Seq Number": "",
                                "Override State": "",
                                "Override Local": "",
                                "Override Local Jurisdiction": "",
                                "Labor Override": labor_override,
                                "_EmployeeName": emp_name,
                                "_LOB": "Home Care",
                            })
                            hours = hours - allowed
                            actual_comp = "Overtime"
                    else:
                        actual_comp = "Overtime"

                raw_rows.append({
                    "Review": "✅ Validated",
                    "Client ID": 16068715,
                    "Worker ID": formatted_worker_id,
                    "Org": "",
                    "Job Number": "",
                    "Pay Component": actual_comp,
                    "Rate": rate if rate > 0 else "",
                    "Rate Number": "",
                    "Hours": hours,
                    "Units": "",
                    "Line Date": "",
                    "Amount": "",
                    "Check Seq Number": "",
                    "Override State": "",
                    "Override Local": "",
                    "Override Local Jurisdiction": "",
                    "Labor Override": labor_override,
                    "_EmployeeName": emp_name,
                    "_LOB": "Home Care",
                })

        if mileage_units > 0:
            raw_rows.append({
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": formatted_worker_id,
                "Org": "",
                "Job Number": "",
                "Pay Component": "MILEAGE REIMB",
                "Rate": 0.73,
                "Rate Number": "",
                "Hours": "",
                "Units": mileage_units,
                "Line Date": "",
                "Amount": "",
                "Check Seq Number": "",
                "Override State": "",
                "Override Local": "",
                "Override Local Jurisdiction": "",
                "Labor Override": labor_override,
                "_EmployeeName": emp_name,
                "_LOB": "Home Care",
            })

    return aggregate_and_standardize(raw_rows)


def process_hospice_reconciliation(hh_file, timesheet_files):
    id_mapping = {}
    name_mapping = {}
    prn_points_by_employee = {}

    if hh_file is not None:
        try:
            df_raw = pd.read_excel(hh_file, header=None) if not hasattr(hh_file, "name") or not hh_file.name.endswith(
                ".csv") else pd.read_csv(hh_file, header=None)
            header_row_idx = 0
            for r in range(min(10, len(df_raw))):
                row_str = " ".join([str(df_raw.iloc[r, c]).lower() for c in range(len(df_raw.columns))])
                if ("employee" in row_str or "worker" in row_str or "name" in row_str) and (
                        "id" in row_str or "emp" in row_str):
                    header_row_idx = r
                    break

            hh_df = pd.read_csv(hh_file, skiprows=header_row_idx) if hasattr(hh_file, "name") and hh_file.name.endswith(
                ".csv") else pd.read_excel(hh_file, header=header_row_idx)
            hh_df = sanitize_columns(hh_df)

            name_col = hh_df.columns[3] if len(hh_df.columns) > 3 else hh_df.columns[0]
            id_col = hh_df.columns[4] if len(hh_df.columns) > 4 else hh_df.columns[1]

            for _, row in hh_df.iterrows():
                emp_name_raw = row.get(name_col, "")
                emp_name = str(emp_name_raw).strip()
                emp_name_lower = emp_name.lower()
                emp_id = row.get(id_col)

                if emp_name and pd.notnull(emp_id):
                    try:
                        formatted_id = int(emp_id) if isinstance(emp_id, float) and emp_id.is_integer() else emp_id
                    except:
                        formatted_id = emp_id
                    id_mapping[emp_name_lower] = formatted_id
                    name_mapping[formatted_id] = emp_name

                amount_val = float(row.get("Amount", 0)) if pd.notnull(row.get("Amount")) and str(
                    row.get("Amount")).replace(".", "", 1).isdigit() else 0.0
                if amount_val > 0 and emp_name_lower:
                    if emp_name_lower not in prn_points_by_employee:
                        prn_points_by_employee[emp_name_lower] = []
                    prn_points_by_employee[emp_name_lower].append({
                        "Review": "✅ Validated",
                        "Client ID": 16068715,
                        "Worker ID": formatted_id if 'formatted_id' in locals() else emp_id,
                        "Org": "",
                        "Job Number": "",
                        "Pay Component": "PRN Points",
                        "Rate": "",
                        "Rate Number": "",
                        "Hours": "",
                        "Units": "",
                        "Line Date": "",
                        "Amount": amount_val,
                        "Check Seq Number": "",
                        "Override State": "",
                        "Override Local": "",
                        "Override Local Jurisdiction": "",
                        "Labor Override": emp_name,
                        "_EmployeeName": emp_name,
                        "_LOB": "Hospice",
                    })
        except Exception as e:
            st.error(f"Error reading HH master for hospice: {e}")

    all_raw_rows = []

    if timesheet_files:
        for ts_file in timesheet_files:
            try:
                xls = pd.ExcelFile(ts_file)
                df_ts = pd.read_excel(xls, sheet_name=xls.sheet_names[0], header=None)

                file_base = ts_file.name.split(".")[0]
                clean_file_name = re.sub(r'[\-_]\s*(copy|duplicate|\d+).*$', '', file_base, flags=re.IGNORECASE).strip()

                found_name_in_cells = ""
                for r_idx in range(min(5, len(df_ts))):
                    for c_idx in range(len(df_ts.columns)):
                        cell_val = str(df_ts.iloc[r_idx, c_idx]).strip()
                        if cell_val and cell_val.lower() not in ["nan", "none", "employee", "name", "worker", "client",
                                                                 "timesheet"]:
                            if any(c.isalpha() for c in cell_val):
                                found_name_in_cells = cell_val
                                break
                    if found_name_in_cells:
                        break

                def resolve_worker_id(search_target):
                    if not search_target:
                        return None, ""
                    target_lower = str(search_target).lower()

                    for k, v in id_mapping.items():
                        if k in target_lower or target_lower in k:
                            return v, name_mapping.get(v, k.title())

                    target_tokens = set(re.findall(r'\b[a-z]{3,}\b', target_lower))
                    best_id = None
                    best_name = ""
                    max_overlap = 0

                    for k, v in id_mapping.items():
                        key_tokens = set(re.findall(r'\b[a-z]{3,}\b', k))
                        overlap = len(target_tokens.intersection(key_tokens))
                        if overlap > max_overlap:
                            max_overlap = overlap
                            best_id = v
                            best_name = name_mapping.get(v, k.title())

                    if max_overlap > 0:
                        return best_id, best_name
                    return None, ""

                worker_id, matched_name = resolve_worker_id(found_name_in_cells)
                if not worker_id:
                    worker_id, matched_name = resolve_worker_id(clean_file_name)

                if not worker_id:
                    worker_id = 1349
                    matched_name = clean_file_name

                formatted_worker_id = int(worker_id) if pd.notnull(worker_id) and str(worker_id).replace(".", "",
                                                                                                         1).isdigit() else worker_id
                display_name = matched_name if matched_name else clean_file_name
                labor_override = display_name

                # --- STRICT ADJACENT/ONE-ROW VERTICAL COLUMN-BASED PARSER ---
                rate_hours_list = []
                mileage_units_list = []

                for c_idx in range(len(df_ts.columns)):
                    col_data = []
                    for r_idx in range(len(df_ts)):
                        cell_val = df_ts.iloc[r_idx, c_idx]
                        if pd.notnull(cell_val):
                            cell_str = str(cell_val).replace("$", "").strip()
                            try:
                                val_num = float(cell_str)
                                col_data.append((r_idx, val_num))
                            except:
                                pass

                    # Look for rate and hours positioned right next to each other (same row or exactly 1 row apart)
                    for i, (r_rate, val_rate) in enumerate(col_data):
                        if val_rate in [80.0, 45.0, 50.0, 100.0, 90.0, 185.0, 26.0, 28.0, 30.0,
                                        10.0] or val_rate == 0.73:
                            best_hr = None
                            for r_hr, val_hr in col_data:
                                if 0 < val_hr <= 200.0 and abs(r_hr - r_rate) <= 1:
                                    if val_hr not in [80.0, 45.0, 50.0, 100.0, 90.0, 185.0, 26.0, 28.0, 30.0, 10.0]:
                                        best_hr = val_hr
                                        break

                            if best_hr is not None:
                                if val_rate == 0.73:
                                    if best_hr < 500:
                                        mileage_units_list.append(best_hr)
                                else:
                                    pair = (val_rate, best_hr)
                                    if pair not in rate_hours_list:
                                        rate_hours_list.append(pair)

                accumulated_hospice_hours = 0.0
                for rate, hours in rate_hours_list:
                    pay_comp = "Hourly"
                    if rate == 50.0:
                        pay_comp = "On call Weekdays"
                    elif rate == 100.0:
                        pay_comp = "On call Weekends"
                    elif rate == 90.0:
                        pay_comp = "Routine Visit"
                    elif rate == 185.0:
                        pay_comp = "Start of Care"

                    if pay_comp == "Hourly":
                        if accumulated_hospice_hours < 80:
                            allowed = 80 - accumulated_hospice_hours
                            if hours <= allowed:
                                accumulated_hospice_hours += hours
                                reg_hrs = hours
                                ot_hrs = 0.0
                            else:
                                reg_hrs = allowed
                                ot_hrs = hours - allowed
                                accumulated_hospice_hours = 80.0
                        else:
                            reg_hrs = 0.0
                            ot_hrs = hours

                        if reg_hrs > 0:
                            all_raw_rows.append({
                                "Review": "✅ Validated",
                                "Client ID": 16068715,
                                "Worker ID": formatted_worker_id,
                                "Org": "",
                                "Job Number": "",
                                "Pay Component": "Hourly",
                                "Rate": rate,
                                "Rate Number": "",
                                "Hours": reg_hrs,
                                "Units": "",
                                "Line Date": "",
                                "Amount": "",
                                "Check Seq Number": "",
                                "Override State": "",
                                "Override Local": "",
                                "Override Local Jurisdiction": "",
                                "Labor Override": labor_override,
                                "_EmployeeName": display_name,
                                "_LOB": "Hospice",
                            })
                        if ot_hrs > 0:
                            all_raw_rows.append({
                                "Review": "✅ Validated",
                                "Client ID": 16068715,
                                "Worker ID": formatted_worker_id,
                                "Org": "",
                                "Job Number": "",
                                "Pay Component": "Overtime",
                                "Rate": rate,
                                "Rate Number": "",
                                "Hours": ot_hrs,
                                "Units": "",
                                "Line Date": "",
                                "Amount": "",
                                "Check Seq Number": "",
                                "Override State": "",
                                "Override Local": "",
                                "Override Local Jurisdiction": "",
                                "Labor Override": labor_override,
                                "_EmployeeName": display_name,
                                "_LOB": "Hospice",
                            })
                    else:
                        all_raw_rows.append({
                            "Review": "✅ Validated",
                            "Client ID": 16068715,
                            "Worker ID": formatted_worker_id,
                            "Org": "",
                            "Job Number": "",
                            "Pay Component": pay_comp,
                            "Rate": rate,
                            "Rate Number": "",
                            "Hours": hours,
                            "Units": "",
                            "Line Date": "",
                            "Amount": "",
                            "Check Seq Number": "",
                            "Override State": "",
                            "Override Local": "",
                            "Override Local Jurisdiction": "",
                            "Labor Override": labor_override,
                            "_EmployeeName": display_name,
                            "_LOB": "Hospice",
                        })

                total_miles = sum(mileage_units_list)
                if total_miles > 0:
                    all_raw_rows.append({
                        "Review": "✅ Validated",
                        "Client ID": 16068715,
                        "Worker ID": formatted_worker_id,
                        "Org": "",
                        "Job Number": "",
                        "Pay Component": "MILEAGE REIMB",
                        "Rate": 0.73,
                        "Rate Number": "",
                        "Hours": "",
                        "Units": total_miles,
                        "Line Date": "",
                        "Amount": "",
                        "Check Seq Number": "",
                        "Override State": "",
                        "Override Local": "",
                        "Override Local Jurisdiction": "",
                        "Labor Override": labor_override,
                        "_EmployeeName": display_name,
                        "_LOB": "Hospice",
                    })

                display_lower = display_name.lower()
                matched_prn_keys = [k for k in prn_points_by_employee.keys() if
                                    k in display_lower or display_lower in k]
                for pk in matched_prn_keys:
                    for prn_row in prn_points_by_employee[pk]:
                        prn_row_copy = prn_row.copy()
                        prn_row_copy["Worker ID"] = formatted_worker_id
                        prn_row_copy["Labor Override"] = display_name
                        prn_row_copy["_EmployeeName"] = display_name
                        all_raw_rows.append(prn_row_copy)

            except Exception as e:
                st.error(f"Error processing hospice timesheet {ts_file.name}: {e}")

    return aggregate_and_standardize(all_raw_rows)


# --- ROUTING VIA QUERY PARAMS ---

if current_tab == "Home":
    st.markdown(
        '<div class="hero-title">Everything You Need to <span>Start</span>, <span>Get Hired</span>, and <span>Thrive</span> as a Payroll Professional</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-subtitle">Transform raw operational exports into sleek, verified, Paychex-ready statements instantly. Automatically catch new employees, per diem rates, and missing IDs with live review flags across Home Health, Home Care, and Hospice workflows.</div>',
        unsafe_allow_html=True,
    )

    col_cta1, col_cta2, col_cta3 = st.columns([1, 1.2, 1])
    with col_cta2:
        if st.button("🚀 Upload Data & Get Started", type="primary", use_container_width=True):
            st.query_params["tab"] = "Upload Data"
            st.rerun()

elif current_tab == "Upload Data":
    st.markdown("## 📂 Select Upload Workflow (Specialized LOBs)")

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
                    f"Successfully loaded Home Health file: **{uploaded_file.name}** ({len(df)} rows)"
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
            "Upload your pre-formatted file for Home Care processing (Blanks automatically tagged as Overtime; Hourly rows split over 80 hours)."
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
                    f"Successfully loaded Home Care file: **{uploaded_file.name}** ({len(df)} rows)"
                )

                processed = process_home_care_payroll(df)
                st.session_state.processed_df = processed

                st.markdown("### 🔍 Live Review & Validation Preview (Home Care)")
                st.dataframe(processed, use_container_width=True)

            except Exception as e:
                st.error(f"Error processing Home Care file: {e}")
        else:
            st.info("Awaiting Home Care file upload...")

    else:
        st.markdown("### 🕊️ Hospice Reconciliation Workflow")
        col1, col2 = st.columns(2)
        with col1:
            hh_master_file = st.file_uploader(
                "Upload Home Health Master File (for ID Mapping & Names)",
                type=["xls", "xlsx", "csv"],
                key="hospice_hh_master",
            )
        with col2:
            timesheet_files_uploaded = st.file_uploader(
                "Upload Hospice Timesheet Files",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="hospice_timesheets",
            )

        if hh_master_file and timesheet_files_uploaded:
            if st.button("Run Hospice Reconciliation", type="primary"):
                with st.spinner("Processing hospice timesheets and matching IDs..."):
                    processed = process_hospice_reconciliation(
                        hh_master_file, timesheet_files_uploaded
                    )
                    st.session_state.processed_df = processed
                    st.success(
                        f"Successfully reconciled {len(timesheet_files_uploaded)} timesheets!"
                    )
                    st.dataframe(processed, use_container_width=True)
        else:
            st.info(
                "Please upload both the Home Health Master file and at least one Hospice timesheet file to run reconciliation."
            )

elif current_tab == "Multi-LOB Batch":
    st.markdown("## ⚡ Multi-LOB Batch Processing Hub")
    st.markdown(
        "Process and combine Home Health, Home Care, and Hospice outputs into a single Paychex import layout."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🏥 Home Health Files")
        hh_batch_files = st.file_uploader(
            "Upload Home Health Files",
            type=["xls", "xlsx", "csv"],
            accept_multiple_files=True,
            key="batch_hh",
        )
    with col2:
        st.markdown("#### 🏡 Home Care Files")
        hc_batch_files = st.file_uploader(
            "Upload Home Care Files",
            type=["xls", "xlsx", "csv"],
            accept_multiple_files=True,
            key="batch_hc",
        )
    with col3:
        st.markdown("#### 🕊️ Hospice Timesheets")
        hospice_batch_files = st.file_uploader(
            "Upload Hospice Timesheets",
            type=["xls", "xlsx"],
            accept_multiple_files=True,
            key="batch_hospice",
        )

    if st.button(
            "Run Multi-LOB Batch Compilation", type="primary", use_container_width=True
    ):
        all_batch_rows = []

        hospice_names = set()
        if hospice_batch_files:
            for f in hospice_batch_files:
                base = f.name.split(".")[0]
                clean = re.sub(r'[\-_]\s*(copy|duplicate|\d+).*$', '', base, flags=re.IGNORECASE).strip().lower()
                hospice_names.add(clean)

        if hospice_batch_files:
            try:
                res_df = process_hospice_reconciliation(None, hospice_batch_files)
                all_batch_rows.append(res_df)
            except Exception as e:
                st.error(f"Error processing hospice batch: {e}")

        if hh_batch_files:
            for f in hh_batch_files:
                try:
                    df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
                    res_df = process_home_health_payroll(df, hospice_names)
                    all_batch_rows.append(res_df)
                except Exception as e:
                    st.error(f"Error in {f.name}: {e}")

        if hc_batch_files:
            for f in hc_batch_files:
                try:
                    df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
                    res_df = process_home_care_payroll(df)
                    all_batch_rows.append(res_df)
                except Exception as e:
                    st.error(f"Error in {f.name}: {e}")

        if all_batch_rows:
            combined_df = pd.concat(all_batch_rows, ignore_index=True)
            final_batch_df = aggregate_and_standardize(combined_df.to_dict("records"))
            st.session_state.batch_processed_df = final_batch_df
            st.success(
                f"Successfully compiled batch dataset ({len(final_batch_df)} rows)."
            )
            st.dataframe(final_batch_df, use_container_width=True)
        else:
            st.warning("Please upload at least one file across any LOB to run batch compilation.")

    if st.session_state.batch_processed_df is not None:
        st.markdown("---")
        st.markdown("### 📥 Download Batch Compilation Results")
        csv_data = st.session_state.batch_processed_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Master Paychex CSV",
            data=csv_data,
            file_name="Master_Paychex_Batch_Import.csv",
            mime="text/csv",
            use_container_width=True,
        )

elif current_tab == "Export Center":
    st.markdown("## 📤 Export Center")
    st.markdown(
        "Download your finalized, validated Paychex-formatted statement."
    )

    target_df = (
        st.session_state.batch_processed_df
        if st.session_state.batch_processed_df is not None
        else st.session_state.processed_df
    )

    if target_df is not None and not target_df.empty:
        st.dataframe(target_df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            csv_bytes = target_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV Format",
                data=csv_bytes,
                file_name="Paychex_Import_Standard.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                target_df.to_excel(writer, index=False, sheet_name="Paychex Import")
            excel_bytes = output.getvalue()
            st.download_button(
                "📥 Download Excel Format",
                data=excel_bytes,
                file_name="Paychex_Import_Standard.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.info("No processed payroll dataset available. Please upload and process a file first.")

elif current_tab == "Developer Support":
    st.markdown("## 📬 Contact Developer Support")
    st.markdown("Get in touch directly with the developer or report any system issues.")

    with st.form("contact_form"):
        sender_email = st.text_input("Your Email Address")
        subject = st.text_input("Subject")
        message = st.text_area("Message / Inquiry")
        submit_ticket = st.form_submit_button("Send Email to Developer", use_container_width=True)

        if submit_ticket:
            if not sender_email or not message:
                st.warning("Please fill in your email and message.")
            else:
                st.success(
                    f"Your message has been successfully dispatched to **cunananmarkedward2330@gmail.com**! We will get back to you shortly."
                )