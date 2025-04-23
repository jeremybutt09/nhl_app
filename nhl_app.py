import streamlit as st
import requests
import pandas as pd
import logging
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to fetch NHL team data
def team_data_function():
    try:
        url = "https://api.nhle.com/stats/rest/en/team"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the team data: {e}")
        return None

# Function to fetch NHL game data
def game_data_function():
    try:
        url = "https://api.nhle.com/stats/rest/en/game"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        df['gameDate'] = pd.to_datetime(df['gameDate']).dt.date
        df['easternStartTime'] = pd.to_datetime(df['easternStartTime'], errors='coerce')
        return df
    except Exception as e:
        logging.error(f"An error occurred while fetching game data: {e}")
        return None

def enrich_with_team_names(df, team_df):
    # Merge home team
    df = df.merge(team_df[['id', 'fullName', 'rawTricode']], how='left', left_on='homeTeamId', right_on='id')
    df.rename(columns={'fullName': 'homeTeamFullName', 'rawTricode': 'homeTeamAbrv'}, inplace=True)
    #df.drop(columns=['id'], inplace=True, errors='ignore')  # Safe drop

    # Merge visiting team
    df = df.merge(team_df[['id', 'fullName', 'rawTricode']], how='left', left_on='visitingTeamId', right_on='id')
    df.rename(columns={'fullName': 'visitingTeamFullName', 'rawTricode': 'visitingTeamAbrv'}, inplace=True)
    #df.drop(columns=['id'], inplace=True, errors='ignore')  # Safe drop

    return df

# Streamlit UI
st.title("NHL Games")

# Load data
team_df = team_data_function()
game_df = game_data_function()

if team_df is None:
    st.error("Failed to retrieve team data.")
elif game_df is None:
    st.error("Failed to retrieve game data.")
else:
    selected_date = st.date_input("Select game date", value=date.today())
    filtered_df = game_df[game_df['gameDate'] == selected_date].copy()

    if not filtered_df.empty:
        filtered_df = enrich_with_team_names(filtered_df, team_df)

        # Optional: Select and reorder columns to display
        display_cols = [
            'gameId', 'gameDate', 'easternStartTime',
            'homeTeamFullName', 'homeTeamAbrv',
            'visitingTeamFullName', 'visitingTeamAbrv',
            'homeTeamScore', 'visitingTeamScore'
        ]
        display_df = filtered_df[display_cols] if all(col in filtered_df.columns for col in display_cols) else filtered_df

        st.dataframe(display_df)
    else:
        st.warning(f"No games scheduled for {selected_date}.")
