# Import python packages
import streamlit as st
import requests
import pandas as pd
import logging  # Make sure to import logging

# Optional: configure logging level
logging.basicConfig(level=logging.INFO)

# Helpful links (not displayed but useful during development)
helpful_links = [
    "https://docs.streamlit.io",
    "https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit",
    "https://github.com/Snowflake-Labs/snowflake-demo-streamlit",
    "https://docs.snowflake.com/en/release-notes/streamlit-in-snowflake"
]

# Function to fetch and return NHL team data
def team_data_function():
    try:
        url = "https://api.nhle.com/stats/rest/en/team"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        df = pd.DataFrame(data)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the team data: {e}")
        return None

# Streamlit app UI
st.title("NHL Team Stats")

team_df = team_data_function()

if team_df is not None:
    team_df = team_df.sort_values(by='franchiseId')
    st.dataframe(team_df)  # This will render the DataFrame in the app
else:
    st.error("Failed to retrieve data.")
