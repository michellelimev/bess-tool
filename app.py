import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="BESS Sizing Tool", layout="wide", initial_sidebar_state="expanded")

st.title("🔋 Battery Energy Storage System (BESS) Sizing Tool")
st.markdown("**Interactive Dashboard** - Adjust parameters and see real-time calculations")

st.sidebar.header("📁 Project File")
uploaded_file = st.sidebar.file_uploader("Upload Excel workbook (.xlsm)", type=["xlsm", "xlsx"])

if uploaded_file is None:
    st.info("👈 Upload your Excel file to get started")
    st.stop()

try:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Available Sheets:** {len(sheet_names)}")

def calculate_system(power_mw, energy_mwh, cycles_day, temp_c, pf, efficiency_total, battery_specs, inverter_specs, enclosure_specs):
    required_power_poi = power_mw
    required_power_inv = required_power_poi / inverter_specs['efficiency']
    required_power_racks = required_power_inv / efficiency_total
    required_energy_poi = energy_mwh
    required_energy_racks = required_energy_poi / efficiency_total
    rte_bol = efficiency_total * inverter_specs['efficiency'] * 0.96
    required_racks = max(1, int(np.ceil(required_energy_racks * 1000 / battery_specs['energy_per_rack'])))
    required_enclosures = max(1, int(np.ceil(required_racks / enclosure_specs['racks'])))
    required_inverters = max(1, int(np.ceil(required_power_inv / inverter_specs['power'])))
    required_transformers = required_inverters
    derate_factor = 1 - (temp_c - 40) * 0.01 if temp_c > 40 else 1.0
    derated_power = required_power_inv * derate_factor
    cost_batteries = required_enclosures * enclosure_specs['cost_per_unit'] * battery_specs['cost_impact']
    cost_inverters = required_inverters * inverter_specs['cost_per_unit']
    cost_transformers = required_transformers * 0.08
    cost_other = (cost_batteries + cost_inverters + cost_transformers) * 0.4
    total_capex = cost_batteries + cost_inverters + cost_transformers + cost_other
    return {'power_poi': required_power_poi, 'power_inverter': required_power_inv, 'power_racks': required_power_racks,
            'energy_poi': required_energy_poi, 'energy_racks': required_energy_racks, 'rte_bol': rte_bol * 100,
            'derate_factor': derate_factor, 'derated_power': derated_power, 'required_racks': required_racks,
            'required_enclosures': required_enclosures, 'required_inverters': required_inverters,
            'required_transformers': required_transformers, 'total_capex': total_capex,
            'cost_per_kw': total_capex / power_mw if power_mw > 0 else 0, 'cost_per_kwh': total_capex / energy_mwh if energy_mwh > 0 else 0}

st.sidebar.markdown("---")
st.sidebar.header("⚙️ PARAMETER ADJUSTMENT")

power_mw = st.sidebar.slider("🔌 Power (MW)", 25, 500, 100, 5)
energy_mwh = st.sidebar.slider("⚡ Energy (MWh)", 50, 2000, 400, 50)
cycles_day = st.sidebar.slider("🔄 Cycles/Day", 0.5, 5.0, 1.0, 0.25)
temp_c = st.sidebar.slider("🌡️ Temp (°C)", 20, 60, 40, 2)
pf = st.sidebar.slider("⚙️ Power Factor", 0.85, 1.0, 0.95, 0.01)
efficiency_total = st.sidebar.slider("📊 Efficiency", 0.90, 0.98, 0.9606, 0.0025)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Equipment")

battery_types = {
    'REPT 314Ah 0.25C': {'energy_per_rack': 418, 'power_per_rack': 251, 'cost_impact': 1.0},
    'REPT 320Ah 0.25C': {'energy_per_rack': 426, 'power_per_rack': 256, 'cost_impact': 1.02},
    'REPT 345Ah 0.25C': {'energy_per_rack': 459, 'power_per_rack': 161, 'cost_impact': 1.05},
    'CATL 306Ah 0.25C': {'energy_per_rack': 407, 'power_per_rack': 244, 'cost_impact': 0.98}
}
battery_selection = st.sidebar.selectbox("🔋 Battery", list(battery_types.keys()))

inverter_types = {
    'Sineng EH-5000': {'power': 5.5, 'efficiency': 0.985, 'cost_per_unit': 200},
    'Sineng EH-6000': {'power': 6.0, 'efficiency': 0.986, 'cost_per_unit': 220},
    'EPC Power M8': {'power': 5.4, 'efficiency': 0.984, 'cost_per_unit': 210}
}
inverter_selection = st.sidebar.selectbox("⚡ Inverter", list(inverter_types.keys()))

enclosure_types = {
    'B-VAULT DC PLTF 3.n': {'racks': 12, 'energy': 5016, 'cost_per_unit': 68},
    'B-VAULT DC PLTF 2.2A': {'racks': 10, 'energy': 4272, 'cost_per_unit': 58},
    'B-VAULT AC PLTF 2.2': {'racks': 10, 'energy': 4272, 'cost_per_unit': 76}
}
enclosure_selection = st.sidebar.selectbox("📦 Enclosure", list(enclosure_types.keys()))

battery_specs = battery_types[battery_selection]
inverter_specs = inverter_types[inverter_selection]
enclosure_specs = enclosure_types[enclosure_selection]
calc_results = calculate_system(power_mw, energy_mwh, cycles_day, temp_c, pf, efficiency_total, battery_specs, inverter_specs, enclosure_specs)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Summary", "📊 Performance", "💰 Cost", "🔧 Details", "📁 Data"])

with tab1:
    st.header("System Configuration")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Power", f"{power_mw} MW")
    col2.metric("Energy", f"{energy_mwh} MWh")
    col3.metric("RTE @ BOL", f"{calc_results['rte_bol']:.1f}%")
    col4.metric("Derating", f"{calc_results['derate_factor']*100:.1f}%")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🔋 Battery")
        st.markdown(f"**Model:** {battery_selection}\n**Enclosure:** {enclosure_selection}\n**Qty:** {calc_results['required_enclosures']} enclosures\n**Racks:** {calc_results['required_racks']}")
    with col2:
        st.subheader("⚡ Power Electronics")
        st.markdown(f"**Model:** {inverter_selection}\n**Power:** {inverter_specs['power']} MVA\n**Efficiency:** {inverter_specs['efficiency']*100:.2f}%\n**Qty:** {calc_results['required_inverters']} units")
    with col3:
        st.subheader("📋 Operating")
        st.markdown(f"**Cycles/Day:** {cycles_day}\n**Temperature:** {temp_c}°C\n**Power Factor:** {pf:.2f}\n**Transformers:** {calc_results['required_transformers']}")
    st.markdown("---")
    st.subheader("Power Flow")
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    pcol1.metric("POI", f"{calc_results['power_poi']:.1f} MW")
    pcol2.metric("Inverter", f"{calc_results['power_inverter']:.1f} MW")
    pcol3.metric("Derated", f"{calc_results['derated_power']:.1f} MW")
    pcol4.metric("Racks", f"{calc_results['power_racks']:.1f} MW")

with tab2:
    st.header("25-Year Projections")
    years = list(range(26))
    degradation_curve = [100, 95.04, 92.70, 90.76, 89.04, 87.46, 85.99, 84.61, 83.30, 82.04, 80.83, 79.66, 78.54, 77.44, 76.37, 75.33, 74.32, 73.32, 72.35, 71.40, 70.46, 69.54, 68.63, 67.75, 66.87, 66.00]
    degradation_adjusted = [100 - (100-d) * (cycles_day/1.0) for d in degradation_curve]
    rte_curve = [84.13, 84.92, 84.72, 84.55, 84.38, 84.23, 84.08, 83.93, 83.79, 83.66, 83.52, 83.38, 83.25, 83.11, 82.98, 82.84, 82.71, 82.57, 82.44, 82.30, 82.16, 82.03, 81.95, 81.75, 81.65, 81.65]
    energy_capacity = [calc_results['energy_poi'] * (d/100) for d in degradation_adjusted]
    col1, col2 = st.columns(2)
    with col1:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(years, degradation_adjusted, marker='o', linewidth=2.5, color='#FF6B6B')
        ax1.fill_between(years, degradation_adjusted, alpha=0.3, color='#FF6B6B')
        ax1.set_title("Degradation (SOH %)")
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)
    with col2:
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(years, rte_curve, marker='s', linewidth=2.5, color='#4ECDC4')
        ax2.fill_between(years, rte_curve, alpha=0.3, color='#4ECDC4')
        ax2.set_title("RTE (%)")
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)
    st.markdown("---")
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    ax3.plot(years, energy_capacity, marker='D', linewidth=2.5, color='#95E1D3')
    ax3.axhline(y=energy_mwh, color='red', linestyle='--', linewidth=2, label=f'Required ({energy_mwh} MWh)')
    ax3.fill_between(years, energy_capacity, alpha=0.3, color='#95E1D3')
    ax3.set_title("Energy Capacity Over 25 Years")
    ax3.set_xlabel('Year')
    ax3.set_ylabel('MWh')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)
    st.markdown("---")
    projection_data = {'Year': years, 'SOH (%)': [round(d, 2) for d in degradation_adjusted], 'RTE (%)': [round(r, 2) for r in rte_curve], 'Energy (MWh)': [round(e, 2) for e in energy_capacity]}
    st.dataframe(pd.DataFrame(projection_data), use_container_width=True)

with tab3:
    st.header("Cost Analysis")
    col1, col2 = st.columns(2)
    with col1:
        bat_cost = calc_results['required_enclosures'] * enclosure_specs['cost_per_unit'] * battery_specs['cost_impact']
        inv_cost = calc_results['required_inverters'] * inverter_specs['cost_per_unit']
        trans_cost = calc_results['required_transformers'] * 0.08
        other_cost = (bat_cost + inv_cost + trans_cost) * 0.4
        cost_breakdown = {'Component': ['Batteries', 'Inverters', 'Transformers', 'Other'], 'Cost ($M)': [bat_cost / 1000, inv_cost / 1000, trans_cost, other_cost / 1000]}
        df_cost = pd.DataFrame(cost_breakdown)
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFA07A']
        ax4.pie(df_cost['Cost ($M)'], labels=df_cost['Component'], autopct='%1.1f%%', colors=colors)
        ax4.set_title('CAPEX Breakdown')
        st.pyplot(fig4)
    with col2:
        st.dataframe(df_cost, use_container_width=True)
        st.markdown("---")
        ccol1, ccol2, ccol3 = st.columns(3)
        ccol1.metric("Total CAPEX", f"${calc_results['total_capex']:.1f}M")
        ccol2.metric("$/kW", f"${calc_results['cost_per_kw']:.0f}")
        ccol3.metric("$/kWh", f"${calc_results['cost_per_kwh']:.0f}")

with tab4:
    st.header("System Details")
    details = {'Parameter': ['Power POI', 'Power Inverter', 'Power Racks', 'Energy POI', 'Energy Racks', 'RTE BOL', 'Efficiency', 'Derating'],
               'Value': [f"{calc_results['power_poi']:.2f} MW", f"{calc_results['power_inverter']:.2f} MW", f"{calc_results['power_racks']:.2f} MW", f"{calc_results['energy_poi']:.2f} MWh", f"{calc_results['energy_racks']:.2f} MWh", f"{calc_results['rte_bol']:.2f}%", f"{efficiency_total*100:.2f}%", f"{calc_results['derate_factor']*100:.1f}%"]}
    st.dataframe(pd.DataFrame(details), use_container_width=True)
    st.markdown("---")
    equipment = {'Component': ['Enclosures', 'Racks', 'Inverters', 'Transformers'],
                 'Quantity': [calc_results['required_enclosures'], calc_results['required_racks'], calc_results['required_inverters'], calc_results['required_transformers']]}
    st.dataframe(pd.DataFrame(equipment), use_container_width=True)

with tab5:
    st.header("Raw Data Sheets")
    sheet_selector = st.selectbox("Select Sheet:", sheet_names)
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_selector)
        st.info(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        rows_display = st.slider("Rows:", 10, min(500, df.shape[0]), 50)
        cols_display = st.slider("Columns:", 5, min(30, df.shape[1]), 15)
        st.dataframe(df.iloc[:rows_display, :cols_display], use_container_width=True, height=600)
        csv = df.to_csv(index=False)
        st.download_button(f"📥 Download {sheet_selector}", csv, f"{sheet_selector}.csv", "text/csv")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.markdown("<small style='color: #888;'>BESS Tool | Real-time Calculations | Interactive Parameters</small>", unsafe_allow_html=True)
