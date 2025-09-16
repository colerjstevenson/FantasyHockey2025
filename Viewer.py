import streamlit as st
import pandas as pd

st.title("📊 Interactive Data Viewer")

# --- Load Data ---
uploaded_file = st.sidebar.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

def detect_encoding(file):
    import chardet
    raw_data = file.read(50000)
    file.seek(0)
    result = chardet.detect(raw_data)
    return result["encoding"]

if uploaded_file is not None:
    # --- Read file ---
    if uploaded_file.name.endswith(".csv"):
        encoding = detect_encoding(uploaded_file)
        df = pd.read_csv(uploaded_file, encoding=encoding)
    else:
        df = pd.read_excel(uploaded_file)

    # --- Initialize crossed-out state ---
    if "crossed" not in st.session_state or len(st.session_state.crossed) != len(df):
        st.session_state.crossed = [False] * len(df)

    st.subheader("Data Table (click column headers to sort)")

    # Display table (sortable via built-in header click)
    st.dataframe(df, use_container_width=True, height=700)

    # Display checkboxes on the left side
    st.subheader("Cross Out Rows")
    for i, row in df.iterrows():
        cols = st.columns([0.1, 0.9])  # narrow column for checkbox, wide for row
        # Checkbox
        crossed = cols[0].checkbox("", value=st.session_state.crossed[i], key=f"cross_{i}")
        st.session_state.crossed[i] = crossed
        # Display row with strike-through if crossed
        row_text = " | ".join([f"~~{v}~~" if crossed else str(v) for v in row])
        cols[1].markdown(row_text)

else:
    st.info("👈 Please upload a CSV or Excel file to get started.")
