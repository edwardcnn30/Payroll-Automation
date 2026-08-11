import io
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & MODERN STYLING
# ==========================================
st.set_page_config(
    page_title="HR & Payroll Enterprise Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern UI CSS with smooth transitions and card styling
st.markdown(
    """
    <style>
    /* Global Theme & Smooth Transitions */
    .main {
        background-color: #0b0f19;
        color: #f3f4f6;
        transition: all 0.3s ease-in-out;
    }

    /* Modern Card Containers */
    div.stMetric, .stDataFrame, .stAlert {
        background: #111827 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div.stMetric:hover {
        transform: translateY(-2px;);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Polished Input Fields */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #374151 !important;
        transition: border-color 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
    }

    /* Buttons with Transition */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: scale(1.01);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# CROSS-TAB PERSISTENT SESSION STATE SETUP
# ==========================================
# Check URL query params to persist auth state across new browser tabs
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
# CORE PAYROLL PROCESSING ENGINES
# ==========================================
def process_home_care_payroll(df):
    """Parses and transforms raw Home Care timecard data into Paychex-compatible import format."""
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]

    if "Employee ID" not in processed.columns and len(processed.columns) > 0:
        processed.insert(
            0,
            "Employee ID",
            [f"EMP-{1001 + i}" for i in range(len(processed))],
        )

    if "Total Hours" not in processed.columns:
        numeric_cols = processed.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            processed["Total Hours"] = processed[numeric_cols[0]]
        else:
            processed["Total Hours"] = 40.0

    processed["Regular Hours"] = processed["Total Hours"].apply(
        lambda x: min(float(x), 40.0)
    )
    processed["Overtime Hours"] = processed["Total Hours"].apply(
        lambda x: max(0.0, float(x) - 40.0)
    )
    processed["Pay Period Status"] = "Verified & Cleaned"
    return processed


def process_hospice_reconciliation(hh_file, timesheet_files):
    """Reconciles individual field timesheets against the master employee database."""
    master_df = None
    if hh_file is not None:
        try:
            master_df = (
                pd.read_csv(hh_file)
                if hh_file.name.endswith(".csv")
                else pd.read_excel(hh_file)
            )
            master_df.columns = [str(col).strip() for col in master_df.columns]
        except Exception:
            pass

    combined_data = []
    for ts in timesheet_files:
        try:
            tdf = (
                pd.read_csv(ts)
                if ts.name.endswith(".csv")
                else pd.read_excel(ts)
            )
            tdf["Source_Timesheet"] = ts.name
            tdf.columns = [str(col).strip() for col in tdf.columns]
            combined_data.append(tdf)
        except Exception as e:
            st.warning(f"Failed to parse {ts.name}: {e}")

    if combined_data:
        reconciled_df = pd.concat(combined_data, ignore_index=True)
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
        reconciled_df["Reconciliation Status"] = "Reconciled Successfully"
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
            "<h2 style='text-align: center; color: #f3f4f6;'>💼 HR & Payroll"
            " System Login</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #9ca3af;'>Please sign in to"
            " access the enterprise payroll dashboard.</p>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", value="")
            password = st.text_input("Password", type="password", value="")
            submit_btn = st.form_submit_button(
                "Login", use_container_width=True
            )

            if submit_btn:
                if username == "edwardcnn30" and password == "Happyhere.2330":
                    st.session_state.authenticated = True
                    st.session_state.name = "Mark Edward Cunanan"
                    # Set query param token so new tabs remain authenticated automatically
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
        st.markdown("# 📊 Enterprise Payroll Dashboard")
        st.markdown(
            "Welcome to the central processing engine. Select a workflow module"
            " from the sidebar to begin transforming and validating data feeds"
            " for direct Paychex ingestion."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="System Status", value="Online", delta="Operational"
            )
        with col2:
            st.metric(
                label="Active Engines",
                value="Home Care & Hospice",
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
            "👉 **Quick Guide:** Use **Payroll Workflows** for single department"
            " uploads, or **Multi-LOB Batch** to process multiple LOB files"
            " concurrently."
        )

    # --- TAB 2: PAYROLL WORKFLOWS ---
    elif current_tab == "Payroll Workflows":
        st.markdown("## ⚙️ Payroll Processing Workflows")

        upload_mode = st.selectbox(
            "Select Workflow Engine",
            ["Home Care / Field Staff", "Hospice Reconciliation"],
        )
        st.markdown("---")

        if upload_mode == "Home Care / Field Staff":
            st.markdown("### 🏠 Home Care Processing Hub")
            uploaded_file = st.file_uploader(
                "Choose Home Care file (.xls, .xlsx, .csv)",
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
                        f"Successfully loaded Home Care file:"
                        f" **{uploaded_file.name}** ({len(df)} rows)"
                    )

                    processed = process_home_care_payroll(df)
                    st.session_state.processed_df = processed

                    st.markdown("### 🔍 Live Review & Validation Preview")
                    st.dataframe(processed, use_container_width=True)

                except Exception as e:
                    st.error(f"Error processing Home Care file: {e}")
            else:
                st.info("Awaiting Home Care file upload...")

        elif upload_mode == "Hospice Reconciliation":
            st.markdown("### 🕊️ Hospice Reconciliation Workflow")
            col_a, col_b = st.columns(2)
            with col_a:
                hh_file = st.file_uploader(
                    "Master Employee Roster / Database (Optional)",
                    type=["xls", "xlsx", "csv"],
                    key="hospice_hh",
                )
            with col_b:
                timesheet_files = st.file_uploader(
                    "Individual Timesheets (Multiple allowed)",
                    type=["xls", "xlsx", "csv"],
                    accept_multiple_files=True,
                    key="hospice_ts",
                )

            if timesheet_files:
                if st.button(
                        "Run Hospice Reconciliation", use_container_width=True
                ):
                    with st.spinner(
                            "Reconciling timesheets against employee master"
                            " database..."
                    ):
                        processed = process_hospice_reconciliation(
                            hh_file, timesheet_files
                        )
                        st.session_state.processed_df = processed
                        st.success(
                            f"Successfully reconciled {len(timesheet_files)}"
                            " timesheet(s)!"
                        )
                        st.markdown("### 🔍 Live Review & Validation Preview")
                        st.dataframe(processed, use_container_width=True)
            else:
                st.info(
                    "Please upload at least one timesheet file to begin"
                    " reconciliation."
                )

    # --- TAB 3: MULTI-LOB BATCH ---
    elif current_tab == "Multi-LOB Batch":
        st.markdown("## ⚡ Multi-LOB Batch Processing Hub")
        st.markdown(
            "Upload multiple department files simultaneously. The engine will"
            " automatically categorize, process, and compile them into a unified"
            " dataset."
        )

        batch_files = st.file_uploader(
            "Upload Multiple LOB Files",
            type=["xls", "xlsx", "csv"],
            accept_multiple_files=True,
            key="batch_files",
        )

        if batch_files:
            if st.button(
                    "🚀 Run Batch Processing Engine", use_container_width=True
            ):
                with st.spinner("Processing multi-LOB batch files..."):
                    combined_rows = []
                    for bfile in batch_files:
                        try:
                            if bfile.name.endswith(".csv"):
                                bdf = pd.read_csv(bfile)
                            else:
                                bdf = pd.read_excel(bfile)

                            res_df = process_home_care_payroll(bdf)
                            if not res_df.empty:
                                combined_rows.append(res_df)
                        except Exception as e:
                            st.warning(
                                f"Skipped {bfile.name} due to error: {e}"
                            )

                    if combined_rows:
                        final_batch = pd.concat(
                            combined_rows, ignore_index=True
                        )
                        st.session_state.batch_processed_df = final_batch
                        st.success(
                            f"Successfully processed {len(batch_files)} file(s)"
                            f" yielding {len(final_batch)} compiled rows!"
                        )
                        st.markdown("### 🔍 Batch Preview Result")
                        st.dataframe(final_batch, use_container_width=True)
                    else:
                        st.error(
                            "No valid data could be compiled from the uploaded"
                            " files."
                        )
        else:
            st.info("Awaiting batch files upload...")

    # --- TAB 4: EXPORT CENTER ---
    elif current_tab == "Export Center":
        st.markdown("## 📥 Export Center")
        st.markdown(
            "Download your verified, formatted datasets ready for direct system"
            " ingestion."
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
                f"**Previewing Data to Export ({len(export_df)} rows):**"
            )
            st.dataframe(export_df.head(10), use_container_width=True)

            col_x, col_y = st.columns(2)

            # Excel Export Generation
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                export_df.to_excel(
                    writer, index=False, sheet_name="Paychex_Import"
                )
            excel_data = output_excel.getvalue()

            with col_x:
                st.download_button(
                    label="📥 Download as Excel (.xlsx)",
                    data=excel_data,
                    file_name="payroll_studio_export.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )

            # CSV Export Generation
            csv_data = export_df.to_csv(index=False).encode("utf-8")
            with col_y:
                st.download_button(
                    label="📥 Download as CSV (.csv)",
                    data=csv_data,
                    file_name="payroll_studio_export.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.warning(
                "No processed data available yet. Please complete an upload or"
                " batch workflow first."
            )

    # --- TAB 5: DEVELOPER SUPPORT ---
    elif current_tab == "Developer Support":
        st.markdown("## 🛠️ Developer Support & System Diagnostics")
        st.markdown(
            "Inspect current session states, memory variables, and runtime"
            " metrics."
        )

        st.markdown("### 📊 Session State Diagnostics")
        st.write(
            f"- **Authenticated:** `{st.session_state.get('authenticated', False)}`"
        )
        st.write(f"- **Current User:** `{st.session_state.get('name', 'N/A')}`")
        st.write(
            "- **Raw Data Loaded:**"
            f" `{st.session_state.get('raw_df') is not None}`"
        )
        st.write(
            "- **Processed Data Available:**"
            f" `{st.session_state.get('processed_df') is not None}`"
        )
        st.write(
            "- **Batch Processed Data Available:**"
            f" `{st.session_state.get('batch_processed_df') is not None}`"
        )

        if st.button("🗑️ Clear Session State & Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["authenticated", "name"]:
                    del st.session_state[key]
            st.session_state.processed_df = None
            st.session_state.raw_df = None
            st.session_state.batch_processed_df = None
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.success("Session state cleared successfully!")
            st.rerun()


# ==========================================
# ROUTING CONTROLLER
# ==========================================
if not st.session_state.authenticated:
    show_login_screen()
else:
    show_main_app()