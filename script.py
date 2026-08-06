import pandas as pd
import streamlit as st
import io

# Set page configuration
st.set_page_config(
    page_title="Payroll Automation Dashboard",
    page_icon="💼",
    layout="wide"
)


def process_raw_payroll(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    client_id = 16068715
    sheet_mapping = {s.strip().upper(): s for s in xls.sheet_names}

    # Explicit list of PRN Worker IDs
    prn_employee_ids = {
        1206, 1349, 1199, 1318, 1414, 1458, 1387, 1466, 1267, 1351,
        1246, 1123, 1159, 910, 1391, 1175, 877, 1242, 1334, 980,
        1096, 1237, 1259, 1294, 1208, 1418, 1207, 1184, 1417, 1428,
        1185, 1308, 1276, 1330, 1268, 1247
    }

    # Locate the primary raw data export sheet
    target_sheet = None
    for key, name in sheet_mapping.items():
        if any(k in key for k in ['EXPORT', 'DATA', 'RAW', 'VISIT', 'HOURS', 'MAIN']):
            target_sheet = name
            break

    if not target_sheet:
        target_sheet = xls.sheet_names[0]

    # Dynamically find the header row
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

    # Strict Employee ID column matching
    id_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ['employee id', 'emp id', 'worker id', 'staff id'])),
        None)
    if not id_col:
        id_col = next((c for c in df.columns if 'id' in c.lower() and not any(ex in c.lower() for ex in
                                                                              ['transaction', 'trans', 'order',
                                                                               'invoice', 'record', 'receipt', 'visit',
                                                                               'client', 'company', 'branch', 'site'])),
                      None)

    # Strict Employee Name column matching (Excluding branch, facility, healing hearts, company, etc.)
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
        # 1. Extract Employee ID
        emp_id = None
        if id_col and pd.notna(row.get(id_col)):
            try:
                emp_id = int(float(str(row.get(id_col)).strip()))
            except (ValueError, TypeError):
                pass

        if not emp_id:
            continue

        # 2. Extract Employee Name (Strictly avoiding branch/facility names like Healing Hearts)
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

        # 3. Extract Rate
        rate_val = 0.0
        if rate_col and pd.notna(row.get(rate_col)):
            try:
                rate_val = float(row.get(rate_col))
            except (ValueError, TypeError):
                rate_val = 0.0

        # 4. Extract Metrics
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

        # 5. Determine Pay Component Category
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
        st.error("No valid payroll rows were found. Please check your file layout.")
        return None

    df_raw = pd.DataFrame(raw_records)

    # Group and aggregate sums per Worker ID, Labor Override, and Pay Component
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

        # Format Labor Override to display both Employee Name and Employee ID
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

    # Sort so that Hourly & PRN appear first, and Mileage Reimb rows are listed at the bottom
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


# --- Streamlit User Interface ---
st.title("💼 Payroll Automation Dashboard")
st.markdown(
    "Upload your **raw data export file**. Branch names are now excluded, ensuring the Labor Override correctly captures the Employee Name and Employee ID.")

uploaded_file = st.file_uploader("Upload Raw Excel Export (.xls / .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
    with st.spinner("Processing payroll calculations..."):
        df_result = process_raw_payroll(uploaded_file)

    if df_result is not None and not df_result.empty:
        st.success("Payroll successfully transformed into Paychex format!")

        st.markdown("### 📊 Live Preview of Paychex Import Data")
        st.dataframe(df_result, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Line Items", len(df_result))
        col2.metric("Hourly Entries", len(df_result[df_result['Pay Component'] == 'Hourly']))
        col3.metric("PRN / Mileage Entries",
                    len(df_result[df_result['Pay Component'].isin(['PRN Points', 'MILEAGE REIMB'])]))

        st.markdown("---")
        st.header("📥 Download Final Import File")

        csv_data = df_result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Paychex-Ready CSV",
            data=csv_data,
            file_name="Paychex_Final_Import.csv",
            mime="text/csv",
            type="primary"
        )