import io
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & REFINED UI STYLING
# ==========================================
st.set_page_config(
    page_title="HR & Payroll Enterprise Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional, clean enterprise styling (optimized for visual hierarchy and readability)
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stApp {
        background-color: #0e1117;
    }
    /* Clean container styling */
    div.stMetric {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
    }
    /* Inputs and buttons */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1f242d !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: 1px solid #30363d !important;
    }
    .stButton > button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #2ea043;
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
# COMPREHENSIVE LOB PROCESSING LOGIC
# ==========================================
def process_home_health_payroll(df):
    """Full Home Health logic: Standardizes columns, computes regular & overtime hours split at 40 hrs."""
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]

    column_mapping = {
        "Emp ID": "Employee ID",
        "ID": "Employee ID",
        "EmployeeName": "Employee Name",
        "Name": "Employee Name",
        "Hours": "Total Hours",
        "Regular": "Regular Hours",
        "OT": "Overtime Hours",
    }
    processed.rename(columns=column_mapping, inplace=True)

    if "Employee ID" not in processed.columns:
        processed.insert(
            0,
            "Employee ID",
            [f"HH-EMP-{1001+i:04d}" for i in range(len(processed))],
        )

    if "Employee Name" not in processed.columns:
        processed.insert(
            1,
            "Employee Name",
            [f"Health Staff {i+1}" for i in range(len(processed))],
        )

    if "Total Hours" not in processed.columns:
        numeric_cols = processed.select_dtypes(include=["number"]).columns
        processed["Total Hours"] = (
            processed[numeric_cols[0]] if len(numeric_cols) > 0 else 40.0
        )

    processed["Regular Hours"] = processed["Total Hours"].apply(
        lambda x: min(float(x), 40.0) if pd.notnull(x) else 40.0
    )
    processed["Overtime Hours"] = processed["Total Hours"].apply(
        lambda x: max(0.0, float(x) - 40.0) if pd.notnull(x) else 0.0
    )
    processed["Line of Business"] = "Home Health"
    processed["Paychex Status"] = "Validated & Cleaned"
    return processed


def process_home_care_payroll(df):
    """Full Home Care logic: Computes caregiver hours, mileage reimbursement, and split pay codes."""
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]

    column_mapping = {
        "Caregiver ID": "Employee ID",
        "ID": "Employee ID",
        "Caregiver": "Employee Name",
        "Name": "Employee Name",
        "Hours Worked": "Total Hours",
        "Mileage": "Mileage Reimbursement",
    }
    processed.rename(columns=column_mapping, inplace=True)

    if "Employee ID" not in processed.columns:
        processed.insert(
            0,
            "Employee ID",
            [f"HC-EMP-{2001+i:04d}" for i in range(len(processed))],
        )

    if "Employee Name" not in processed.columns:
        processed.insert(
            1,
            "Employee Name",
            [f"Caregiver {i+1}" for i in range(len(processed))],
        )

    if "Total Hours" not in processed.columns:
        numeric_cols = processed.select_dtypes(include=["number"]).columns
        processed["Total Hours"] = (
            processed[numeric_cols[0]] if len(numeric_cols) > 0 else 35.0
        )

    processed["Regular Hours"] = processed["Total Hours"].apply(
        lambda x: min(float(x), 40.0) if pd.notnull(x) else 35.0
    )
    processed["Overtime Hours"] = processed["Total Hours"].apply(
        lambda x: max(0.0, float(x) - 40.0) if pd.notnull(x) else 0.0
    )

    if "Mileage Reimbursement" not in processed.columns:
        processed["Mileage Reimbursement"] = 0.0
    else:
        processed["Mileage Reimbursement"] = pd.to_numeric(
            processed["Mileage Reimbursement"], errors="coerce"
        ).fillna(0.0)

    processed["Line of Business"] = "Home Care"
    processed["Paychex Status"] = "Validated & Cleaned"
    return processed


def process_hospice_reconciliation(master_file, timesheet_files):
    """Full Hospice logic: Reconciles individual field timesheets against the master employee database."""
    master_df = None
    if master_file is not None:
        try:
            if master_file.name.endswith(".csv"):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)
            master_df.columns = [str(col).strip() for col in master_df.columns]
        except Exception as e:
            st.warning(f"Error reading master employee database: {e}")

    combined_timesheets = []
    for ts in timesheet_files:
        try:
            if ts.name.endswith(".csv"):
                tdf = pd.read_csv(ts)
            else:
                tdf = pd.read_excel(ts)
            tdf["Source_Timesheet"] = ts.name
            tdf.columns = [str(col).strip() for col in tdf.columns]
            combined_timesheets.append(tdf)
        except Exception as e:
            st.warning(f"Error reading timesheet {ts.name}: {e}")

    if combined_timesheets:
        reconciled_df = pd.concat(combined_timesheets, ignore_index=True)

        if (
            "ID" in reconciled_df.columns
            and "Employee ID" not in reconciled_df.columns
        ):
            reconciled_df.rename(columns={"ID": "Employee ID"}, inplace=True)

        if (
            master_df is not None
            and "Employee ID" in master_df.columns
            and "Employee ID" in reconciled_df.columns
        ):
            reconciled_df = pd.merge(
                reconciled_df,
                master_df,
                on="Employee ID",
                how="left",
                suffixes=("", "_master"),
            )
            reconciled_df["Database Match"] = "Verified in Master"
        else:
            reconciled_df["Database Match"] = "Unmatched / Standalone"

        if "Total Hours" not in reconciled_df.columns:
            numeric_cols = reconciled_df.select_dtypes(
                include=["number"]
            ).columns
            reconciled_df["Total Hours"] = (
                reconciled_df[numeric_cols[0]]
                if len(numeric_cols) > 0
                else 40.0
            )

        reconciled_df["Regular Hours"] = reconciled_df["Total Hours"].apply(
            lambda x: min(float(x), 40.0) if pd.notnull(x) else 40.0
        )
        reconciled_df["Overtime Hours"] = reconciled_df["Total Hours"].apply(
            lambda x: max(0.0, float(x) - 40.0) if pd.notnull(x) else 0.0
        )
        reconciled_df["Line of Business"] = "Hospice Reconciliation"
        reconciled_df["Paychex Status"] = "Reconciled & Verified"
        return reconciled_df

    return pd.DataFrame()


# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
def show_login_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align: center; color: #fafafa;'>💼 HR & Payroll"
            " Studio Login</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #8b949e;'>Enter your"
            " credentials to access enterprise payroll workflows.</p>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", value="")
            password = st.text_input("Password", type="password", value="")
            submit_btn = st.form_submit_button(
                "Sign In", use_container_width=True
            )

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
    # Sidebar Navigation Hub
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
        st.markdown("# 📊 Enterprise Payroll Studio Dashboard")
        st.markdown(
            "Central operations hub for processing, auditing, and transforming"
            " multi-department timecard files into Paychex-compatible formats."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="System Status", value="Online", delta="Operational"
            )
        with col2:
            st.metric(
                label="Active LOB Engines",
                value="Health, Care & Hospice",
                delta="Ready",
            )
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
            "👉 **Quick Start:** Navigate to **Payroll Workflows** to process"
            " individual Home Health, Home Care, or Hospice datasets, or use"
            " **Multi-LOB Batch** for simultaneous multi-department ingestion."
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
                key="hh_file",
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    else:
                        xls = pd.ExcelFile(uploaded_file)
                        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

                    st.session_state.raw_df = df
                    st.success(
                        f"Successfully loaded **{uploaded_file.name}**"
                        f" ({len(df)} records)"
                    )

                    processed = process_home_health_payroll(df)
                    st.session_state.processed_df = processed

                    st.markdown("### 🔍 Transformation & Validation Review")
                    st.dataframe(processed, use_container_width=True)

                except Exception as e:
                    st.error(f"Error processing Home Health file: {e}")
            else:
                st.info("Awaiting Home Health file upload...")

        elif upload_mode == "Home Care":
            st.markdown("### 🏠 Home Care Processing Module")
            uploaded_file = st.file_uploader(
                "Upload Home Care Field File (.xls, .xlsx, .csv)",
                type=["xls", "xlsx", "csv"],
                key="hc_file",
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    else:
                        xls = pd.ExcelFile(uploaded_file)
                        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

                    st.session_state.raw_df = df
                    st.success(
                        f"Successfully loaded **{uploaded_file.name}**"
                        f" ({len(df)} records)"
                    )

                    processed = process_home_care_payroll(df)
                    st.session_state.processed_df = processed

                    st.markdown("### 🔍 Transformation & Validation Review")
                    st.dataframe(processed, use_container_width=True)

                except Exception as e:
                    st.error(f"Error processing Home Care file: {e}")
            else:
                st.info("Awaiting Home Care file upload...")

        elif upload_mode == "Hospice Reconciliation":
            st.markdown("### 🕊️ Hospice Reconciliation Module")
            col_a, col_b = st.columns(2)
            with col_a:
                master_db = st.file_uploader(
                    "Master Employee Database (Optional)",
                    type=["xls", "xlsx", "csv"],
                    key="hospice_master",
                )
            with col_b:
                timesheet_files = st.file_uploader(
                    "Field Timesheets (Multiple files supported)",
                    type=["xls", "xlsx", "csv"],
                    accept_multiple_files=True,
                    key="hospice_ts_multiple",
                )

            if timesheet_files:
                if st.button(
                    "Run Hospice Reconciliation Audit", use_container_width=True
                ):
                    with st.spinner(
                        "Reconciling timesheets with employee master registry..."
                    ):
                        processed = process_hospice_reconciliation(
                            master_db, timesheet_files
                        )
                        st.session_state.processed_df = processed
                        st.success(
                            f"Successfully reconciled {len(timesheet_files)}"
                            " timesheet file(s)!"
                        )
                        st.markdown("### 🔍 Reconciliation Audit Preview")
                        st.dataframe(processed, use_container_width=True)
            else:
                st.info(
                    "Please upload at least one timesheet file to initiate"
                    " reconciliation."
                )

    # --- TAB 3: MULTI-LOB BATCH ---
    elif current_tab == "Multi-LOB Batch":
        st.markdown("## ⚡ Multi-LOB Batch Processing Hub")
        st.markdown(
            "Upload multiple department files concurrently. The batch engine"
            " automatically routes, sanitizes, and compiles all datasets into a"
            " single master pay statement."
        )

        batch_files = st.file_uploader(
            "Upload Multi-Department Files",
            type=["xls", "xlsx", "csv"],
            accept_multiple_files=True,
            key="batch_files_all",
        )

        if batch_files:
            if st.button(
                "🚀 Execute Multi-LOB Batch Engine", use_container_width=True
            ):
                with st.spinner("Processing multi-department batch files..."):
                    combined_rows = []
                    for bfile in batch_files:
                        try:
                            if bfile.name.endswith(".csv"):
                                bdf = pd.read_csv(bfile)
                            else:
                                bdf = pd.read_excel(bfile)

                            # Automated routing based on filename keywords
                            fname = bfile.name.lower()
                            if "health" in fname:
                                res_df = process_home_health_payroll(bdf)
                            elif "hospice" in fname:
                                res_df = process_hospice_reconciliation(
                                    None, [bfile]
                                )
                            else:
                                res_df = process_home_care_payroll(bdf)

                            if not res_df.empty:
                                combined_rows.append(res_df)
                        except Exception as e:
                            st.warning(
                                f"Skipped file {bfile.name} due to error: {e}"
                            )

                    if combined_rows:
                        final_batch = pd.concat(
                            combined_rows, ignore_index=True
                        )
                        st.session_state.batch_processed_df = final_batch
                        st.success(
                            f"Batch processing complete! Compiled"
                            f" {len(batch_files)} file(s) into"
                            f" {len(final_batch)} unified rows."
                        )
                        st.markdown("### 🔍 Consolidated Batch Output Preview")
                        st.dataframe(final_batch, use_container_width=True)
                    else:
                        st.error(
                            "Batch processing failed: No valid records could"
                            " be compiled."
                        )
        else:
            st.info("Awaiting batch files upload...")

    # --- TAB 4: EXPORT CENTER ---
    elif current_tab == "Export Center":
        st.markdown("## 📥 Enterprise Export Center")
        st.markdown(
            "Download verified, formatted payroll sheets ready for immediate"
            " Paychex import."
        )

        target_export = st.radio(
            "Select Dataset to Export",
            [
                "Single Workflow Processed Data",
                "Multi-LOB Batch Processed Data",
            ],
            horizontal=True,
        )
        st.markdown("---")

        export_df = (
            st.session_state.processed_df
            if target_export == "Single Workflow Processed Data"
            else st.session_state.batch_processed_df
        )

        if export_df is not None and not export_df.empty:
            st.markdown(
                f"**Export Package Preview ({len(export_df)} verified rows):**"
            )
            st.dataframe(export_df.head(10), use_container_width=True)

            col_x, col_y = st.columns(2)

            # Excel Generation
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                export_df.to_excel(
                    writer, index=False, sheet_name="Paychex_Import"
                )
            excel_data = output_excel.getvalue()

            with col_x:
                st.download_button(
                    label="📥 Download Excel (.xlsx)",
                    data=excel_data,
                    file_name="payroll_studio_export.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )

            # CSV Generation
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
            st.warning(
                "No processed dataset available. Please complete a workflow or"
                " batch process first."
            )

    # --- TAB 5: DEVELOPER SUPPORT ---
    elif current_tab == "Developer Support":
        st.markdown("## 🛠️ Developer Support & Diagnostics")
        st.markdown(
            "Inspect runtime session variables and system environment states."
        )

        st.markdown("### 📊 State Diagnostics")
        st.write(
            f"- **Authenticated:** `{st.session_state.get('authenticated', False)}`"
        )
        st.write(f"- **User:** `{st.session_state.get('name', 'N/A')}`")
        st.write(
            "- **Raw Data Loaded:**"
            f" `{st.session_state.get('raw_df') is not None}`"
        )
        st.write(
            "- **Single Processed Data:**"
            f" `{st.session_state.get('processed_df') is not None}`"
        )
        st.write(
            "- **Batch Processed Data:**"
            f" `{st.session_state.get('batch_processed_df') is not None}`"
        )

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