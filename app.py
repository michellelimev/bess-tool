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
            'cost_per_kw': total_capex / power_mw if power_mw > 0 else 0,
            'cost_per_kwh': total_capex / energy_mwh if energy_mwh > 0 else 0}

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
    'REPT 314Ah 0.25C': {'energy_per_rack':
