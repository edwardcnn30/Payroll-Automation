import pandas as pd
import streamlit as st
import io

# Set page configuration with wide layout
st.set_page_config(
    page_title="Payroll Automation Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling & Theme Matching the Reference UI ---
st.markdown("""
    <style>
        /* Global App Dark Theme Background */
        .stApp {
            background-color: #0b0f19;
            color: #f3f4f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Top Navigation Bar Styling */
        .top-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #0b0f19;
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            position: sticky;
            top: 0;
            z-index: 999;
        }
        .nav-brand {
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.02em;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .nav-links {
            display: flex;
            gap: 1.5rem;
            list-style: none;
            margin: 0;
            padding: 0;
            align-items: center;
        }
        .nav-link {
            color: #9ca3af;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            transition: color 0.2s ease;
        }
        .nav-link:hover, .nav-link.active {
            color: #ffffff;
        }

        /* Hero Banner Container */
        .hero-container {
            text-align: center;
            padding: 3.5rem 1rem 2rem 1rem;
            max-width: 900px;
            margin: 0 auto;
        }
        .hero-title {
            font-size: 3rem;
            font-weight: 900;
            line-height: 1.2;
            color: #ffffff;
            letter-spacing: -0.03em;
            margin-bottom: 1.5rem;
        }
        .hero-title span.orange {
            color: #f97316;
        }
        .hero-title span.yellow {
            color: #eab308;
        }
        .hero-subtitle {
            font-size: 1.1rem;
            color: #9ca3af;
            line-height: 1.6;
            margin-bottom: 2rem;
        }

        /* Glassmorphic Cards */
        .custom-card {
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        /* Action Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
            color: white;
            border-radius: 10px;
            font-weight: 600;
            border: none;
            padding: 0.6rem 1.5rem;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 14px rgba(249, 115, 22, 0.3);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(249, 115, 22, 0.5);
        }

        /* Custom Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(17, 24, 39, 0.6);
            border-radius: 8px;
            color: #9ca3af;
            font-weight: 600;
            padding: 10px 20px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
            color: white !important;
            border: none !important;
        }
    </style>

    <!-- Top Navigation Bar HTML -->
    <div class="top-navbar">
        <a href="#" class="nav-brand">💼 Payroll Studio</a>
        <div class="nav-links">
            <a href="#" class="nav-link active">Home</a>
            <a href="#" class="nav-link">Upload Data</a>
            <a href="#" class="nav-link">Interactive Editor</a>
            <a href="#" class="nav-link">Export Center</a>
            <a href="#" class="nav-link">Developer Support</a>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- CORE BACKEND PROCESSING FUNCTION (UNALTERED LOGIC) ---
def process_raw_payroll(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    client_id = 16068715
    sheet_mapping = {s.strip().upper(): s for s in xls.sheet_names}

    prn_employee_ids = {
        1206, 1349, 1199, 1318, 1414, 1458, 1387, 1466, 1267, 1351,
        1246, 1123, 1159, 910, 1391, 1175, 877, 1242, 1334, 980,
        1096, 1237, 1259, 1294, 1208, 1418, 1207, 1184, 1417, 1428,
        1185, 1308, 1276, 1330, 1268, 1247
    }

    target_sheet = None
    for key, name in sheet_mapping.items():
        if any(k in key for k in ['EXPORT', 'DATA', 'RAW', 'VISIT', 'HOURS', 'MAIN']):
            target_sheet = name
            break

    if not target_sheet:
        target_sheet = xls.sheet_names[0]

    df_raw_check = pd.read_excel(xls, sheet_name=target_sheet, header=None)
    header_row = 0
    for idx, row in df_raw_check.head(15).iterrows():
        row_str = ' '.join(str(v).lower() for v in row.values if pd.notna(v))
        if 'name' in row_str or 'employee' in row_str or 'id' in row_str:
            header_row = idx
            break

    df = pd.read_excel(xls, sheet_name=target_sheet, header=header_row)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]

    id_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ['employee id', 'emp id', 'worker id', 'staff id'])),
        None)
    if not id_col:
        id_col = next((c for c in df.columns if 'id' in c.lower() and not any(ex in c.lower() for ex in
                                                                              ['transaction', 'trans', 'order',
                                                                               'invoice', 'record', 'receipt', 'visit',
                                                                               'client', 'company', 'branch', 'site'])),
                      None)

    exclusion_keywords = ['company', 'client', 'facility', 'business', 'vendor', 'location', 'account', 'branch',
                          'site', 'healing', 'hearts', 'department']
    name_col = next((c for c in df.columns if any(
        k in c.lower() for k in ['employee name', 'worker name', 'staff name', 'full name', 'emp name']) and not any(
        ex in c.lower() for ex in exclusion_keywords)), None)
    if not name_col:
        name_col = next(
            (c for c in df.columns if 'name' in c.lower() and not any(ex in c.lower() for ex in exclusion_keywords)),
            None)

    rate_col = next((c for c in df.columns if 'rate' in c.lower() or 'wage' in c.lower()), None)
    hours_col = next((c for c in df.columns if any(k in c.lower() for k in ['hour', 'hrs', 'misc', 'input'])), None)
    miles_col = next((c for c in df.columns if 'mile' in c.lower() and 'total' not in c.lower()), None)
    type_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ['type', 'component', 'service', 'category', 'pay'])),
        None)

    raw_records = []

    for _, row in df.iterrows():
        emp_id = None
        if id_col and pd.notna(row.get(id_col)):
            try:
                emp_id = int(float(str(row.get(id_col)).strip()))
            except (ValueError, TypeError):
                pass

        if not emp_id:
            continue

        emp_name = ""
        if name_col and pd.notna(row.get(name_col)):
            val = str(row.get(name_col)).strip()
            if val and val.lower() not in ['nan', 'none', ''] and not val.replace('.', '', 1).isdigit():
                if not any(ex in val.lower() for ex in ['healing', 'hearts']):
                    emp_name = val

        if not emp_name:
            for c in df.columns:
                if c == id_col or any(k in c.lower() for k in exclusion_keywords):
                    continue
                val = str(row.get(c, '')).strip()
                if val and val.lower() not in ['nan', 'none', ''] and not val.replace('.', '', 1).isdigit() and len(
                        val) > 2:
                    if not any(ex in val.lower() for ex in ['healing', 'hearts']):
                        emp_name = val
                        break
        if not emp_name:
            continue

        rate_val = 0.0
        if rate_col and pd.notna(row.get(rate_col)):
            try:
                rate_val = float(row.get(rate_col))
            except (ValueError, TypeError):
                rate_val = 0.0

        hours_val = 0.0
        if hours_col and pd.notna(row.get(hours_col)):
            try:
                hours_val = float(row.get(hours_col))
            except (ValueError, TypeError):
                hours_val = 0.0

        miles_val = 0.0
        if miles_col and pd.notna(row.get(miles_col)):
            try:
                miles_val = float(row.get(miles_col))
            except (ValueError, TypeError):
                miles_val = 0.0

        if miles_val > 0:
            raw_records.append({
                'Worker ID': emp_id,
                'Labor Override': emp_name,
                'Pay Component': 'MILEAGE REIMB',
                'Rate': 0.73,
                'Hours': 0.0,
                'Units': miles_val,
                'Amount': 0.0
            })

        if emp_id in prn_employee_ids:
            comp_type = 'PRN Points'
            row_amount = rate_val * hours_val
            row_hours = 0.0
        else:
            comp_type = 'Hourly'
            row_amount = 0.0
            row_hours = hours_val
            if type_col and pd.notna(row.get(type_col)):
                t_val = str(row.get(type_col)).upper()
                if 'PRN' in t_val or 'VISIT' in t_val:
                    comp_type = 'PRN Points'
                    row_amount = rate_val * hours_val
                    row_hours = 0.0
                elif 'PTO' in t_val:
                    comp_type = 'PTO Pay'

        if row_hours > 0 or row_amount > 0:
            raw_records.append({
                'Worker ID': emp_id,
                'Labor Override': emp_name,
                'Pay Component': comp_type,
                'Rate': rate_val,
                'Hours': row_hours,
                'Units': 0.0,
                'Amount': row_amount
            })

    if not raw_records:
        return None

    df_raw = pd.DataFrame(raw_records)

    df_grouped = df_raw.groupby(
        ['Worker ID', 'Labor Override', 'Pay Component'], as_index=False
    ).agg({
        'Rate': 'max',
        'Hours': 'sum',
        'Units': 'sum',
        'Amount': 'sum'
    })

    paychex_rows = []
    for _, row in df_grouped.iterrows():
        comp = row['Pay Component']
        hrs = row['Hours']
        units = row['Units']
        rate = row['Rate']
        amt = row['Amount']

        final_rate = ''
        final_hours = ''
        final_units = ''
        final_amount = ''

        if comp == 'MILEAGE REIMB':
            final_rate = 0.73
            final_units = units if units > 0 else ''
            if not final_units:
                continue
        elif comp == 'PRN Points':
            if amt > 0:
                final_amount = round(amt, 2)
            else:
                continue
        elif comp in ['Hourly', 'PTO Pay']:
            if hrs > 0:
                final_hours = hrs
                final_rate = rate if rate > 0 else ''
            else:
                continue
        else:
            if hrs > 0:
                final_hours = hrs
                final_rate = rate if rate > 0 else ''
            else:
                continue

        combined_labor_override = f"{row['Labor Override']} ({row['Worker ID']})"

        paychex_rows.append({
            'Client ID': client_id,
            'Worker ID': row['Worker ID'],
            'Org': '',
            'Job Number': '',
            'Pay Component': comp,
            'Rate': final_rate,
            'Rate Number': '',
            'Hours': final_hours,
            'Units': final_units,
            'Line Date': '',
            'Amount': final_amount,
            'Check': '',
            'Override State': '',
            'Override Local': '',
            'Override Local Jurisdiction': '',
            'Labor Override': combined_labor_override
        })

    df_paychex = pd.DataFrame(paychex_rows)

    if not df_paychex.empty:
        df_paychex['SortOrder'] = df_paychex['Pay Component'].apply(lambda x: 1 if x == 'MILEAGE REIMB' else 0)
        df_paychex = df_paychex.sort_values(by=['SortOrder', 'Worker ID']).drop(columns=['SortOrder'])

    columns_order = [
        'Client ID', 'Worker ID', 'Org', 'Job Number', 'Pay Component',
        'Rate', 'Rate Number', 'Hours', 'Units', 'Line Date', 'Amount',
        'Check', 'Override State', 'Override Local', 'Override Local Jurisdiction', 'Labor Override'
    ]

    for col in columns_order:
        if col not in df_paychex.columns:
            df_paychex[col] = ''

    return df_paychex[columns_order]


# --- HERO HEADER MATCHING REFERENCE IMAGE ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">
            Everything You Need to <span class="orange">Start</span>, <span class="orange">Get Hired</span>, and <span class="yellow">Thrive</span> as a Payroll Professional
        </h1>
        <p class="hero-subtitle">
            Transform raw operational exports into sleek, verified, Paychex-ready statements instantly. Perform direct live edits and handle custom adjustments seamlessly.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- MAIN INTERACTIVE WORKSPACE TABS ---
tab1, tab2 = st.tabs(["📁 Upload & Transform Data", "✏️ Interactive Editor & Export"])

with tab1:
    st.markdown("""
        <div class="custom-card">
            <h3>Upload Raw Payroll Spreadsheet</h3>
            <p style="color: #9ca3af; font-size: 0.95rem;">Upload your Excel export below (.xls or .xlsx formats supported) to run calculations and PRN allocations automatically.</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Raw Excel Export", type=["xls", "xlsx"], label_visibility="collapsed")

with tab2:
    if 'uploaded_file' in locals() and uploaded_file is not None:
        pass

# Processing logic execution whenever file is active
if uploaded_file is not None:
    with st.spinner("✨ Processing calculations and structuring export..."):
        df_result = process_raw_payroll(uploaded_file)

    if df_result is not None and not df_result.empty:
        st.markdown("""
            <div class="custom-card">
                <h3>✏️ Live Payroll Editor & Verification Table</h3>
                <p style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 1rem;">Directly edit any cell value or add manual email timesheets/mileages below before downloading your final CSV file.</p>
            </div>
        """, unsafe_allow_html=True)

        edited_df = st.data_editor(df_result, num_rows="dynamic", use_container_width=True, key="payroll_editor")

        # Summary Metrics Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; padding: 1rem;">
                    <div style="font-size: 0.8rem; color: #9ca3af; text-transform: uppercase;">Total Entries</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #f97316; margin-top: 0.2rem;">{len(edited_df)}</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            hourly_count = len(edited_df[edited_df['Pay Component'] == 'Hourly'])
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; padding: 1rem;">
                    <div style="font-size: 0.8rem; color: #9ca3af; text-transform: uppercase;">Hourly Entries</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #eab308; margin-top: 0.2rem;">{hourly_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            special_count = len(edited_df[edited_df['Pay Component'].isin(['PRN Points', 'MILEAGE REIMB'])])
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; padding: 1rem;">
                    <div style="font-size: 0.8rem; color: #9ca3af; text-transform: uppercase;">PRN / Mileage</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #60a5fa; margin-top: 0.2rem;">{special_count}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div class="custom-card" style="margin-top: 2rem;">
                <h3>📥 Download Final Import File</h3>
                <p style="color: #9ca3af; font-size: 0.95rem; margin-bottom: 1rem;">Export your verified Paychex CSV file including all your live adjustments and manual inputs.</p>
            </div>
        """, unsafe_allow_html=True)

        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="🚀 Download Paychex-Ready CSV",
            data=csv_data,
            file_name="Paychex_Final_Import.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.error("⚠️ No valid payroll records could be parsed. Please check your source file formatting.")
else:
    st.info("👆 Please upload your payroll spreadsheet file in the **'Upload & Transform Data'** tab above to begin.")