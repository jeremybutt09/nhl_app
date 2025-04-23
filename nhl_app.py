# Import python packages
import streamlit as st
import requests
import pandas as pd
import logging
from datetime import date  # For defaulting to today's date

# Optional: configure logging level
logging.basicConfig(level=logging.INFO)

# Helpful links (not displayed but useful during development)
helpful_links = [
    "https://docs.streamlit.io",
    "https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit",
    "https://github.com/Snowflake-Labs/snowflake-demo-streamlit",
    "https://docs.snowflake.com/en/release-notes/streamlit-in-snowflake"
]

# Function to fetch game data
def game_data_function():
    try:
        url = "https://api.nhle.com/stats/rest/en/game"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Convert date columns to datetime
        df['gameDate'] = pd.to_datetime(df['gameDate']).dt.date  # Keep only the date part
        df['easternStartTime'] = pd.to_datetime(df['easternStartTime'], format="%Y-%m-%dT%H:%M:%S", errors='coerce')
        
        return df
    except Exception as e:
        logging.error(f"An error occurred while fetching game data: {e}")
        return None

# Streamlit app UI
st.title("NHL Games")

game_df = game_data_function()

if game_df is not None:
    # Date picker - defaults to today
    selected_date = st.date_input("Select game date", value=date.today())

    # Filter DataFrame based on selected date
    filtered_df = game_df[game_df['gameDate'] == selected_date]

    # Show filtered data
    st.write(f"Games on {selected_date}:")
    st.dataframe(filtered_df)
else:
    st.error("Failed to retrieve game data.")
