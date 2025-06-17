import os
import requests
from datetime import datetime
import streamlit as st

def fetch_asteroid_data(start_date: datetime, end_date: datetime):
    api_key = os.getenv("NASA_API_KEY")
    if not api_key:
        st.error("NASA_API_KEY is not set as an environment variable.")
        st.stop()

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "api_key": api_key
    }

    with st.spinner("Fetching asteroid data from NASA..."):
        try:
            response = requests.get("https://api.nasa.gov/neo/rest/v1/feed", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error accessing NASA API: {e}")
            return None
