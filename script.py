import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import os

# Page Configuration
st.set_page_config(
    page_title="Payroll Dashboard",
    page_icon="💼",
    layout="wide"
)


# Load Configuration for Authentication
def load_config():
    if os.path.exists("CONFIG.YAML"):
        with open("CONFIG.YAML") as file:
            return yaml.load(file, Loader=SafeLoader)
    return None


config = load_config()

# Initialize Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None


# Authentication Login Screen
def login_screen():
    st.markdown("<h1 style='text-align: center;'>💼 HR & Payroll System Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please sign in to access the payroll dashboard.</p>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if config and "credentials" in config and "usernames" in config["credentials"]:
                    users = config["credentials"]["usernames"]
                    if username in users and users[username]["password"] == password:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["name"] = users[username]["name"]
                        st.success("Login successful! Loading dashboard...")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Configuration error: Invalid CONFIG.YAML structure.")


# Main Payroll Dashboard
def main_dashboard():
    # Sidebar Profile & Navigation
    st.sidebar.title(f"Welcome, {st.session_state['name']}!")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio("Navigation", ["Dashboard Overview", "Payroll Processing", "Reports & Export", "Settings"])

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        st.rerun()

    # Dashboard Overview Tab
    if menu == "Dashboard Overview":
        st.title("📊 Payroll Dashboard Overview")
        st.markdown("Monitor key payroll metrics, employee payouts, and active processing summaries.")

        # Top Metrics Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Payroll", "$145,280.00", "+4.2%")
        col2.metric("Processed Employees", "124", "0")
        col3.metric("Pending Approvals", "3", "-2")
        col4.metric("Active Pay Period", "Aug 01 - Aug 15", "Current")

        st.markdown("---")

        # Quick File Preview Section
        st.subheader("📁 Recent Payroll Files")

        # Check if local files exist and display mock/actual data preview
        if os.path.exists("Paychex_Import_Summary.xlsx"):
            try:
                df_summary = pd.read_excel("Paychex_Import_Summary.xlsx")
                st.write("**Paychex Import Summary Preview:**")
                st.dataframe(df_summary.head(5), use_container_width=True)
            except Exception as e:
                st.info("Upload or place 'Paychex_Import_Summary.xlsx' in the project root to preview.")
        else:
            st.info("No default summary spreadsheet detected. Use the Processing tab to upload files.")

    # Payroll Processing Tab
    elif menu == "Payroll Processing":
        st.title("⚙️ Payroll Data Processing")
        st.markdown("Upload raw payroll files (Excel/CSV) to run calculations and generate summaries.")

        uploaded_file = st.file_uploader("Upload Payroll Source File (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.success(f"Successfully loaded: **{uploaded_file.name}**")
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)

                if st.button("Process Payroll Calculations", type="primary"):
                    with st.spinner("Processing payroll rules and net pay..."):
                        # Placeholder logic for processing script integration
                        st.success("Payroll successfully processed! Processed output ready for download.")

                        # Save mock processed file for download
                        output_filename = "Processed_HH_Payroll.xlsx"
                        df.to_excel(output_filename, index=False)

                        with open(output_filename, "rb") as f:
                            st.download_button(
                                label="Download Processed Payroll Report",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Reports & Export Tab
    elif menu == "Reports & Export":
        st.title("📈 Reports & Export Center")
        st.markdown("Generate and download comprehensive organizational payroll reports.")

        report_type = st.selectbox("Select Report Type",
                                   ["Summary Payroll Register", "Tax Deduction Report", "BPO Client Billing Summary"])

        if st.button("Generate Report"):
            st.info(f"Generating {report_type}...")
            st.success("Report ready!")
            st.download_button("Download Report (Excel)", data=b"Mock excel data",
                               file_name=f"{report_type.replace(' ', '_')}.xlsx")

    # Settings Tab
    elif menu == "Settings":
        st.title("🛠️ System Settings")
        st.markdown("Manage application preferences and user profiles.")
        st.text_input("Company Name", value="BPO Payroll Solutions Inc.")
        st.text_input("Default Tax Rate (%)", value="15.0")
        st.button("Save Changes")


# Control Flow based on Authentication State
if not st.session_state["authenticated"]:
    login_screen()
else:
    main_dashboard()