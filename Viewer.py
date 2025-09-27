import streamlit as st
import pandas as pd
from DataManager import DataManager
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

st.title("Grind Center - Draft Board")
st.set_page_config(layout="wide")

# --- Dropdown menus ---
seasons = ["20222023", "20232024", "20242025"]  # add all available seasons here
data_types = ['Full', "Ratios", "Totals", "Means", "Deviations"]   # adjust to match what DataManager supports


if "page" not in st.session_state:
    st.session_state.page = "main"
if "selected_player" not in st.session_state:
    st.session_state.selected_player = None


# --- Get data ---
if "dm" not in st.session_state:
    st.session_state.dm = DataManager()

dm = st.session_state.dm






if st.session_state.page == "main":

    col1, col2 = st.columns([1, 2]) 

    with col1:
       showing_type = st.selectbox("Select Data Type", data_types, index=data_types.index("Full"))
    with col2:
        season = st.selectbox("Select Season", seasons, index=seasons.index("20242025"))
    

    if showing_type == 'Full':
        data = dm.get_fullset(season)
    elif showing_type == 'Ratios':
        data = dm.get_ratios(season)
    elif showing_type == "Totals":
        data = dm.get_totals(season)
    elif showing_type == "Means":
        data = dm.get_averages(season)
    elif showing_type == "Deviations":
        data = dm.get_std(season)
    
    df = dm.toCVS(data)
    if 'Picked' not in df.columns:
        df['Picked'] = False
    
    df['Notes'] = df['ID'].map(lambda pid: dm.meta[pid]['note'])


    # Sort so picked players are at the bottom
    df = df.sort_values(by='Picked')

    for col in df.columns:
        if col not in ['Name', 'Notes', 'Pos', 'Team', 'Picked', 'ID']:
            df[col] = df[col].map(lambda v: float(v))

    search_query = st.text_input("Search for player name...")

    # Filter DataFrame by player name (case-insensitive)
    if search_query:
        df = df[df['Name'].str.contains(search_query, case=False, na=False)]

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True, paginationPageSize=100)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=False)
    gb.configure_column("Picked", editable=True, cellEditor='agCheckboxCellEditor')
    gb.configure_column("Notes", hide=True)
    gb.configure_column("ID", hide=True)

    

    # Cross out picked rows using cellStyle on all columns except 'Picked'
    cell_style_jscode = JsCode("""
        function(params) {
            if (params.data['Picked']) {
                return {textDecoration: 'line-through', color: 'gray', backgroundColor: 'black'};
            }                  
            if (params.data['Notes'] != '') {
                if (params.data['Notes'].includes('[DB]')) {
                    return {backgroundColor: 'blue', color: 'white'};
                }
                if (params.data['Notes'].includes('[WARN]')) {
                    return {backgroundColor: 'red', color: 'white'};
                }
                if (params.data['Notes'].includes('[WANT]')) {
                    return {backgroundColor: 'green', color: 'white'};
                }
                if (params.data['Notes'].includes('[WATCH]')) {
                    return {backgroundColor: 'yellow', color: 'grey'};
                }
            }
            return {};
        }
        """)

    for col in df.columns:
        if col not in ['Picked', 'Notes']:
            gb.configure_column(col, cellStyle=cell_style_jscode)

    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        height=2000,
        width=1000,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
    )

    temp = df[df['Notes'].str.contains('[DB]')]
    board = temp[temp['Picked'] == 0]
    st.header("Draft Board")
    draft_board = AgGrid(
        board,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        height=2000,
        width=1000,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
    )


    if grid_response['data'] is not None:
        updated_df = pd.DataFrame(grid_response['data'])
        for _, row in updated_df.iterrows():
            dm.set_pick(row['ID'], row['Picked'])
        dm.save_meta()  # <-- Add this line here

    # If a row is selected
    if grid_response["selected_rows"] is not None and len(grid_response["selected_rows"]) > 0:
        player = grid_response["selected_rows"].iat[0,2]  # Get the full row dict
        st.session_state.selected_player = player
        st.session_state.page = "player"
        dm.save_meta()
        st.rerun()

# --- Player Detail Page ---
elif st.session_state.page == "player":
    if st.button("⬅️ Back to Table"):
        st.session_state.page = "main"
        dm.save_meta()
        st.rerun()

    player = st.session_state.selected_player
    player_info = dm.get_player_bio(player)

    col1, col2 = st.columns([1, 2])  # Adjust ratio as needed

    with col1:
        st.image(player_info['image'], caption=player_info['name'], use_container_width=False, width=200)

    with col2:
        st.header(f"{player_info['name']}")
        st.write(f'Rating: {dm.get_rating(player)}')
        st.write(f"Height: {player_info.get('height', 'N/A')} inches")
        st.write(f"Weight: {player_info.get('weight', 'N/A')} lbs")
        st.write(f"Age: {player_info.get('age', 'N/A')}")

        # Picked checkbox
        picked_key = f"picked_{player}"
        picked = st.checkbox("Picked", value=dm.meta[player]['picked'], key=picked_key)
        dm.set_pick(player, picked)
        dm.save_meta()

    notes_key = f"notes_{player}"
    notes = st.text_area("([WATCH] - add watchlist, [WARN] - add warning flag)", value=dm.meta[player]['note'], key=notes_key)
    dm.set_note(player, notes)
    dm.save_meta()


    showing_type = st.selectbox("Select Data Type", data_types, index=data_types.index("Full"))
    player_data = dm.toCVS(dm.get_player_data(str(player)))  # implement this in DataManager
    st.write(player_data)

    stat_options = [col for col in player_data.columns if col not in ['GP', 'season', 'ID', 'Name', 'Pos', 'Team']]
    selected_stat = st.selectbox("Select stat to graph over time", stat_options, width=500)

    # Plot the stat over seasons
    st.line_chart(player_data.set_index('season')[selected_stat], width=500, use_container_width=False)
