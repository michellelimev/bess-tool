import streamlit as st
import pandas as pd
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import io

st.set_page_config(page_title="BESS Sizing Tool", layout="wide", initial_sidebar_state="expanded")

# Title
st.title("🔋 Battery Energy Storage System (BESS) Sizing Tool")
st.markdown("**Interactive Dashboard** - Adjust parameters below and watch calculations update in real-time")

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
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None)
        return df
    except:
        return None

wb = load_workbook(uploaded_file)
sheet_names = wb.sheetnames

st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Available Sheets:** {len(sheet_names)}")

# ============ CALCULATION FUNCTIONS ============
def calculate_system(power_mw, energy_mwh, cycles_day, temp_c, pf, efficiency_total, battery_specs, inverter_specs, enclosure_specs):
    """Calculate system parameters based on inputs"""
    
    # Power calculations
    required_power_poi = power_mw
    required_power_inv = required_power_poi / inverter_specs['efficiency']
    required_power_racks = required_power_inv / efficiency_total
    
    # Energy calculations
    required_energy_poi = energy_mwh
    required_energy_racks = required_energy_poi / efficiency_total
    
    # RTE calculation
    rte_bol = efficiency_total * inverter_specs['efficiency'] * 0.96
    
    # Equipment sizing
    required_racks = max(1, int(np.ceil(required_energy_racks * 1000 / battery_specs['energy_per_rack'])))
    required_enclosures = max(1, int(np.ceil(required_racks / enclosure_specs['racks'])))
    required_inverters = max(1, int(np.ceil(required_power_inv / inverter_specs['power'])))
    required_transformers = required_inverters
    
    # Temperature derating
    if temp_c > 40:
        derate_factor = 1 - (temp_c - 40) * 0.01
    else:
        derate_factor = 1.0
    
    derated_power = required_power_inv * derate_factor
    
    # Cost calculation
    cost_batteries = required_enclosures * enclosure_specs['cost_per_unit'] * battery_specs['cost_impact']
    cost_inverters = required_inverters * inverter_specs['cost_per_unit']
    cost_transformers = required_transformers * 0.08
    cost_other = (cost_batteries + cost_inverters + cost_transformers) * 0.4
    total_capex = cost_batteries + cost_inverters + cost_transformers + cost_other
    
    return {
        'power_poi': required_power_poi,
        'power_inverter': required_power_inv,
        'power_racks': required_power_racks,
        'energy_poi': required_energy_poi,
        'energy_racks': required_energy_racks,
        'rte_bol': rte_bol * 100,
        'derate_factor': derate_factor,
        'derated_power': derated_power,
        'required_racks': required_racks,
        'required_enclosures': required_enclosures,
        'required_inverters': required_inverters,
        'required_transformers': required_transformers,
        'total_capex': total_capex,
        'cost_per_kw': total_capex / power_mw if power_mw > 0 else 0,
        'cost_per_kwh': total_capex / energy_mwh if energy_mwh > 0 else 0,
    }

# ============ PARAMETER CONTROLS IN SIDEBAR ============
st.sidebar.markdown("---")
st.sidebar.header("⚙️ PARAMETER ADJUSTMENT")
st.sidebar.markdown("Adjust all parameters to recalculate system sizing:")

power_mw = st.sidebar.slider("🔌 Required Power (MW)", min_value=25, max_value=500, value=100, step=5, help="Power capacity at Point of Interconnection")
energy_mwh = st.sidebar.slider("⚡ Required Energy (MWh)", min_value=50, max_value=2000, value=400, step=50, help="Energy storage capacity at POI")
cycles_day = st.sidebar.slider("🔄 Cycles per Day", min_value=0.5, max_value=5.0, value=1.0, step=0.25, help="Daily charge/discharge cycles")
temp_c = st.sidebar.slider("🌡️ Max Site Temperature (°C)", min_value=20, max_value=60, value=40, step=2, help="Maximum ambient temperature")
pf = st.sidebar.slider("⚙️ Power Factor", min_value=0.85, max_value=1.0, value=0.95, step=0.01, help="System power factor at POI")
efficiency_total = st.sidebar.slider("📊 Total System Efficiency", min_value=0.90, max_value=0.98, value=0.9606, step=0.0025, help="Overall one-way system efficiency")

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Equipment Selections")

battery_types = {
    'REPT 314Ah 0.25C': {'energy_per_rack': 418, 'power_per_rack': 251, 'cost_impact': 1.0},
    'REPT 320Ah 0.25C': {'energy_per_rack': 426, 'power_per_rack': 256, 'cost_impact': 1.02},
    'REPT 345Ah 0.25C': {'energy_per_rack': 459, 'power_per_rack': 161, 'cost_impact': 1.05},
    'CATL 306Ah 0.25C': {'energy_per_rack': 407, 'power_per_rack': 244, 'cost_impact': 0.98},
}
battery_selection = st.sidebar.selectbox("🔋 Battery Type", list(battery_types.keys()), index=0)

inverter_types = {
    'Sineng EH-5000': {'power': 5.5, 'efficiency': 0.985, 'cost_per_unit': 200},
    'Sineng EH-6000': {'power': 6.0, 'efficiency': 0.986, 'cost_per_unit': 220},
    'EPC Power M8': {'power': 5.4, 'efficiency': 0.984, 'cost_per_unit': 210},
}
inverter_selection = st.sidebar.selectbox("⚡ Inverter Model", list(inverter_types.keys()), index=0)

enclosure_types = {
    'B-VAULT DC PLTF 3.n': {'racks': 12, 'energy': 5016, 'cost_per_unit': 68},
    'B-VAULT DC PLTF 2.2A': {'racks': 10, 'energy': 4272, 'cost_per_unit': 58},
    'B-VAULT AC PLTF 2.2': {'racks': 10, 'energy': 4272, 'cost_per_unit': 76},
}
enclosure_selection = st.sidebar.selectbox("📦 Battery Enclosure", list(enclosure_types.keys()), index=0)

battery_specs = battery_types[battery_selection]
inverter_specs = inverter_types[inverter_selection]
enclosure_specs = enclosure_types[enclosure_selection]

calc_results = calculate_system(power_mw, energy_mwh, cycles_day, temp_c, pf, efficiency_total, battery_specs, inverter_specs, enclosure_specs)

# ============ MAIN CONTENT TABS ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Summary", "📊 Performance & Projections", "💰 Cost Analysis", "🔧 System Details", "📁 All Data Sheets"])

with tab1:
    st.header("System Configuration Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Power Capacity", f"{power_mw} MW", f"±{power_mw-100:+.0f} vs baseline", delta_color="off")
    with col2:
        st.metric("Energy Capacity", f"{energy_mwh} MWh", f"±{energy_mwh-400:+.0f} vs baseline", delta_color="off")
    with col3:
        st.metric("RTE at BOL", f"{calc_results['rte_bol']:.1f}%", f"Efficiency: {efficiency_total*100:.2f}%", delta_color="off")
    with col4:
        st.metric("Temperature Derating", f"{calc_results['derate_factor']*100:.1f}%", f"@ {temp_c}°C", delta_color="off")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🔋 Battery System")
        st.markdown(f"- **Type:** {battery_selection}\n- **Enclosure:** {enclosure_selection}\n- **Racks per Enclosure:** {enclosure_specs['racks']}\n- **Energy per Rack:** {battery_specs['energy_per_rack']} kWh")
        st.success(f"**→ {calc_results['required_racks']} racks in {calc_results['required_enclosures']} enclosures**")
    with col2:
        st.subheader("⚡ Power Electronics")
        st.markdown(f"- **Inverter:** {inverter_selection}\n- **Rated Power:** {inverter_specs['power']} MVA\n- **Efficiency:** {inverter_specs['efficiency']*100:.2f}%\n- **Power Factor:** {pf:.3f}")
        st.success(f"**→ {calc_results['required_inverters']} inverters needed**")
    with col3:
        st.subheader("📋 Operating Parameters")
        st.markdown(f"- **Cycles/Day:** {cycles_day}\n- **Max Temperature:** {temp_c}°C\n- **System Efficiency:** {efficiency_total*100:.2f}%\n- **Total Transformers:** {calc_results['required_transformers']}")
    
    st.markdown("---")
    st.subheader("Power Flow & Losses")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("At POI", f"{calc_results['power_poi']:.1f} MW", "Input")
    with col2:
        st.metric("Inverter Output", f"{calc_results['power_inverter']:.1f} MW", f"Eff: {inverter_specs['efficiency']*100:.1f}%")
    with col3:
        st.metric("After Derating", f"{calc_results['derated_power']:.1f} MW", f"{calc_results['derate_factor']*100:.1f}%")
    with col4:
        st.metric("At Racks", f"{calc_results['power_racks']:.1f} MW", f"Eff: {efficiency_total*100:.2f}%")

with tab2:
    st.header("25-Year Performance Projections")
    years = list(range(0, 26))
    degradation_curve = [100, 95.04, 92.70, 90.76, 89.04, 87.46, 85.99, 84.61, 83.30, 82.04, 80.83, 79.66, 78.54, 77.44, 76.37, 75.33, 74.32, 73.32, 72.35, 71.40, 70.46, 69.54, 68.63, 67.75, 66.87, 66.00]
    degradation_adjusted = [100 - (100-d) * (cycles_day/1.0) for d in degradation_curve]
    rte_curve = [84.13, 84.92, 84.72, 84.55, 84.38, 84.23, 84.08, 83.93, 83.79, 83.66, 83.52, 83.38, 83.25, 83.11, 82.98, 82.84, 82.71, 82.57, 82.44, 82.30, 82.16, 82.03, 81.95, 81.75, 81.65, 81.65]
    energy_capacity = [calc_results['energy_poi'] * (d/100) for d in degradation_adjusted]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Battery Degradation (SOH %)")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(years, degradation_adjusted, marker='o', linewidth=2.5, markersize=5, color='#FF6B6B')
        ax1.fill_between(years, degradation_adjusted, alpha=0.3, color='#FF6B6B')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('State of Health (%)')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([60, 105])
        st.pyplot(fig1)
    with col2:
        st.subheader("Round-Trip Efficiency (RTE)")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(years, rte_curve, marker='s', linewidth=2.5, markersize=5, color='#4ECDC4')
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
    ax3.axhline(y=energy_mwh, color='red', linestyle='--', linewidth=2, label=f'Required Energy ({energy_mwh} MWh)')
    ax3.fill_between(years, energy_capacity, alpha=0.3, color='#95E1D3')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('AC Usable Energy (MWh)')
    ax3.set_title('Energy Capacity Degradation Over 25 Years')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)
    
    st.markdown("---")
    st.subheader("Detailed Projections Table")
    projection_data = {'Year': years, 'SOH (%)': [round(d, 2) for d in degradation_adjusted], 'RTE (%)': [round(r, 2) for r in rte_curve], 'Energy (MWh)': [round(e, 2) for e in energy_capacity], 'Annual Cycles': [round(cycles_day * 365, 0) for _ in years], 'Throughput (GWh)': [round(e * cycles_day * 365 / 1000, 2) for e in energy_capacity]}
    df_projections = pd.DataFrame(projection_data)
    st.dataframe(df_projections, use_container_width=True, height=400)

with tab3:
    st.header("Cost Analysis & Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Capital Costs")
        cost_breakdown = {'Component': ['Batteries', 'Inverters', 'Transformers', 'Other Equipment'], 'Cost ($M)': [calc_results['required_enclosures'] * enclosure_specs['cost_per_unit'] * battery_specs['cost_impact'] / 1000, calc_results['required_inverters'] * inverter_specs['cost_per_unit'] / 1000, calc_results['required_transformers'] * 0.08, (calc_results['required_enclosures'] * enclosure_specs['cost_per_unit'] * battery_specs['cost_impact'] + calc_results['required_inverters'] * inverter_specs['cost_per_unit'] + calc_results['required_transformers'] * 80) * 0.4 / 1000]}
        df_cost = pd.DataFrame(cost_breakdown)
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFA07A']
        ax4.pie(df_cost['Cost ($M)'], labels=df_cost['Component'], autopct='%1.1f%%', colors=colors, startangle=90)
        ax4.set_title('CAPEX Breakdown')
        st.pyplot(fig4)
    with col2:
        st.subheader("Cost Metrics")
        st.dataframe(df_cost, use_container_width=True)
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total CAPEX", f"${calc_results['total_capex']:.1f}M")
        with col_b:
            st.metric("$/kW", f"${calc_results['cost_per_kw']:.0f}")
        with col_c:
            st.metric("$/kWh", f"${calc_results['cost_per_kwh']:.0f}")

with tab4:
    st.header("Detailed System Configuration")
    st.subheader("Equipment Quantities")
    equipment_data = {'Component': ['Battery Enclosures', 'Battery Racks', 'Inverter Units', 'MV Transformers', 'Cycles per Day', 'Estimated Annual Throughput'], 'Quantity': [f"{calc_results['required_enclosures']} units", f"{calc_results['required_racks']} racks", f"{calc_results['required_inverters']} units", f"{calc_results['required_transformers']} units", f"{cycles_day} cycles/day", f"{energy_mwh * cycles_day * 365 / 1000:.0f} GWh/year"]}
    df_equip = pd.DataFrame(equipment_data)
    st.dataframe(df_equip, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Energy & Power Summary")
    summary_data = {'Parameter': ['Required Power at POI', 'Power at Inverter Output', 'Power at Racks', 'Required Energy at POI', 'Energy at Racks', 'RTE at BOL', 'System Efficiency', 'Temperature Derating Factor'], 'Value': [f"{calc_results['power_poi']:.2f} MW", f"{calc_results['power_inverter']:.2f} MW", f"{calc_results['power_racks']:.2f} MW", f"{calc_results['energy_poi']:.2f} MWh", f"{calc_results['energy_racks']:.2f} MWh", f"{calc_results['rte_bol']:.2f}%", f"{efficiency_total*100:.2f}%", f"{calc_results['derate_factor']:.3f} ({calc_results['derate_factor']*100:.1f}%)"]}
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)

with tab5:
    st.header("Raw Data from All Sheets")
    sheet_selector = st.selectbox("Select Sheet to View:", sheet_names)
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_selector, header=None)
        st.subheader(f"Sheet: {sheet_selector}")
        st.info(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        col1, col2 = st.columns(2)
        with col1:
            rows_display = st.slider("Rows to display:", min_value=10, max_value=min(500, df.shape[0]), value=50, key=f"rows_{sheet_selector}")
        with col2:
            cols_display = st.slider("Columns to display:", min_value=5, max_value=min(30, df.shape[1]), value=15, key=f"cols_{sheet_selector}")
        st.dataframe(df.iloc[:rows_display, :cols_display], use_container_width=True, height=600)
        csv = df.to_csv(index=False)
        st.download_button(label=f"📥 Download {sheet_selector} as CSV", data=csv, file_name=f"{sheet_selector}.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error loading sheet: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'><small>BESS Sizing Tool Dashboard | Real-time Calculations | Interactive Parameter Adjustment</small></div>", unsafe_allow_html=True)
