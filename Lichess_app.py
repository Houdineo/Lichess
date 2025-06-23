import streamlit as st
import requests
import json
from collections import defaultdict
import pandas as pd
import altair as alt

#test

st.set_page_config(page_title="Lichess Tournament Stats", layout="centered")
st.title("♟️ Lichess Tournament Stats Viewer")

# Hardcoded API key and performance settings
TOKEN = st.secrets["LICHESS_API_KEY"]
INCLUDE_PERFORMANCE = True

def fetch_tournaments():
    username = st.session_state.username
    if not username:
        st.error("Please enter a Lichess username.")
        return

    url = f"https://lichess.org/api/user/{username}/tournament/played"
    headers = {'Accept': 'application/x-ndjson'}
    params = {'performance': str(INCLUDE_PERFORMANCE).lower()}
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'

    st.info("Fetching tournaments... please wait ⏳")
    response = requests.get(url, headers=headers, params=params, stream=True)

    if response.status_code != 200:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return

    tournaments = []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            tournaments.append(json.loads(line))

    st.success(f"Fetched {len(tournaments)} tournaments.")
    st.session_state['tournaments'] = tournaments

# Text input with on_change callback
st.text_input("Enter your Lichess username:", key='username', on_change=fetch_tournaments)

# Also keep the button as an alternative way to fetch
if st.button("Fetch Tournament Stats"):
    fetch_tournaments()

# Show stats if tournaments are loaded
if 'tournaments' in st.session_state:
    tournaments = st.session_state['tournaments']
    
    # === Overall Summary Statistics ===
    num_total = len(tournaments)
    total_first_place = sum(1 for t in tournaments if t.get('player', {}).get('rank') == 1)
    total_points = sum(t.get('player', {}).get('score', 0) for t in tournaments)

    st.subheader("📊 Overall Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tournaments", num_total)
    col2.metric("1st Place Finishes", total_first_place)
    col3.metric("Total Points", int(total_points))

    # === Group by Tournament Name ===
    grouped = defaultdict(list)
    for t in tournaments:
        name = t.get("tournament", {}).get("fullName", "Unknown")
        grouped[name].append(t)

    # === Categorize tournaments by frequency ===
    def get_frequency(name):
        lname = name.lower()
        if lname.startswith('hourly'):
            return 'hourly'
        elif lname.startswith('daily'):
            return 'daily'
        elif lname.startswith('weekly'):
            return 'weekly'
        elif lname.startswith('monthly'):
            return 'monthly'
        elif lname.startswith('yearly'):
            return 'yearly'
        elif 'shield' in lname:
            return 'shield'
        else:
            return 'other'

    # === Define time control sort order for sub-sorting within frequency groups
    time_control_order = {
        'ultrabullet': 1,
        'hyperbullet': 2,
        'bullet': 3,
        'superblitz': 4,
        'blitz': 5,
        'rapid': 6
    }

    frequency_order = {
        'hourly': 1,
        'daily': 2,
        'weekly': 3,
        'monthly': 4,
        'yearly': 5,
        'shield': 6,
        'other': 7
    }

    def final_sort_key(name):
        lname = name.lower()
        freq = get_frequency(name)
        freq_rank = frequency_order[freq]
    
        for tc, tc_rank in time_control_order.items():
            if tc in lname:
                return (freq_rank, tc_rank, lname)
    
        return (freq_rank, 99999, lname)  # Default to end

    sorted_names = sorted(grouped.keys(), key=final_sort_key)

    # === Selectbox with sorted tournament types
    selected_name = st.selectbox("Select tournament type to view details:", sorted_names)

    group = grouped[selected_name]
    num_played = len(group)
    num_1st = sum(1 for t in group if t.get('player', {}).get('rank') == 1)
    num_2nd = sum(1 for t in group if t.get('player', {}).get('rank') == 2)
    num_3rd = sum(1 for t in group if t.get('player', {}).get('rank') == 3)
    num_podium = sum(1 for t in group if 1 <= t.get('player', {}).get('rank', 9999999) <= 3)
    num_top10 = sum(1 for t in group if 1 <= t.get('player', {}).get('rank', 9999999) <= 10)
    total_points = sum(t.get('player', {}).get('score', 0) for t in group)
    max_points = max(t.get('player', {}).get('score', 0) for t in group) if group else 0
    best_perf = max(
        (int(t.get("player", {}).get("performance")) for t in group if t.get("player", {}).get("performance") is not None),
        default=None
    )

    # Prepare data for points over time chart (only for selected group)
    points_time_data = []
    for t in group:
        timestamp = t.get("tournament", {}).get("startsAt")
        score = t.get("player", {}).get("score", 0)
        if timestamp:
            dt = pd.to_datetime(timestamp, unit='ms')
            points_time_data.append((dt, score))

    # Only show chart if there's valid data
    if points_time_data:
        df_points = pd.DataFrame(points_time_data, columns=["Date", "Points"]).sort_values("Date")
        df_points["Cumulative"] = df_points["Points"].cumsum()

        today = pd.Timestamp.today().normalize()
        start_of_year = pd.Timestamp(today.year, 1, 1)

        st.markdown("### 📈 Points Over Time")
        col1, col2 = st.columns(2)
        with col1:
            preset = st.selectbox("Date range:", [
                "ALL", "1M", "3M", "6M", "YTD", "1Y"
            ])
        with col2:
            view_mode = st.radio("View:", ["Per Tournament", "Cumulative"], horizontal = True)

        if preset == "ALL":
            df_filtered = df_points
        elif preset == "1M":
            df_filtered = df_points[df_points["Date"] >= today - pd.DateOffset(months=1)]
        elif preset == "3M":
            df_filtered = df_points[df_points["Date"] >= today - pd.DateOffset(months=3)]
        elif preset == "6M":
            df_filtered = df_points[df_points["Date"] >= today - pd.DateOffset(months=6)]
        elif preset == "YTD":
            df_filtered = df_points[df_points["Date"] >= start_of_year]
        elif preset == "1Y":
            df_filtered = df_points[df_points["Date"] >= today - pd.DateOffset(years=1)]
        else:
            df_filtered = df_points

        if df_filtered.empty:
            st.warning("No tournaments in selected date range.")
        else:
            y_column = "Cumulative" if view_mode == "Cumulative" else "Points"

            chart = alt.Chart(df_filtered).mark_line().encode(
                x=alt.X("Date:T", title="Date", axis=alt.Axis(format="%Y", labelAngle=0, tickCount="year")),
                y=alt.Y(f"{y_column}:Q", title=y_column),
                tooltip=["Date:T", f"{y_column}:Q"]
            ).properties(
                width=700,
                height=400
            ).interactive()

            st.altair_chart(chart, use_container_width=True)

    st.markdown(f"### 🏆 Stats for {selected_name}")

    # Top row: Played, Max Points, Total Points
    top_row = st.columns(4)

    top_row[0].markdown(
        f"<div style='text-align: center;'>Played<br><span style='font-size: 24px'>{num_played:,}</span></div>",
        unsafe_allow_html=True
    )

    top_row[1].markdown(
        f"<div style='text-align: center; color: purple;'>Max Points<br><span style='font-size: 24px'>{max_points:,}</span></div>",
        unsafe_allow_html=True
    )

    top_row[2].markdown(
        f"<div style='text-align: center; color: teal;'>Best Performance<br><span style='font-size: 24px'>{best_perf if best_perf else 'N/A'}</span></div>",
        unsafe_allow_html=True
    )

    top_row[3].markdown(
        f"<div style='text-align: center;'>Total Points<br><span style='font-size: 24px'>{total_points:,}</span></div>",
        unsafe_allow_html=True
    )

    # Second row: 1st, 2nd, 3rd, Podium, Top 10
    bottom_row = st.columns(5)

    bottom_row[0].markdown(
        f"<div style='text-align: center; color: gold;'>🥇 1st<br><span style='font-size: 24px'>{num_1st:,}</span></div>",
        unsafe_allow_html=True
    )

    bottom_row[1].markdown(
        f"<div style='text-align: center; color: silver;'>🥈 2nd<br><span style='font-size: 24px'>{num_2nd:,}</span></div>",
        unsafe_allow_html=True
    )

    bottom_row[2].markdown(
        f"<div style='text-align: center; color: #cd7f32;'>🥉 3rd<br><span style='font-size: 24px'>{num_3rd:,}</span></div>",
        unsafe_allow_html=True
    )

    bottom_row[3].markdown(
        f"<div style='text-align: center; color: #FF69B4;'>🏅 Podiums<br><span style='font-size: 24px'>{num_podium:,}</span></div>",
        unsafe_allow_html=True
    )

    bottom_row[4].markdown(
        f"<div style='text-align: center; color: #1E90FF;'>Top 🔟<br><span style='font-size: 24px'>{num_top10:,}</span></div>",
        unsafe_allow_html=True
    )
