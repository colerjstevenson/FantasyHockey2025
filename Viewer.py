import streamlit as st
import pandas as pd

from DataManager import DataManager 


st.title("📊 Interactive Data Viewer")

showing_type = "Ratios"
season = '20242025'

dm = DataManager()

df = dm.toCVS(dm.get_fullset(season)).sort_values(by='Rating', ascending=False)




st.subheader("Data Table (click column headers to sort)")

# Display table (sortable via built-in header click)
st.dataframe(df, use_container_width=True, height=900)

