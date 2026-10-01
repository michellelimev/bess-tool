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

w
