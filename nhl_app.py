# Import python packages
import streamlit as st
import requests
import pandas as pd

helpful_links = [
    "https://docs.streamlit.io",
    "https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit",
    "https://github.com/Snowflake-Labs/snowflake-demo-streamlit",
    "https://docs.snowflake.com/en/release-notes/streamlit-in-snowflake"
]

def team_data_function():
    try:
        # URL for the game data
        url = "https://api.nhle.com/stats/rest/en/team"
        response = requests.get(url)
        response.raise_for_status()

        # Extract data
        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        return df

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the team data: {e}")
        return None
    
team_df = team_data_function().sort_values(by = 'franchiseId')
