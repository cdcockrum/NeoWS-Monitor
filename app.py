# app.py
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from fetch import fetch_asteroid_data

# App title and description
st.title("\U0001F320 NASA Near-Earth Objects Tracker")
st.markdown("""
This application uses NASA's NeoWs (Near Earth Object Web Service) API to retrieve and visualize 
information about asteroids and other near-Earth objects.
""")

# Date selection
st.sidebar.header("Search Parameters")
today = datetime.now()
default_start_date = today.date()
default_end_date = (today + timedelta(days=7)).date()

start_date = st.sidebar.date_input("Start Date", default_start_date)
end_date = st.sidebar.date_input("End Date", default_end_date)

# Validate date range
date_diff = (end_date - start_date).days
if date_diff > 7:
    st.warning("\u26a0\ufe0f NASA API limits date range to 7 days or less. Adjusting to a 7-day period.")
    end_date = start_date + timedelta(days=7)

# Search button
if st.sidebar.button("Search Asteroids"):
    data = fetch_asteroid_data(start_date, end_date)

    if data:
        st.session_state.asteroid_data = data
        st.session_state.searched = True
    else:
        st.error("Failed to fetch asteroid data. Please check your environment setup.")

# Display results if search was performed
if 'searched' in st.session_state and st.session_state.searched:
    data = st.session_state.asteroid_data
    element_count = data.get('element_count', 0)
    st.success(f"Found {element_count} near-Earth objects between {start_date} and {end_date}")

    neo_data = data.get('near_earth_objects', {})
    all_asteroids = []

    for date, asteroids in neo_data.items():
        for asteroid in asteroids:
            if not asteroid['close_approach_data']:
                continue

            asteroid_info = {
                'id': asteroid['id'],
                'name': asteroid['name'],
                'date': date,
                'diameter_min_km': asteroid['estimated_diameter']['kilometers']['estimated_diameter_min'],
                'diameter_max_km': asteroid['estimated_diameter']['kilometers']['estimated_diameter_max'],
                'is_hazardous': asteroid['is_potentially_hazardous_asteroid'],
                'close_approach_date': asteroid['close_approach_data'][0]['close_approach_date'],
                'miss_distance_km': float(asteroid['close_approach_data'][0]['miss_distance']['kilometers']),
                'relative_velocity_kph': float(asteroid['close_approach_data'][0]['relative_velocity']['kilometers_per_hour'])
            }
            all_asteroids.append(asteroid_info)

    df = pd.DataFrame(all_asteroids)
    df['avg_diameter_km'] = (df['diameter_min_km'] + df['diameter_max_km']) / 2

    st.header("Summary Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Asteroids", len(df))
    with col2:
        hazardous_count = df['is_hazardous'].sum()
        st.metric("Potentially Hazardous", f"{hazardous_count} ({hazardous_count/len(df)*100:.1f}%)")
    with col3:
        st.metric("Avg. Size", f"{df['avg_diameter_km'].mean():.2f} km")

    st.header("Visualizations")
    viz_tab1, viz_tab2 = st.tabs(["Size Distribution", "Miss Distance"])
    with viz_tab1:
        fig1 = px.histogram(
            df, x="avg_diameter_km", color="is_hazardous",
            title="Size Distribution of Near-Earth Objects",
            labels={"avg_diameter_km": "Average Diameter (km)", "is_hazardous": "Potentially Hazardous"},
            color_discrete_map={True: "red", False: "green"}
        )
        st.plotly_chart(fig1, use_container_width=True)
    with viz_tab2:
        fig2 = px.scatter(
            df, x="miss_distance_km", y="avg_diameter_km", color="is_hazardous",
            size="relative_velocity_kph", hover_name="name",
            title="Miss Distance vs. Size (with velocity)",
            labels={
                "miss_distance_km": "Miss Distance (km)",
                "avg_diameter_km": "Average Diameter (km)",
                "is_hazardous": "Potentially Hazardous",
                "relative_velocity_kph": "Velocity (km/h)"
            },
            color_discrete_map={True: "red", False: "green"}
        )
        fig2.update_layout(xaxis_type="log")
        st.plotly_chart(fig2, use_container_width=True)

    st.header("Detailed Asteroid Data")
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    with col1:
        show_hazardous = st.checkbox("Show only hazardous asteroids", False)
    with col2:
        size_threshold = st.slider("Minimum size (km)", 0.0, max(df['avg_diameter_km']), 0.0, 0.01)

    filtered_df = df.copy()
    if show_hazardous:
        filtered_df = filtered_df[filtered_df['is_hazardous'] == True]
    filtered_df = filtered_df[filtered_df['avg_diameter_km'] >= size_threshold]

    sort_by = st.selectbox("Sort by", [
        "close_approach_date", "name", "avg_diameter_km", "miss_distance_km", "relative_velocity_kph"])
    sort_order = st.radio("Sort order", ["Ascending", "Descending"], horizontal=True)
    ascending = sort_order == "Ascending"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    display_df = filtered_df[[
        'name', 'close_approach_date', 'avg_diameter_km', 
        'miss_distance_km', 'relative_velocity_kph', 'is_hazardous'
    ]].rename(columns={
        'name': 'Name',
        'close_approach_date': 'Approach Date',
        'avg_diameter_km': 'Diameter (km)',
        'miss_distance_km': 'Miss Distance (km)',
        'relative_velocity_kph': 'Velocity (km/h)',
        'is_hazardous': 'Hazardous'
    })
    st.dataframe(display_df, use_container_width=True)

    st.subheader("Individual Asteroid Details")
    selected_asteroid = st.selectbox("Select an asteroid", filtered_df['name'].tolist())
    if selected_asteroid:
        asteroid_details = filtered_df[filtered_df['name'] == selected_asteroid].iloc[0]
        st.subheader(f"\U0001F311 {selected_asteroid}")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**ID:**", asteroid_details['id'])
            st.write("**Approach Date:**", asteroid_details['close_approach_date'])
            st.write("**Hazardous:**", "Yes \u26a0\ufe0f" if asteroid_details['is_hazardous'] else "No \u2713")
        with col2:
            st.write("**Diameter Range:**", f"{asteroid_details['diameter_min_km']:.3f} - {asteroid_details['diameter_max_km']:.3f} km")
            st.write("**Miss Distance:**", f"{asteroid_details['miss_distance_km']:,.0f} km")
            st.write("**Relative Velocity:**", f"{asteroid_details['relative_velocity_kph']:,.0f} km/h")

        hazard_level = 0
        if asteroid_details['is_hazardous']:
            size_factor = min(asteroid_details['avg_diameter_km'] / 0.5, 1)
            distance_factor = min(1000000 / asteroid_details['miss_distance_km'], 1)
            hazard_level = (size_factor * 0.7 + distance_factor * 0.3) * 100
        st.progress(int(hazard_level), text=f"Relative Hazard Level: {hazard_level:.1f}%")

        st.write("### Context")
        if hazard_level > 70:
            st.warning("This asteroid is classified as potentially hazardous and is relatively large and close.")
        elif hazard_level > 40:
            st.info("This asteroid is classified as potentially hazardous but poses minimal risk at this time.")
        else:
            st.success("This asteroid is not considered hazardous and poses no risk to Earth.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About NASA NeoWs API
The [Near Earth Object Web Service](https://api.nasa.gov) provides asteroid data based on closest approach to Earth.
To get an API key, visit [api.nasa.gov](https://api.nasa.gov).
""")

