import streamlit as st
import pandas as pd
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import io

st.set_page_config(page_title="BESS Sizing Tool", layout="wide", initial_sidebar_state="expanded")

# Title and description
st.title("🔋 Battery Energy Storage System (BESS) Sizing Tool")
st.markdown("Interactive dashboard for 100 MW / 400 MWh BESS project analysis")

# Sidebar for file upload
st.sidebar.header("📁 Project File")
uploaded_file = st.sidebar.file_uploader("Upload Excel workbook (.xlsm)", type=["xlsm", "xlsx"])

if uploaded_file is None:
    st.info("👈 Upload your Combined_Tool_V2_4_11_KS_Update.xlsm file to get started")
    st.stop()

# Load workbook
@st.cache_data
def load_workbook(file):
    wb = openpyxl.load_workbook(file, data_only=True)
    return wb

@st.cache_data
def extract_sheet_data(file, sheet_name):
    """Extract all data from a sheet as a dataframe"""
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None)
        return df
    except:
        return None

# Load the workbook
wb = load_workbook(uploaded_file)
sheet_names = wb.sheetnames

st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Available Sheets:** {len(sheet_names)}")

# Create tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Summary", 
    "⚙️ Interface Inputs",
    "📈 Performance & Projections",
    "💰 Cost Analysis",
    "📊 All Sheets"
])

# ============ TAB 1: SUMMARY ============
with tab1:
    st.header("Project Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Power Capacity", "100 MW", "at POI")
    with col2:
        st.metric("Energy Capacity", "416.38 MWh", "AC Usable")
    with col3:
        st.metric("Expected COD", "Q4 2030", "")
    with col4:
        st.metric("RTE at BOL", "84.1%", "Guaranteed")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔋 Battery System")
        st.markdown("""
        - **Type:** B-VAULT DC PLTF 3.n REPT_Deep_Racks
        - **Quantity:** 92 enclosures
        - **Battery:** REPT 314Ah 0.25C
        - **DC Nameplate:** 461.47 MWh
        """)
    
    with col2:
        st.subheader("⚡ Power Electronics")
        st.markdown("""
        - **Inverter:** Sineng EH-5000-HB-UD-US
        - **Quantity:** 23 units
        - **MV Skid:** Sineng EH-5000-HB-UD-US-34.5
        - **Rated Power:** 5.5 MVA each
        """)
    
    with col3:
        st.subheader("🏗️ Infrastructure")
        st.markdown("""
        - **MV Voltage:** 33 kV
        - **Transformers:** 23 @ 5.5 MVA
        - **Feeders:** 5 total
        - **Aux Transformers:** 2 @ 1.66 MVA
        """)
    
    st.markdown("---")
    st.subheader("💵 Cost Summary")
    
    cost_data = {
        'Component': ['Batteries', 'Enclosures', 'Inverters', 'EMS (HW & SW)', 'Warranty Management', 'Internal Costs', 'External Costs'],
        'Cost ($M)': [29.07, 6.26, 4.60, 0.47, 1.00, 2.48, 0.54],
        '$/kWh': [72.68, 15.64, 11.50, 1.18, 2.50, 6.20, 1.36]
    }
    
    df_costs = pd.DataFrame(cost_data)
    st.dataframe(df_costs, use_container_width=True)

# ============ TAB 2: INTERFACE INPUTS ============
with tab2:
    st.header("Interface Sheet - Project Inputs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Parameters")
        st.info("""
        **Baseline Values (from spreadsheet):**
        - Required Power at POI: 100 MW
        - Required Energy at POI: 400 MWh
        - Cycles per Day: 1
        - Power Factor: 0.95
        - Max Site Temperature: 40°C
        - Region: NAM (North America)
        - Expected COD: Q4 2030
        """)
    
    with col2:
        st.subheader("System Efficiency Chain")
        efficiency_chain = {
            'Component': [
                'HV T-Line',
                'MV Collection',
                'MV Transformer',
                'LV Cables',
                'Inverter',
                'DC Cables',
                'Total One-Way'
            ],
            'Efficiency': [1.0, 0.995, 0.99, 1.0, 0.985, 0.99, 0.9606]
        }
        df_eff = pd.DataFrame(efficiency_chain)
        st.dataframe(df_eff, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Interactive Parameter Adjustment")
    st.warning("⚠️ Note: Adjust parameters to see how they affect sizing. This is a preview tool—for detailed recalculations, update the Excel file.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        power_mw = st.slider("Power (MW)", min_value=50, max_value=200, value=100, step=10)
    with col2:
        energy_mwh = st.slider("Energy (MWh)", min_value=100, max_value=1000, value=400, step=50)
    with col3:
        temp_c = st.slider("Max Site Temp (°C)", min_value=20, max_value=55, value=40, step=5)
    
    st.info(f"**Selected Configuration:** {power_mw} MW / {energy_mwh} MWh @ {temp_c}°C")

# ============ TAB 3: PERFORMANCE & PROJECTIONS ============
with tab3:
    st.header("25-Year Performance Projections")
    
    years = list(range(0, 26))
    degradation_curve = [
        100, 95.04, 92.70, 90.76, 89.04, 87.46, 85.99, 84.61, 83.30, 82.04,
        80.83, 79.66, 78.54, 77.44, 76.37, 75.33, 74.32, 73.32, 72.35, 71.40,
        70.46, 69.54, 68.63, 67.75, 66.87, 66.00
    ]
    
    rte_curve = [
        84.13, 84.92, 84.72, 84.55, 84.38, 84.23, 84.08, 83.93, 83.79, 83.66,
        83.52, 83.38, 83.25, 83.11, 82.98, 82.84, 82.71, 82.57, 82.44, 82.30,
        82.16, 82.03, 81.95, 81.75, 81.65, 81.65
    ]
    
    energy_capacity = [100 * (d/100) * 416.38 / 100 for d in degradation_curve]
    
    proj_col1, proj_col2 = st.columns(2)
    
    with proj_col1:
        st.subheader("Battery Degradation (SOH %)")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(years, degradation_curve, marker='o', linewidth=2, markersize=4, color='#FF6B6B')
        ax1.fill_between(years, degradation_curve, alpha=0.3, color='#FF6B6B')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('State of Health (%)')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([60, 105])
        st.pyplot(fig1)
    
    with proj_col2:
        st.subheader("Round-Trip Efficiency (RTE)")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(years, rte_curve, marker='s', linewidth=2, markersize=4, color='#4ECDC4')
        ax2.fill_between(years, rte_curve, alpha=0.3, color='#4ECDC4')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('RTE (%)')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([80, 86])
        st.pyplot(fig2)
    
    st.markdown("---")
    
    st.subheader("AC Usable Energy Capacity @ POI (MWh)")
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    ax3.plot(years, energy_capacity, marker='D', linewidth=2.5, markersize=5, color='#95E1D3')
    ax3.axhline(y=400, color='red', linestyle='--', linewidth=2, label='Required Energy (400 MWh)')
    ax3.fill_between(years, energy_capacity, alpha=0.3, color='#95E1D3')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('AC Usable Energy (MWh)')
    ax3.set_title('Energy Capacity Degradation Over 25 Years')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)
    
    st.markdown("---")
    
    st.subheader("Detailed Projections Table")
    projection_data = {
        'Year': years,
        'SOH (%)': [round(d, 2) for d in degradation_curve],
        'RTE (%)': [round(r, 2) for r in rte_curve],
        'Energy Capacity (MWh)': [round(e, 2) for e in energy_capacity],
        'Annual Throughput (MWh)': [round(e * 365, 0) for e in energy_capacity]
    }
    df_projections = pd.DataFrame(projection_data)
    st.dataframe(df_projections, use_container_width=True, height=400)

# ============ TAB 4: COST ANALYSIS ============
with tab4:
    st.header("Cost Analysis & Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Capital Cost by Component")
        
        components = ['Batteries', 'Enclosures', 'Inverters', 'EMS', 'Warranty', 'Int. Costs', 'Ext. Costs']
        costs = [29.07, 6.26, 4.60, 0.47, 1.00, 2.48, 0.54]
        
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        colors = plt.cm.Set3(np.linspace(0, 1, len(components)))
        wedges, texts, autotexts = ax4.pie(costs, labels=components, autopct='%1.1f%%', 
                                            colors=colors, startangle=90)
        ax4.set_title('BESS Capital Cost Distribution')
        st.pyplot(fig4)
    
    with col2:
        st.subheader("Cost per Unit")
        
        cost_per_unit = {
            'Component': components,
            'Cost ($M)': costs,
            '$/kWh-AC': [72.68, 15.64, 11.50, 1.18, 2.50, 6.20, 1.36],
            '% of Total': [round(c/sum(costs)*100, 1) for c in costs]
        }
        df_cost_unit = pd.DataFrame(cost_per_unit)
        st.dataframe(df_cost_unit, use_container_width=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total CAPEX", "$44.42M", "estimated")
    with col2:
        st.metric("Cost per kWh-AC", "$111.01", "")
    with col3:
        st.metric("Cost per kW", "$0.44M", "")

# ============ TAB 5: ALL SHEETS ============
with tab5:
    st.header("Raw Data from All Sheets")
    
    sheet_selector = st.selectbox("Select Sheet to View:", sheet_names)
    
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_selector, header=None)
        
        st.subheader(f"Sheet: {sheet_selector}")
        st.info(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        
        col1, col2 = st.columns(2)
        with col1:
            rows_display = st.slider("Rows to display:", min_value=10, max_value=min(500, df.shape[0]), value=50)
        with col2:
            cols_display = st.slider("Columns to display:", min_value=5, max_value=min(30, df.shape[1]), value=15)
        
        st.dataframe(df.iloc[:rows_display, :cols_display], use_container_width=True, height=600)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {sheet_selector} as CSV",
            data=csv,
            file_name=f"{sheet_selector}.csv",
            mime="text/csv"
        )
    
    except Exception as e:
        st.error(f"Error loading sheet: {e}")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
<small>BESS Sizing Tool Dashboard | Python + Streamlit | 100 MW / 400 MWh Project</small>
</div>
""", unsafe_allow_html=True)
