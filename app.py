import streamlit as st
import pandas as pd

st.set_page_config(page_title="BESS Data Diagnostic", layout="wide")

st.title("🔍 BESS Data Table Diagnostic Tool")

st.sidebar.header("📁 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload Excel workbook", type=["xlsm", "xlsx"])

if uploaded_file is None:
    st.info("Upload your Excel file")
    st.stop()

sheet_names = ['BVault', 'PCS Data', 'Battery Rack Data', 'Battery Enclosure Data',
               'Calendar Degradation', 'Cycling Degradation', 'RTE Data', 'Cost Book', 'System Efficiency']

tables = {}
for sheet in sheet_names:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
        tables[sheet] = df
    except Exception as e:
        st.warning(f"Could not load {sheet}")

selected_table = st.selectbox("Select table:", list(tables.keys()))

if selected_table in tables and not tables[selected_table].empty:
    df = tables[selected_table]
    st.subheader(f"Table: {selected_table}")
    st.info(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    st.markdown("**Columns:**")
    st.write(list(df.columns))
    
    st.markdown("**First 5 rows:**")
    st.dataframe(df.head(5), use_container_width=True)
else:
    st.error(f"Table '{selected_table}' is empty")
