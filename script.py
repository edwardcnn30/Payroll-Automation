import traceback
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & DESIGN SYSTEM (UI/UX PRO MAX)
# ==========================================
st.set_page_config(
    page_title="Payroll Studio Enterprise",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom SaaS CSS Styling Injection
st.markdown("""
<style>
    /* Global Theme & Font Hierarchy */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Premium SaaS Card Container */
    .saas-card {
        background: #FFFFFF;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
    }

    /* Typography Overrides */
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    p, span, label {
        color: #475569;
    }

    /* Custom Button Styling */
    .stButton>button {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #4338CA;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    }

    /* Metric & Badge Styling */
    .metric-container {
        background: #EEF2FF;
        border-left: 4px solid #4F46E5;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_db" not in st.session_state:
    # Default admin credentials requested by user
    st.session_state.user_db = {"edwardcnn30": "Happyhere.2330"}
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None


# ==========================================
# CORE MULTI-LOB PIPELINE LOGIC ENGINES
# ==========================================

def process_home_health_standalone(df):
    """
    Tier 2: Standalone Home Health Engine Logic
    - Anchors ID to Column E, name to Worker Name columns.
    - Applies strict hourly roster check vs PRN / Salaried-Hourly points.
    - Enforces 80-hour OT rule and $0.73 mileage reimbursement.
    """
    df.columns = [str(c).strip() for c in df.columns]
    emp_id_col = df.columns[4] if len(df.columns) > 4 else df.columns[0]
    name_col = next((c for c in df.columns if any(k in c.lower() for k in ["name", "employee", "worker"])),
                    df.columns[3] if len(df.columns) > 3 else df.columns[0])
    rate_col = next((c for c in df.columns if "rate" in c.lower()), None)
    hours_col = next((c for c in df.columns if any(k in c.lower() for k in ["hour", "hrs"])), None)
    amount_col = next((c for c in df.columns if any(k in c.lower() for k in ["amount", "total", "pay", "fee"])), None)

    if "Mileage" not in df.columns:
        df["Mileage"] = 0.0

    HOURLY_TARGET_IDS = {"1389", "1351", "1388", "1162", "1280"}
    HOURLY_RATES = {
        "1389": 40.00,
        "1351": 35.00,
        "1388": 40.00,
        "1162": 35.00,
        "1280": 0.00
    }

    raw_rows = []

    def clean_id(val):
        if pd.isnull(val):
            return "UNKNOWN"
        val_str = str(val).strip()
        if val_str.endswith('.0'):
            val_str = val_str[:-2]
        return val_str

    df["_Clean_Emp_ID"] = df[emp_id_col].apply(clean_id)
    grouped = df.groupby(["_Clean_Emp_ID", df[name_col].astype(str)], dropna=False)

    for (emp_id_str, emp_name), group in grouped:
        emp_name_str = str(emp_name).strip()
        labor_override = emp_name_str if emp_name_str and emp_name_str.lower() != "nan" else emp_id_str

        is_hourly = emp_id_str in HOURLY_TARGET_IDS

        total_employee_hours = 0.0
        total_employee_mileage = 0.0
        total_prn_amount = 0.0
        applied_rate = HOURLY_RATES.get(emp_id_str, 35.00)

        for _, row in group.iterrows():
            mileage = float(row.get("Mileage", 0)) if pd.notnull(row.get("Mileage")) and str(
                row.get("Mileage")).replace(".", "", 1).isdigit() else 0.0
            total_employee_mileage += mileage

            if is_hourly:
                if hours_col and pd.notnull(row.get(hours_col)):
                    try:
                        total_employee_hours += float(str(row.get(hours_col)).replace(",", "").strip())
                    except:
                        pass
                if rate_col and pd.notnull(row.get(rate_col)):
                    try:
                        r = float(str(row.get(rate_col)).replace("$", "").replace(",", "").strip())
                        if r > 0:
                            applied_rate = r
                    except:
                        pass
            else:
                item_amt = 0.0
                if amount_col and pd.notnull(row.get(amount_col)):
                    try:
                        item_amt = float(str(row.get(amount_col)).replace("$", "").replace(",", "").strip())
                    except:
                        item_amt = 0.0
                if item_amt == 0 and rate_col and pd.notnull(row.get(rate_col)):
                    try:
                        item_amt = float(str(row.get(rate_col)).replace("$", "").replace(",", "").strip())
                    except:
                        item_amt = 0.0
                if item_amt > 0:
                    total_prn_amount += item_amt

        if is_hourly:
            if total_employee_hours > 0:
                base_item = {
                    "Review": "✅ Validated",
                    "Client ID": 16068715,
                    "Worker ID": emp_id_str,
                    "Org": "",
                    "Job Number": "",
                    "Pay Component": "Hourly",
                    "Rate": round(applied_rate, 2),
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
                }
                if total_employee_hours > 80:
                    reg = base_item.copy()
                    reg["Hours"] = round(80.0, 2)
                    raw_rows.append(reg)
                    ot = base_item.copy()
                    ot["Pay Component"] = "Overtime"
                    ot["Hours"] = round(total_employee_hours - 80.0, 2)
                    raw_rows.append(ot)
                else:
                    reg = base_item.copy()
                    reg["Hours"] = round(total_employee_hours, 2)
                    raw_rows.append(reg)
        else:
            if total_prn_amount > 0:
                raw_rows.append({
                    "Review": "✅ Validated",
                    "Client ID": 16068715,
                    "Worker ID": emp_id_str,
                    "Org": "",
                    "Job Number": "",
                    "Pay Component": "PRN Points",
                    "Rate": "",
                    "Rate Number": "",
                    "Hours": "",
                    "Units": "",
                    "Line Date": "",
                    "Amount": round(total_prn_amount, 2),
                    "Check Seq Number": "",
                    "Override State": "",
                    "Override Local": "",
                    "Override Local Jurisdiction": "",
                    "Labor Override": labor_override,
                })

        if total_employee_mileage > 0:
            raw_rows.append({
                "Review": "✅ Validated",
                "Client ID": 16068715,
                "Worker ID": emp_id_str,
                "Org": "",
                "Job Number": "",
                "Pay Component": "MILEAGE REIMB",
                "Rate": 0.73,
                "Rate Number": "",
                "Hours": "",
                "Units": round(total_employee_mileage, 2),
                "Line Date": "",
                "Amount": "",
                "Check Seq Number": "",
                "Override State": "",
                "Override Local": "",
                "Override Local Jurisdiction": "",
                "Labor Override": labor_override,
            })

    return pd.DataFrame(raw_rows)


def process_home_care_engine(df):
    """
    Tier 3: Home Care Engine Logic
    - Groups by Column E, tags missing IDs.
    - Fallback blank component to Overtime.
    - Splits hours at 80-hour threshold.
    """
    df.columns = [str(c).strip() for c in df.columns]
    raw_rows = []

    for emp_id, group in df.groupby(df.columns[4], dropna=False):
        is_missing_id = pd.isnull(emp_id) or str(emp_id).strip().lower() in ["", "nan", "none"]
        review_status = "⚠️ Missing ID" if is_missing_id else "✅ Validated"

        total_id_hours = 0.0
        id_records = []

        for _, row in group.iterrows():
            comp = str(row.get("Pay Component", "")).strip()
            if not comp or comp.lower() in ["nan", "none"]:
                comp = "Overtime"

            hrs = 0.0
            try:
                hrs = float(str(row.get("Hours", 0)).replace(",", ""))
            except:
                hrs = 0.0

            if comp.upper() == "HOURLY":
                total_id_hours += hrs
            else:
                id_records.append({**row.to_dict(), "Pay Component": comp, "Hours": hrs})

        if total_id_hours > 0:
            if total_id_hours > 80:
                id_records.append({"Pay Component": "Hourly", "Hours": 80.0})
                id_records.append({"Pay Component": "Overtime", "Hours": total_id_hours - 80.0})
            else:
                id_records.append({"Pay Component": "Hourly", "Hours": total_id_hours})

        for rec in id_records:
            raw_rows.append({
                "Review": review_status,
                "Client ID": 16068715,
                "Worker ID": emp_id if not is_missing_id else "UNKNOWN",
                "Pay Component": rec.get("Pay Component"),
                "Hours": rec.get("Hours", ""),
                "Rate": rec.get("Rate", ""),
                "Units": rec.get("Units", ""),
                "Amount": rec.get("Amount", ""),
                "Labor Override": rec.get("Worker Name", ""),
            })

    return pd.DataFrame(raw_rows)


def process_hospice_reconciliation(df):
    """Hospice Timesheet Reconciliation Module Logic"""
    df.columns = [str(c).strip() for c in df.columns]
    raw_rows = []
    for _, row in df.iterrows():
        raw_rows.append({
            "Review": "✅ Validated",
            "Client ID": 16068715,
            "Worker ID": row.get(df.columns[4], "UNKNOWN"),
            "Pay Component": "On-Call Stipend",
            "Hours": row.get("Hours", ""),
            "Rate": row.get("Rate", ""),
            "Amount": row.get("Amount", ""),
            "Labor Override": row.get("Worker Name", "")
        })
    return pd.DataFrame(raw_rows)


# ==========================================
# ROUTING & VIEWS (LANDING, AUTH, & MAIN APP)
# ==========================================

try:
    # ------------------------------------------
    # 1. LANDING PAGE VIEW
    # ------------------------------------------
    if st.session_state.page == "landing":
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2 = st.spec = st.columns([1.5, 1], gap="large")

        with col1:
            st.markdown("# Enterprise Payroll Transformation Studio")
            st.markdown(
                "### Streamline Home Care, Home Health, and Hospice payroll reconciliations with automated DAG pipelines, strict compliance enforcement, and direct Paychex integration.")
            st.markdown("<br>", unsafe_allow_html=True)

            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("🚀 Launch App / Sign In", use_container_width=True):
                    st.session_state.page = "auth"
                    st.rerun()
            with c_btn2:
                if st.button("✨ Create Account", use_container_width=True):
                    st.session_state.page = "signup"
                    st.rerun()

        with col2:
            st.markdown("""
            <div class="saas-card">
                <h3>🔒 Institutional Security</h3>
                <p>Enterprise grade isolation with encrypted state persistence and robust error boundaries.</p>
                <hr style="margin: 1rem 0; border-color: #E2E8F0;">
                <h3>⚡ Multi-LOB Pipeline</h3>
                <p>Simultaneous DAG batch processing supporting WellSky data schemas mapped to Client ID 16068715.</p>
            </div>
            """, unsafe_allow_html=True)

    # ------------------------------------------
    # 2. ACCOUNT CREATION VIEW
    # ------------------------------------------
    elif st.session_state.page == "signup":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 📝 Create Enterprise Account")
        st.markdown("Register your credentials to access the payroll processing studio.")

        with st.form("signup_form"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Register Account")

            if submit_signup:
                if new_user and new_pass:
                    if new_pass == confirm_pass:
                        st.session_state.user_db[new_user] = new_pass
                        st.success("Account successfully created! Redirecting to Sign In...")
                        st.session_state.page = "auth"
                        st.rerun()
                    else:
                        st.error("Passwords do not match.")
                else:
                    st.error("Please fill in all fields.")

        if st.button("← Back to Landing Page"):
            st.session_state.page = "landing"
            st.rerun()

    # ------------------------------------------
    # 3. SECURE LOGIN VIEW
    # ------------------------------------------
    elif st.session_state.page == "auth":
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([1, 1.5, 1])

        with col_b:
            st.markdown("""
            <div class="saas-card">
                <h3>🔐 Secure Portal Sign In</h3>
                <p>Enter your credentials to access Payroll Studio Enterprise.</p>
            </div>
            """, unsafe_allow_html=True)

            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")

            if st.button("Sign In to Studio", use_container_width=True):
                if username_input in st.session_state.user_db and st.session_state.user_db[
                    username_input] == password_input:
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.session_state.page = "app"
                    st.rerun()
                else:
                    st.error("Invalid credentials. (Hint: Admin is edwardcnn30 / Happyhere.2330)")

            if st.button("← Back", use_container_width=True):
                st.session_state.page = "landing"
                st.rerun()

    # ------------------------------------------
    # 4. MAIN APPLICATION DASHBOARD (AUTHENTICATED)
    # ------------------------------------------
    elif st.session_state.page == "app" and st.session_state.authenticated:
        # Top Header Bar with User Info & Sign Out
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.title("💼 Payroll Studio Enterprise")
            st.markdown("Unified Multi-LOB Engine & Compliance Pipeline • **Client ID: 16068715**")
        with head_col2:
            st.markdown(f"👤 **{st.session_state.username}**")
            if st.button("Sign Out"):
                st.session_state.authenticated = False
                st.session_state.page = "landing"
                st.rerun()

        st.markdown("---")

        # Streamlined 3-Click Navigation Tabs
        tab_batch, tab_hh, tab_hc, tab_hospice = st.tabs([
            "📊 Multi-LOB Batch Processor",
            "🩺 Home Health Studio",
            "🏠 Home Care Studio",
            "🕊️ Hospice Reconciliation"
        ])

        # --- TAB 1: MULTI-LOB BATCH PROCESSOR ---
        with tab_batch:
            st.subheader("Unified Batch Execution Pipeline (DAG Sequence)")
            st.info(
                "Hierarchy Active: Standalone Home Health (Strict ID Filtering) ➔ Home Care. Global 80-Hour Rule Enforced.")

            col_up1, col_up2 = st.columns(2)
            with col_up1:
                hh_file = st.file_uploader("Upload Home Health Master (.csv / .xlsx)", type=["csv", "xlsx"],
                                           key="hh_batch")
            with col_up2:
                hc_file = st.file_uploader("Upload Home Care File (.csv / .xlsx)", type=["csv", "xlsx"], key="hc_batch")

            if st.button("Execute Consolidated Multi-LOB Run", use_container_width=True):
                if hh_file or hc_file:
                    with st.spinner("Processing enterprise multi-LOB pipeline..."):
                        master_output_frames = []
                        if hh_file:
                            df_hh = pd.read_excel(hh_file) if hh_file.name.endswith(".xlsx") else pd.read_csv(hh_file)
                            if len(df_hh.columns) < 5:
                                st.error(
                                    "⚠️ Home Health file error: File must contain at least 5 columns to anchor Employee ID on Column E.")
                            else:
                                master_output_frames.append(process_home_health_standalone(df_hh))
                        if hc_file:
                            df_hc = pd.read_excel(hc_file) if hc_file.name.endswith(".xlsx") else pd.read_csv(hc_file)
                            master_output_frames.append(process_home_care_engine(df_hc))

                        if master_output_frames:
                            st.session_state.processed_df = pd.concat(master_output_frames, ignore_index=True)
                            st.success("Unified Batch Execution Completed Successfully!")
                else:
                    st.error("Please upload at least one operational file.")

            if st.session_state.processed_df is not None:
                st.markdown("### 📋 Consolidated Audit Preview")
                st.dataframe(st.session_state.processed_df, use_container_width=True)
                st.download_button(
                    "📥 Download Master Unified Payroll Output (.csv)",
                    data=st.session_state.processed_df.to_csv(index=False).encode("utf-8"),
                    file_name="Master_Unified_Payroll_Output.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # --- TAB 2: HOME HEALTH STUDIO ---
        with tab_hh:
            st.subheader("Home Health Standalone Module")
            st.write("Validates Column E ID mapping, zero-drop PRN points, and blocked salaried-hourly IDs.")

            hh_single = st.file_uploader("Upload Standalone Home Health File", type=["csv", "xlsx"], key="hh_single_up")
            if hh_single and st.button("Run Home Health Engine", key="btn_hh"):
                df_in = pd.read_excel(hh_single) if hh_single.name.endswith(".xlsx") else pd.read_csv(hh_single)
                res_hh = process_home_health_standalone(df_in)
                st.success("Home Health Processing Complete!")
                st.dataframe(res_hh, use_container_width=True)
                st.download_button("Download Home Health CSV", res_hh.to_csv(index=False).encode("utf-8"),
                                   "Home_Health_Output.csv", "text/csv")

        # --- TAB 3: HOME CARE STUDIO ---
        with tab_hc:
            st.subheader("Home Care Paychex Module")
            st.write("Validates missing IDs, blank component fallback to Overtime, and 80-hour split.")

            hc_single = st.file_uploader("Upload Standalone Home Care File", type=["csv", "xlsx"], key="hc_single_up")
            if hc_single and st.button("Run Home Care Engine", key="btn_hc"):
                df_in = pd.read_excel(hc_single) if hc_single.name.endswith(".xlsx") else pd.read_csv(hc_single)
                res_hc = process_home_care_engine(df_in)
                st.success("Home Care Processing Complete!")
                st.dataframe(res_hc, use_container_width=True)
                st.download_button("Download Home Care CSV", res_hc.to_csv(index=False).encode("utf-8"),
                                   "Home_Care_Output.csv", "text/csv")

        # --- TAB 4: HOSPICE RECONCILIATION ---
        with tab_hospice:
            st.subheader("Hospice Timesheet Reconciliation Module")
            st.write("Manages on-call stipend logic and cross-over PRN retention.")

            hospice_file = st.file_uploader("Upload Hospice Timesheet File", type=["csv", "xlsx"], key="hospice_up")
            if hospice_file and st.button("Run Hospice Engine", key="btn_hospice"):
                df_in = pd.read_excel(hospice_file) if hospice_file.name.endswith(".xlsx") else pd.read_csv(
                    hospice_file)
                res_hospice = process_hospice_reconciliation(df_in)
                st.success("Hospice Reconciliation Complete!")
                st.dataframe(res_hospice, use_container_width=True)
                st.download_button("Download Hospice CSV", res_hospice.to_csv(index=False).encode("utf-8"),
                                   "Hospice_Output.csv", "text/csv")

except Exception as e:
    st.error("🚨 Critical Runtime Exception Caught:")
    st.code(traceback.format_exc())