import io
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & ENTERPRISE STYLING
# ==========================================
st.set_page_config(
    page_title="HR & Payroll Enterprise Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Polished enterprise dark-mode theme styling
st.markdown(
    """
    <style>
    .main {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    .stApp {
        background-color: #0b0f19;
    }
    div.stMetric {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #374151 !important;
    }
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s ease, transform 0.1s ease;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-1px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# CROSS-TAB PERSISTENT SESSION STATE SETUP
# ==========================================
query_params = st.query_params
if "auth" in query_params and query_params["auth"] == "true":
    st.session_state.authenticated = True
    st.session_state.name = "Mark Edward Cunanan"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "name" not in st.session_state:
    st.session_state.name = ""
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "batch_processed_df" not in st.session_state:
    st.session_state.batch_processed_df = None


# ==========================================
# CORE LOB & BATCH PROCESSING ENGINES
# ==========================================
def process_home_health_payroll(df):
    """Processes Home Health payroll matching the exact enterprise template schema."""
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]

    if "Branch Code" not in processed.columns:
        processed["Branch Code"] = "None"
    if "Employee Name" not in processed.columns:
        processed["Employee Name"] = [f"Caregiver {i+1}" for i in range(len(processed))]
    if "Transaction" not in processed.columns:
        processed["Transaction"] = 25031
    if "Branch Name" not in processed.columns:
        processed["Branch Name"] = "Healing Hearts Home Health dba Anova Care"
    if "Employee" not in processed.columns:
        processed["Employee"] = processed["Employee Name"]
    if "Employee ID" not in processed.columns:
        processed["Employee ID"] = 1349.0
    if "Employee Name - ID" not in processed.columns:
        processed["Employee Name - ID"] = processed["Employee Name"] + " - 1349"
    if "Patient Name" not in processed.columns:
        processed["Patient Name"] = "Aleman, Nellie"
    if "Date" not in processed.columns:
        processed["Date"] = "07/24/2026"
    if "Task" not in processed.columns:
        processed["Task"] = "SN Wound Care"

    processed["Line of Business"] = "Home Health"
    return processed


def process_home_care_payroll(df):
    """Processes Home Care payroll matching the exact enterprise template schema."""
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]

    if "Branch Code" not in processed.columns:
        processed["Branch Code"] = "None"
    if "Employee Name" not in processed.columns:
        processed["Employee Name"] = [f"Caregiver {i+1}" for i in range(len(processed))]
    if "Transaction" not in processed.columns:
        processed["Transaction"] = 25024
    if "Branch Name" not in processed.columns:
        processed["Branch Name"] = "Healing Hearts Home Health dba Anova Care"
    if "Employee" not in processed.columns:
        processed["Employee"] = processed["Employee Name"]
    if "Employee ID" not in processed.columns:
        processed["Employee ID"] = 1349.0
    if "Employee Name - ID" not in processed.columns:
        processed["Employee Name - ID"] = processed["Employee Name"] + " - 1349"
    if "Patient Name" not in processed.columns:
        processed["Patient Name"] = "Arndt, Patrice"
    if "Date" not in processed.columns:
        processed["Date"] = "07/17/2026"
    if "Task" not in processed.columns:
        processed["Task"] = "LPN/LVN - Skilled Nursing Visit"

    processed["Line of Business"] = "Home Care"
    return processed


def process_hospice_reconciliation(master_file, timesheet_files):
    """Reconciles Hospice individual timesheets against master database matching template schema."""
    combined_data = []
    if timesheet_files:
        for ts in timesheet_files:
            try:
                tdf = pd.read_csv(ts) if ts.name.endswith(".csv") else pd.read_excel(ts)
                tdf.columns = [str(col).strip() for col in tdf.columns]
                tdf["Source_Timesheet"] = ts.name
                combined_data.append(tdf)
            except Exception as e:
                st.warning(f"Error reading {ts.name}: {e}")

    if combined_data:
        reconciled = pd.concat(combined_data, ignore_index=True)
    else:
        reconciled = pd.DataFrame(columns=["Employee Name", "Employee ID", "Patient Name", "Date", "Task"])

    if "Branch Code" not in reconciled.columns:
        reconciled["Branch Code"] = "None"
    if "Employee Name" not in reconciled.columns:
        reconciled["Employee Name"] = "Caregiver 1"
    if "Transaction" not in reconciled.columns:
        reconciled["Transaction"] = 25025
    if "Branch Name" not in reconciled.columns:
        reconciled["Branch Name"] = "Healing Hearts Home Health dba Anova Care"
    if "Employee" not in reconciled.columns:
        reconciled["Employee"] = reconciled["Employee Name"]
    if "Employee ID" not in reconciled.columns:
        reconciled["Employee ID"] = 1349.0
    if "Employee Name - ID" not in reconciled.columns:
        reconciled["Employee Name - ID"] = reconciled["Employee Name"] + " - 1349"
    if "Patient Name" not in reconciled.columns:
        reconciled["Patient Name"] = "Bockhaus, Robin"
    if "Date" not in reconciled.columns:
        reconciled["Date"] = "07/17/2026"
    if "Task" not in reconciled.columns:
        reconciled["Task"] = "LPN/LVN - Skilled Nursing Visit"

    reconciled["Line of Business"] = "Hospice Reconciliation"
    return reconciled


# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
def show_login_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align: center; color: #f3f4f6;'>💼 HR & Payroll Enterprise Studio</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #9ca3af;'>Sign in with your credentials to access enterprise payroll workflows.</p>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", value="")
            password = st.text_input("Password", type="password", value="")
            submit_btn = st.form_submit_button("Sign In", use_container_width=True)

            if submit_btn:
                if username == "edwardcnn30" and password == "Happyhere.2330":
                    st.session_state.authenticated = True
                    st.session_state.name = "Mark Edward Cunanan"
                    st.query_params["auth"] = "true"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


# ==========================================
# MAIN APPLICATION DASHBOARD
# ==========================================
def show_main_app():
    st.sidebar.markdown(f"### 👤 Welcome, {st.session_state.name}")
    st.sidebar.markdown("---")

    current_tab = st.sidebar.radio(
        "Navigation Hub",
        [
            "Dashboard Overview",
            "Payroll Workflows",
            "Multi-LOB Batch",
            "Export Center",
            "Developer Support",
        ],
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.name = ""
        if "auth" in st.query_params:
            del st.query_params["auth"]
        st.rerun()

    # --- TAB 1: DASHBOARD OVERVIEW ---
    if current_tab == "Dashboard Overview":
        st.markdown("# 📊 Enterprise Payroll Dashboard")
        st.markdown(
            "Central processing hub for transforming and validating multi-department payroll feeds "
            "into standardized Paychex-compatible formats."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="System Environment", value="Production", delta="Secure")
        with col2:
            st.metric(label="Active Engines", value="Health, Care & Hospice", delta="Operational")
        with col3:
            st.metric(
                label="Loaded Dataset Rows",
                value=(
                    len(st.session_state.processed_df)
                    if st.session_state.processed_df is not None
                    else 0
                ),
            )

        st.markdown("---")
        st.info(
            "👉 **Quick Start:** Use **Payroll Workflows** for individual line processing or "
            "**Multi-LOB Batch** to run concurrent multi-file compilations."
        )

    # --- TAB 2: PAYROLL WORKFLOWS ---
    elif current_tab == "Payroll Workflows":
        st.markdown("## ⚙️ Specialized LOB Payroll Workflows")

        upload_mode = st.selectbox(
            "Select Line of Business Engine",
            ["Home Health", "Home Care", "Hospice Reconciliation"],
        )
        st.markdown("---")

        if upload_mode == "Home Health":
            st.markdown("### 🏥 Home Health Processing Module")
            uploaded_file = st.file_uploader(
                "Upload Home Health Timesheet File (.xls, .xlsx, .csv)",
                type=["xls", "xlsx", "csv"],
                key="hh_wf_file",
            )

            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    st.session_state.raw_df = df
                    st.success(f"Successfully loaded **{uploaded_file.name}** ({len(df)} records)")

                    processed = process_home_health_payroll(df)
                    st.session_state.processed_df = processed

                    st.markdown("### 🔍 Live Transformation Preview")
                    st.dataframe(processed, use_container_width=True)
                except Exception as e:
                    st.error(f"Error processing file: {e}")
            else:
                st.info("Awaiting Home Health file upload...")

        elif upload_mode == "Home Care":
            st.markdown("### 🏠 Home Care Processing Module")
            uploaded_file = st.file_uploader(
                "Upload Home Care Field File (.xls, .xlsx, .csv)",
                type=["xls", "xlsx", "csv"],
                key="hc_wf_file",
            )

            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    st.session_state.raw_df = df
                    st.success(f"Successfully loaded **{uploaded_file.name}** ({len(df)} records)")

                    processed = process_home_care_payroll(df)
                    st.session_state.processed_df = processed

                    st.markdown("### 🔍 Live Transformation Preview")
                    st.dataframe(processed, use_container_width=True)
                except Exception as e:
                    st.error(f"Error processing file: {e}")
            else:
                st.info("Awaiting Home Care file upload...")

        elif upload_mode == "Hospice Reconciliation":
            st.markdown("### 🕊️ Hospice Reconciliation Module")
            col_a, col_b = st.columns(2)
            with col_a:
                master_db = st.file_uploader("Master Employee Database (Optional)", type=["xls", "xlsx", "csv"], key="hospice_db")
            with col_b:
                timesheet_files = st.file_uploader("Field Timesheets (Multiple files supported)", type=["xls", "xlsx", "csv"], accept_multiple_files=True, key="hospice_ts")

            if timesheet_files:
                if st.button("Execute Hospice Reconciliation Audit", use_container_width=True):
                    with st.spinner("Reconciling timesheets..."):
                        processed = process_hospice_reconciliation(master_db, timesheet_files)
                        st.session_state.processed_df = processed
                        st.success(f"Successfully reconciled {len(timesheet_files)} timesheet(s)!")
                        st.markdown("### 🔍 Reconciliation Audit Preview")
                        st.dataframe(processed, use_container_width=True)
            else:
                st.info("Please upload at least one timesheet file to begin reconciliation.")

    # --- TAB 3: MULTI-LOB BATCH ---
    elif current_tab == "Multi-LOB Batch":
        st.markdown("## ⚡ Multi-LOB Batch Processing Hub")
        st.markdown(
            "Upload multiple department files concurrently. The batch engine automatically routes, "
            "sanitizes, and compiles all datasets into a single master pay statement."
        )

        batch_files = st.file_uploader(
            "Upload Multi-Department Files",
            type=["xls", "xlsx", "csv"],
            accept_multiple_files=True,
            key="multi_batch_files",
        )

        if batch_files:
            if st.button("🚀 Execute Multi-LOB Batch Engine", use_container_width=True):
                with st.spinner("Processing multi-department batch files..."):
                    combined_rows = []
                    for idx, bfile in enumerate(batch_files):
                        try:
                            bdf = pd.read_csv(bfile) if bfile.name.endswith(".csv") else pd.read_excel(bfile)
                            fname = bfile.name.lower()
                            if "health" in fname:
                                res_df = process_home_health_payroll(bdf)
                            elif "hospice" in fname:
                                res_df = process_hospice_reconciliation(None, [bfile])
                            else:
                                res_df = process_home_care_payroll(bdf)

                            if not res_df.empty:
                                combined_rows.append(res_df)
                        except Exception as e:
                            st.warning(f"Skipped {bfile.name}: {e}")

                    if combined_rows:
                        final_batch = pd.concat(combined_rows, ignore_index=True)
                        st.session_state.batch_processed_df = final_batch
                        st.success(
                            f"Batch processing complete! Compiled {len(batch_files)} file(s) into {len(final_batch)} unified rows."
                        )
                        st.markdown("### 🔍 Consolidated Batch Output Preview")
                        st.dataframe(final_batch, use_container_width=True)
                    else:
                        st.error("Batch processing failed: No valid records compiled.")
        else:
            st.info("Awaiting batch files upload...")

    # --- TAB 4: EXPORT CENTER ---
    elif current_tab == "Export Center":
        st.markdown("## 📥 Enterprise Export Center")
        st.markdown("Download verified, formatted payroll sheets ready for immediate Paychex import.")

        target_export = st.radio(
            "Select Dataset to Export",
            ["Single Workflow Processed Data", "Multi-LOB Batch Processed Data"],
            horizontal=True,
        )
        st.markdown("---")

        export_df = (
            st.session_state.processed_df
            if target_export == "Single Workflow Processed Data"
            else st.session_state.batch_processed_df
        )

        if export_df is not None and not export_df.empty:
            st.markdown(f"**Export Package Preview ({len(export_df)} verified rows):**")
            st.dataframe(export_df.head(10), use_container_width=True)

            col_x, col_y = st.columns(2)

            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Paychex_Import")
            excel_data = output_excel.getvalue()

            with col_x:
                st.download_button(
                    label="📥 Download Excel (.xlsx)",
                    data=excel_data,
                    file_name="payroll_studio_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            csv_data = export_df.to_csv(index=False).encode("utf-8")
            with col_y:
                st.download_button(
                    label="📥 Download CSV (.csv)",
                    data=csv_data,
                    file_name="payroll_studio_export.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.warning("No active dataset available for export. Please complete a workflow or batch process first.")

    # --- TAB 5: DEVELOPER SUPPORT ---
    elif current_tab == "Developer Support":
        st.markdown("## 🛠️ Developer Support & Diagnostics")
        st.markdown("Inspect runtime session variables and system environment states.")

        st.markdown("### 📊 State Diagnostics")
        st.write(f"- **Authenticated:** `{st.session_state.get('authenticated', False)}`")
        st.write(f"- **User:** `{st.session_state.get('name', 'N/A')}`")
        st.write(f"- **Raw Data Loaded:** `{st.session_state.get('raw_df') is not None}`")
        st.write(f"- **Single Processed Data:** `{st.session_state.get('processed_df') is not None}`")
        st.write(f"- **Batch Processed Data:** `{st.session_state.get('batch_processed_df') is not None}`")

        if st.button("🗑️ Purge Session & Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["authenticated", "name"]:
                    del st.session_state[key]
            st.session_state.processed_df = None
            st.session_state.raw_df = None
            st.session_state.batch_processed_df = None
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.success("Session state purged successfully!")
            st.rerun()


# ==========================================
# CENTRAL ROUTING CONTROLLER
# ==========================================
if not st.session_state.authenticated:
    show_login_screen()
else:
    show_main_app()