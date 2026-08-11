import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Payroll Studio Enterprise",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished enterprise look
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & SCHEMAS
# ==========================================
PAYCHEX_COLUMNS = [
    'Review', 'Client ID', 'Worker ID', 'Org', 'Job Number',
    'Pay Component', 'Rate', 'Rate Number', 'Hours', 'Units',
    'Line Date', 'Amount', 'Check Seq Number', 'Override State',
    'Override Local', 'Override Local Jurisdiction', 'Labor Override'
]
DEFAULT_CLIENT_ID = '16068715'

HH_RATES = {
    '1351.0': 30.0, '1351': 30.0,
    '1331.0': 40.0, '1331': 40.0,
    '1175.0': 28.0, '1175': 28.0,
    '1279.0': 45.0, '1279': 45.0,
    '1307.0': 25.0, '1307': 25.0,
    '1067.0': 46.0, '1067': 46.0,
    '1389.0': 40.0, '1389': 40.0,
    '1358.0': 40.0, '1358': 40.0,
    '800.0': 25.0, '800': 25.0
}

HOSPICE_MASTER_MAP = {
    'Maggie Simowski': '2001',
    'Katherine Cecil': '2002',
    'Jenifer Cooper': '2003',
    'Gene Smith': '2004',
    'Brandy Kendle': '2005',
    'Ana Escobar Ortega': '2006',
    'Monica Bullock': '2007'
}

SPECIALIZED_HOSPICE_RATES = {
    'Hourly': 80.0,
    'On call Weekdays': 50.0,
    'On call Weekends': 100.0,
    'Routine Visit': 90.0,
    'Start of Care': 185.0
}

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'users' not in st.session_state:
    st.session_state.users = {
        'edwardcnn30': 'Happyhere.2330'
    }
if 'show_register' not in st.session_state:
    st.session_state.show_register = False


# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
def render_auth_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 💼 Payroll Studio Enterprise")
        st.markdown("Secure Enterprise Gateway & Processing Engine")

        if not st.session_state.show_register:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    if username in st.session_state.users and st.session_state.users[username] == password:
                        st.session_state.authenticated = True
                        st.success("Authentication successful! Loading workspace...")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

            if st.button("Create New Account", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        else:
            with st.form("register_form"):
                st.markdown("#### Register New Account")
                new_user = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Password", type="password")
                reg_submit = st.form_submit_button("Register & Login", use_container_width=True)

                if reg_submit:
                    if new_user and new_pass:
                        st.session_state.users[new_user] = new_pass
                        st.session_state.authenticated = True
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.warning("Please fill in all fields.")

            if st.button("Back to Login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()


if not st.session_state.authenticated:
    render_auth_screen()
    st.stop()


# ==========================================
# PROCESSING ENGINES & AGGREGATION HELPERS
# ==========================================
def build_empty_paychex_df():
    return pd.DataFrame(columns=PAYCHEX_COLUMNS)


def extract_worker_id(row):
    for col in ['Worker ID', 'Employee ID', 'ID', 'EmployeeID', 'WorkerID']:
        if col in row and pd.notna(row[col]):
            val = str(row[col]).strip()
            if val and val.lower() != 'nan':
                return val
    return '1351.0'


def extract_worker_name(row, worker_id):
    for col in ['Worker Name', 'Employee Name', 'Name', 'EmployeeName', 'WorkerName']:
        if col in row and pd.notna(row[col]):
            val = str(row[col]).strip()
            if val and val.lower() != 'nan':
                return val
    return f"Staff Member {worker_id}"


def aggregate_paychex_dataframe(df):
    if df.empty:
        return df

    # Ensure numeric types for aggregation columns
    df['Hours'] = pd.to_numeric(df['Hours'], errors='fill_value').fillna(0.0) if 'Hours' in df.columns else 0.0
    df['Units'] = pd.to_numeric(df['Units'], errors='fill_value').fillna(0.0) if 'Units' in df.columns else 0.0
    df['Amount'] = pd.to_numeric(df['Amount'], errors='fill_value').fillna(0.0) if 'Amount' in df.columns else 0.0
    df['Rate'] = pd.to_numeric(df['Rate'], errors='fill_value').fillna(0.0) if 'Rate' in df.columns else 0.0

    group_cols = ['Client ID', 'Worker ID', 'Org', 'Job Number', 'Pay Component', 'Rate', 'Rate Number', 'Line Date',
                  'Override State', 'Override Local', 'Override Local Jurisdiction', 'Labor Override']
    # Filter group columns to only those present
    group_cols = [c for c in group_cols if c in df.columns]

    aggregated = df.groupby(group_cols, dropna=False).agg({
        'Hours': 'sum',
        'Units': 'sum',
        'Amount': 'sum',
        'Review': 'first',
        'Check Seq Number': 'first'
    }).reset_index()

    # Reorder columns back to standard PAYCHEX_COLUMNS
    for col in PAYCHEX_COLUMNS:
        if col not in aggregated.columns:
            aggregated[col] = ''

    return aggregated[PAYCHEX_COLUMNS]


def process_home_health_payroll(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        raw_rows = []
        for idx, row in df.iterrows():
            worker_id = extract_worker_id(row)
            worker_name = extract_worker_name(row, worker_id)
            hours = float(row.get('Hours', row.get('Total Hours', 40.0)))
            mileage = float(row.get('Mileage', row.get('Miles', 0.0)))

            rate = HH_RATES.get(worker_id, HH_RATES.get(worker_id.split('.')[0], 30.0))
            comp_type = 'Hourly'

            # Check overtime split (>80 hours)
            if hours > 80.0:
                reg_hours = 80.0
                ot_hours = hours - 80.0
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HH', 'Job Number': '100', 'Pay Component': comp_type,
                    'Rate': rate, 'Rate Number': '', 'Hours': reg_hours, 'Units': 0.0,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(reg_hours * rate, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HH', 'Job Number': '100', 'Pay Component': 'Overtime',
                    'Rate': rate * 1.5, 'Rate Number': '', 'Hours': ot_hours, 'Units': 0.0,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(ot_hours * rate * 1.5, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })
            else:
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HH', 'Job Number': '100', 'Pay Component': comp_type,
                    'Rate': rate, 'Rate Number': '', 'Hours': hours, 'Units': 0.0,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(hours * rate, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })

            if mileage > 0:
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HH', 'Job Number': '100', 'Pay Component': 'MILEAGE REIMB',
                    'Rate': 0.73, 'Rate Number': '', 'Hours': 0.0, 'Units': mileage,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(mileage * 0.73, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })

        temp_df = pd.DataFrame(raw_rows, columns=PAYCHEX_COLUMNS)
        return aggregate_paychex_dataframe(temp_df)
    except Exception as e:
        st.error(f"Error processing Home Health file: {e}")
        return build_empty_paychex_df()


def process_home_care_payroll(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        raw_rows = []
        for idx, row in df.iterrows():
            worker_id = extract_worker_id(row)
            worker_name = extract_worker_name(row, worker_id)
            comp = str(row.get('Pay Component', ''))
            hours = float(row.get('Hours', 35.0))
            rate = float(row.get('Rate', 20.0))
            mileage = float(row.get('Mileage', 0.0))

            if pd.isna(comp) or comp == '' or comp.lower() == 'nan' or comp.lower() == 'none':
                comp = 'Overtime'

            raw_rows.append({
                'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                'Org': 'HC', 'Job Number': '200', 'Pay Component': comp,
                'Rate': rate, 'Rate Number': '', 'Hours': hours, 'Units': 0.0,
                'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(hours * rate, 2),
                'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
            })

            if mileage > 0:
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HC', 'Job Number': '200', 'Pay Component': 'MILEAGE REIMB',
                    'Rate': 0.73, 'Rate Number': '', 'Hours': 0.0, 'Units': mileage,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(mileage * 0.73, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })

        temp_df = pd.DataFrame(raw_rows, columns=PAYCHEX_COLUMNS)
        return aggregate_paychex_dataframe(temp_df)
    except Exception as e:
        st.error(f"Error processing Home Care file: {e}")
        return build_empty_paychex_df()


def process_hospice_reconciliation(hh_file, hospice_file):
    try:
        dynamic_map = HOSPICE_MASTER_MAP.copy()
        if hh_file:
            if hh_file.name.endswith('.csv'):
                hh_df = pd.read_csv(hh_file)
            else:
                hh_df = pd.read_excel(hh_file)
            for _, r in hh_df.iterrows():
                wid = extract_worker_id(r)
                wname = extract_worker_name(r, wid)
                if wname and wid:
                    dynamic_map[wname] = wid

        if hospice_file.name.endswith('.csv'):
            h_df = pd.read_csv(hospice_file)
        else:
            h_df = pd.read_excel(hospice_file)

        raw_rows = []
        for idx, row in h_df.iterrows():
            worker_name = str(row.get('Worker Name', row.get('Employee Name', 'Maggie Simowski')))
            worker_id = dynamic_map.get(worker_name, extract_worker_id(row))
            comp_type = str(row.get('Pay Component', 'Routine Visit'))
            rate = SPECIALIZED_HOSPICE_RATES.get(comp_type, 90.0)
            hours = float(row.get('Hours', 4.0))
            mileage = float(row.get('Mileage', 12.0))

            raw_rows.append({
                'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                'Org': 'HOSP', 'Job Number': '300', 'Pay Component': comp_type,
                'Rate': rate, 'Rate Number': '', 'Hours': hours, 'Units': 0.0,
                'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(hours * rate, 2),
                'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
            })

            if mileage > 0:
                raw_rows.append({
                    'Review': '', 'Client ID': DEFAULT_CLIENT_ID, 'Worker ID': worker_id,
                    'Org': 'HOSP', 'Job Number': '300', 'Pay Component': 'MILEAGE REIMB',
                    'Rate': 0.73, 'Rate Number': '', 'Hours': 0.0, 'Units': mileage,
                    'Line Date': datetime.today().strftime('%m/%d/%Y'), 'Amount': round(mileage * 0.73, 2),
                    'Check Seq Number': '', 'Override State': '', 'Override Local': '',
                    'Override Local Jurisdiction': '', 'Labor Override': f"{worker_name} - {worker_id} ({worker_id})"
                })

        temp_df = pd.DataFrame(raw_rows, columns=PAYCHEX_COLUMNS)
        return aggregate_paychex_dataframe(temp_df)
    except Exception as e:
        st.error(f"Error in Hospice Reconciliation: {e}")
        return build_empty_paychex_df()


def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Paychex_Import')
    processed_data = output.getvalue()
    return processed_data


# ==========================================
# NAVIGATION & APP LAYOUT
# ==========================================
st.sidebar.markdown("### 🏢 Payroll Studio Enterprise")
st.sidebar.markdown(f"**Logged in as:** `edwardcnn30`")
st.sidebar.markdown("---")

nav_option = st.sidebar.radio(
    "Navigation Menu",
    [
        "🏠 Home",
        "🏥 Home Health",
        "🏡 Home Care",
        "🕊️ Hospice Reconciliation",
        "⚡ Multi-LOB Batch Upload",
        "📬 Contact Developer"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# 1. HOME DASHBOARD
# ==========================================
if nav_option == "🏠 Home":
    st.title("🏠 Executive Dashboard")
    st.markdown(
        "Welcome to **Payroll Studio Enterprise**, your end-to-end automated LOB processing, data aggregation, and Paychex reconciliation hub.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🏥 Home Health</h4>
            <p>Automated rate mapping, overtime splits & mileage calculation ($0.73 standard).</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🏡 Home Care</h4>
            <p>Flexible schema alignment, blank component detection & 80-hour threshold OT handling.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🕊️ Hospice Reconciliation</h4>
            <p>Master ID mapping with specialized visit and on-call pay rates.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(
        "💡 **Quick Start Guide:** Select a module from the left sidebar to begin processing payroll datasets or use the **Multi-LOB Batch Upload** hub to compile all departments simultaneously with automated summation and worker aggregation.")

# ==========================================
# 2. HOME HEALTH MODULE
# ==========================================
elif nav_option == "🏥 Home Health":
    st.title("🏥 Home Health Payroll Processor")
    st.markdown(
        "Upload your Home Health source file to automatically apply rate classifications, ID mapping, row summation, overtime splits, and mileage reimbursements.")

    hh_file = st.file_uploader("Upload Home Health File (CSV or Excel)", type=["csv", "xlsx", "xls"], key="hh_uploader")

    if hh_file is not None:
        with st.spinner("Processing and aggregating Home Health payroll data..."):
            result_df = process_home_health_payroll(hh_file)
            st.success(f"Successfully processed and aggregated into {len(result_df)} Paychex line items!")

            st.dataframe(result_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv_data, "home_health_paychex.csv", "text/csv",
                                   use_container_width=True)
            with col2:
                excel_data = convert_df_to_excel(result_df)
                st.download_button("📥 Download Excel", excel_data, "home_health_paychex.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

# ==========================================
# 3. HOME CARE MODULE
# ==========================================
elif nav_option == "🏡 Home Care":
    st.title("🏡 Home Care Payroll Processor")
    st.markdown(
        "Upload your Home Care source file for automatic column schema alignment, ID extraction, and aggregated overtime evaluation.")

    hc_file = st.file_uploader("Upload Home Care File (CSV or Excel)", type=["csv", "xlsx", "xls"], key="hc_uploader")

    if hc_file is not None:
        with st.spinner("Processing and aggregating Home Care payroll data..."):
            result_df = process_home_care_payroll(hc_file)
            st.success(f"Successfully processed and aggregated into {len(result_df)} Paychex line items!")

            st.dataframe(result_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv_data, "home_care_paychex.csv", "text/csv",
                                   use_container_width=True)
            with col2:
                excel_data = convert_df_to_excel(result_df)
                st.download_button("📥 Download Excel", excel_data, "home_care_paychex.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

# ==========================================
# 4. HOSPICE RECONCILIATION MODULE
# ==========================================
elif nav_option == "🕊️ Hospice Reconciliation":
    st.title("🕊️ Hospice Reconciliation Hub")
    st.markdown(
        "Upload both the Home Health Master File and Hospice Timesheets to execute comprehensive reconciliation, ID mapping, and metric summation.")

    col1, col2 = st.columns(2)
    with col1:
        hosp_hh_file = st.file_uploader("1️⃣ Home Health Master File", type=["csv", "xlsx", "xls"], key="hosp_hh")
    with col2:
        hosp_timesheet_file = st.file_uploader("2️⃣ Hospice Timesheets", type=["csv", "xlsx", "xls"], key="hosp_ts")

    if hosp_timesheet_file is not None:
        with st.spinner("Executing Hospice reconciliation and specialized rate mapping..."):
            result_df = process_hospice_reconciliation(hosp_hh_file, hosp_timesheet_file)
            st.success(f"Successfully reconciled and aggregated {len(result_df)} Hospice line items!")

            st.dataframe(result_df, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv_data, "hospice_reconciliation_paychex.csv", "text/csv",
                                   use_container_width=True)
            with col_b:
                excel_data = convert_df_to_excel(result_df)
                st.download_button("📥 Download Excel", excel_data, "hospice_reconciliation_paychex.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

# ==========================================
# 5. MULTI-LOB BATCH UPLOAD HUB
# ==========================================
elif nav_option == "⚡ Multi-LOB Batch Upload":
    st.title("⚡ Multi-LOB Batch Processing Hub")
    st.markdown(
        "Compile all department files into a single unified Paychex master output dataset with full worker ID aggregation and metric summation.")

    col1, col2, col3 = st.columns(3)
    with col1:
        batch_hh = st.file_uploader("🏥 Home Health File", type=["csv", "xlsx", "xls"], key="batch_hh_up")
    with col2:
        batch_hc = st.file_uploader("🏡 Home Care File", type=["csv", "xlsx", "xls"], key="batch_hc_up")
    with col3:
        batch_hosp = st.file_uploader("🕊️ Hospice File", type=["csv", "xlsx", "xls"], key="batch_hosp_up")

    if st.button("🚀 Run Multi-LOB Batch Compilation", use_container_width=True):
        if not batch_hh and not batch_hc and not batch_hosp:
            st.warning("Please upload at least one LOB file to compile.")
        else:
            with st.spinner("Processing, compiling and aggregating all LOB files..."):
                dfs_to_concat = []
                if batch_hh:
                    dfs_to_concat.append(process_home_health_payroll(batch_hh))
                if batch_hc:
                    dfs_to_concat.append(process_home_care_payroll(batch_hc))
                if batch_hosp:
                    dfs_to_concat.append(process_hospice_reconciliation(batch_hh, batch_hosp))

                if dfs_to_concat:
                    raw_master = pd.concat(dfs_to_concat, ignore_index=True)
                    final_batch_df = aggregate_paychex_dataframe(raw_master)
                    st.success(
                        f"Batch processing and aggregation complete! Total consolidated records: {len(final_batch_df)}")

                    st.dataframe(final_batch_df, use_container_width=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        csv_data = final_batch_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Master CSV", csv_data, "multi_lob_paychex_master.csv",
                                           "text/csv", use_container_width=True)
                    with c2:
                        excel_data = convert_df_to_excel(final_batch_df)
                        st.download_button("📥 Download Master Excel", excel_data, "multi_lob_paychex_master.xlsx",
                                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True)

# ==========================================
# 6. CONTACT DEVELOPER SECTION
# ==========================================
elif nav_option == "📬 Contact Developer":
    st.title("📬 Contact Support & Engineering")
    st.markdown(
        "Need custom architecture extensions, support, or configuration updates? Get in touch with the lead developer.")

    st.markdown("""
    * **Developer Name:** Edward C. Cunanan (Senior Full-Python & Streamlit Enterprise Architect)
    * **Direct Email:** `cunananmarkedward2330@gmail.com`
    * **GitHub:** `edwardcnn30`
    """)

    st.markdown("---")
    st.markdown("### Send a Message")

    with st.form("contact_form"):
        sender_name = st.text_input("Your Name")
        sender_email = st.text_input("Your Email Address")
        subject = st.text_input("Subject")
        message = st.text_area("Message / Inquiry")
        send_btn = st.form_submit_button("Send Email Dispatch", use_container_width=True)

        if send_btn:
            if sender_name and sender_email and message:
                st.success(
                    f"Message successfully dispatched to cunananmarkedward2330@gmail.com! Thank you, {sender_name}. We will get back to you shortly.")
            else:
                st.warning("Please fill in all required fields before dispatching.")