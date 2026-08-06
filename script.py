import streamlit as st
import pandas as pd
import openpyxl
import re

# Page Configuration & Modern Styling
st.set_page_config(
    page_title="Payroll & Email Automation Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a sleek, modern UI
st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
        }
        .hero-banner {
            padding: 2.2rem 2rem;
            background: linear-gradient(135deg, #1f4068 0%, #162447 50%, #1b1b2f 100%);
            border-radius: 16px;
            color: #ffffff;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .hero-banner h1 {
            font-size: 2.3rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .hero-banner p {
            font-size: 1.05rem;
            color: #a0aec0;
            margin-bottom: 0;
        }
        .custom-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .metric-pill {
            display: inline-block;
            background: rgba(49, 130, 206, 0.2);
            color: #63b3ed;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            border: 1px solid rgba(99, 179, 237, 0.3);
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: NAVIGATION & CONTACT ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/payroll.png", width=110)
    st.markdown("### ⚙️ Hub Controls")
    st.write("Manage payroll periods, correct item values, and export clean Paychex templates.")

    st.markdown("---")
    st.markdown("### 📬 Developer Contact")
    st.write("Need workflow tweaks or custom mapping rules?")

    # Direct Email Button linking to your email address
    st.markdown(
        """
        <a href="mailto:cunananmarkedward2330@gmail.com" target="_blank">
            <button style="
                width: 100%;
                background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
                color: white;
                border: none;
                padding: 0.75rem 1rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
                transition: all 0.3s ease;
            ">
                ✉️ Email Developer
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        "<br><p style='font-size:0.8rem; color: #718096; text-align:center;'>Mark Edward Cunanan<br>© 2026 Payroll Automation Hub</p>",
        unsafe_allow_html=True)

# --- HERO HEADER ---
st.markdown("""
    <div class="hero-banner">
        <h1>⚡ Payroll & Email Automation Hub</h1>
        <p>Process raw payroll sheets, verify or correct item values interactively, and export standard Paychex import templates seamlessly.</p>
    </div>
""", unsafe_allow_html=True)

# Tabs separating the Payroll Dashboard and Multi-Excel Converter
tab1, tab2 = st.tabs(["📊 Payroll Dashboard & Value Correction", "📥 Multi-Excel Paychex Converter"])

# ==========================================
# TAB 1: PAYROLL DASHBOARD & VALUE CORRECTION
# ==========================================
with tab1:
    st.markdown("""
        <div class="custom-card">
            <h3>📊 Raw Payroll Processing & Item Correction</h3>
            <p>Upload your raw payroll spreadsheet below. The system will load the values, allowing you to review and <strong>interactively correct any item or value</strong> before generating the final Paychex template.</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_payroll = st.file_uploader("Upload Raw Payroll Excel File", type=["xlsx", "xls"],
                                        key="raw_payroll_uploader")

    if uploaded_payroll is not None:
        try:
            df_raw = pd.read_excel(uploaded_payroll)
            st.success("✅ Payroll file successfully loaded into the dashboard!")

            st.markdown("#### ✏️ Review & Correct Payroll Items Below")
            st.write(
                "Double-click any cell in the table below to edit, correct values, or adjust entries prior to export.")

            # Interactive data editor allowing the user to correct any item value directly
            df_corrected = st.data_editor(df_raw, num_rows="dynamic", use_container_width=True, key="payroll_editor")

            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(
                    "💡 Once you have verified and corrected all items, click the button to generate and download your clean template.")
            with col2:
                csv_processed = df_corrected.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Corrected Paychex Report",
                    data=csv_processed,
                    file_name="Corrected_Paychex_Template.csv",
                    mime="text/csv",
                    help="Download the finalized and corrected data ready for import."
                )
        except Exception as e:
            st.error(f"⚠️ Error processing the uploaded payroll file: {e}")

# ==========================================
# TAB 2: MULTI-EXCEL TIMESHEET CONVERTER
# ==========================================
with tab2:
    st.markdown("""
        <div class="custom-card">
            <h3>📥 Multi-Excel Timesheet Converter</h3>
            <p>Upload 10 to 15 Excel timesheets simultaneously. The engine will parse, aggregate, and map your entries directly into standard Paychex import codes.</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_excels = st.file_uploader(
        "Drop your Excel Timesheets here (Multiple files supported)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="multi_excel_uploader"
    )

    if uploaded_excels:
        all_paychex_rows = []

        with st.spinner(f"✨ Processing {len(uploaded_excels)} Excel files simultaneously..."):
            for file in uploaded_excels:
                try:
                    df = pd.read_excel(file)
                    file_name_lower = file.name.lower()

                    for index, row in df.iterrows():
                        row_text = " ".join([str(val) for val in row.values]).lower()
                        combined_text = file_name_lower + " " + row_text

                        category = "Time Sheet"
                        pay_code = "REG"

                        if any(k in combined_text for k in ["mile", "travel", "mileage"]):
                            category = "Mileage"
                            pay_code = "MIL"
                        elif any(k in combined_text for k in ["case manager", "cm hours", "casemanager"]):
                            category = "Case Manager Hours"
                            pay_code = "CM_HRS"
                        elif any(k in combined_text for k in ["train", "course", "training"]):
                            category = "Training"
                            pay_code = "TRN"

                        emp_name = "Employee"
                        units_val = 0.00

                        string_vals = [str(val) for val in row.values if
                                       isinstance(val, str) and len(str(val).strip()) > 2]
                        numeric_vals = [val for val in row.values if isinstance(val, (int, float)) and val > 0]

                        if string_vals:
                            emp_name = string_vals[0]
                        if numeric_vals:
                            units_val = numeric_vals[0]

                        if units_val > 0:
                            all_paychex_rows.append({
                                "Employee ID": "",
                                "Employee Name": emp_name,
                                "Pay Code": pay_code,
                                "Units/Hours": units_val,
                                "Category Description": category,
                                "Source File": file.name
                            })
                except Exception as ex:
                    st.warning(f"⚠️ Could not parse file {file.name}: {ex}")

        if all_paychex_rows:
            df_paychex_master = pd.DataFrame(all_paychex_rows)

            st.markdown(
                f'<div class="metric-pill">Successfully compiled {len(uploaded_excels)} files into {len(df_paychex_master)} Paychex records</div>',
                unsafe_allow_html=True)
            st.dataframe(df_paychex_master, use_container_width=True)

            csv_output = df_paychex_master.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Master Paychex Import CSV",
                data=csv_output,
                file_name="Master_Paychex_Import.csv",
                mime="text/csv"
            )
        else:
            st.info(
                "ℹ️ Uploaded files were processed, but no valid hours or units were detected inside the spreadsheets.")