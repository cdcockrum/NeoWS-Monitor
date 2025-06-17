# visuals.py
import plotly.express as px
import streamlit as st
import pandas as pd

def render_summary(df: pd.DataFrame):
    st.header("Summary Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Asteroids", len(df))
    with col2:
        hazardous_count = df['is_hazardous'].sum()
        st.metric("Potentially Hazardous", f"{hazardous_count} ({hazardous_count/len(df)*100:.1f}%)")
    with col3:
        st.metric("Avg. Size", f"{df['avg_diameter_km'].mean():.2f} km")

def render_visualizations(df: pd.DataFrame):
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
