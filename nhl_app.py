import streamlit as st
import requests
import pandas as pd
import numpy as np
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
        df = pd.DataFrame(data)
        df.rename(columns={'id': 'teamId'}, inplace=True)
        return df
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
        df.rename(columns={'id': 'gameId'}, inplace=True)
        return df
    except Exception as e:
        logging.error(f"An error occurred while fetching game data: {e}")
        return None

def enrich_with_team_names(df, team_df):
    # Merge home team
    df = df.merge(team_df[['teamId', 'fullName', 'rawTricode']], how='left', left_on='homeTeamId', right_on='teamId')
    df.rename(columns={'fullName': 'homeTeamFullName', 'rawTricode': 'homeTeamAbrv'}, inplace=True)
    df.drop(columns=['teamId'], inplace=True, errors='ignore')  # Safe drop

    # Merge visiting team
    df = df.merge(team_df[['teamId', 'fullName', 'rawTricode']], how='left', left_on='visitingTeamId', right_on='teamId')
    df.rename(columns={'fullName': 'visitingTeamFullName', 'rawTricode': 'visitingTeamAbrv'}, inplace=True)
    df.drop(columns=['teamId'], inplace=True, errors='ignore')  # Safe drop

    return df

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


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

        # Get list of gameIds from filtered dataframe
        game_ids = list(filtered_df['gameId'])
        
        # Initialize rows for clock/period data
        rows = []
        
        # Fetch data for each gameId
        for game_id in game_ids:
            try:
                url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
        
                row = {
                    "gameId": game_id,
                    "timeRemaining": data.get("clock", {}).get("timeRemaining"),
                    "periodNumber": data.get("periodDescriptor", {}).get("number"),
                    "periodType": data.get("periodDescriptor", {}).get("periodType"),
                    "gameOutcome": data.get("gameOutcome", {})
                }
                rows.append(row)
            except Exception as e:
                logging.warning(f"Failed to fetch data for gameId {game_id}: {e}")
        
        # Create DataFrame from clock/period data
        period_df = pd.DataFrame(rows)
        
        # Format period output
        def format_period_output(row):
            if row["timeRemaining"] is None or row["periodNumber"] is None:
                return None
            if row['gameOutcome']:
                return 'Final'
            elif 1 <= row['periodNumber'] <= 3:
                return f"{row['timeRemaining']} {ordinal(row['periodNumber'])}"
            elif row['periodNumber'] > 3:
                overtime_number = row['periodNumber'] - 3
                return f"{row['timeRemaining']} {overtime_number}{row['periodType']}"
            else:
                return None
        
        period_df['periodOutput'] = period_df.apply(format_period_output, axis=1)
        
        # Merge Period Output into filtered_df
        filtered_df = filtered_df.merge(period_df[['gameId', 'periodOutput']], on='gameId', how='left')

        # Optional: Select and reorder columns to display
        display_cols = [
            'easternStartTime', 'periodOutput',
            'visitingTeamFullName', 'visitingScore',
            'homeTeamFullName', 'homeScore'
        ]
        display_df = filtered_df[display_cols] if all(col in filtered_df.columns for col in display_cols) else filtered_df

        display_df.rename(columns={'easternStartTime': 'Game Date', 
                                   'periodOutput': 'Period',
                                   'visitingTeamFullName': 'Visiting Team', 
                                   'visitingScore': 'Visiting Score', 
                                   'homeTeamFullName': 'Home Team',
                                   'homeScore': 'Home Score'}, inplace=True)

        # st.dataframe(period_df)
        # st.dataframe(filtered_df)
        st.dataframe(display_df, use_container_width = True, hide_index = True)
    else:
        st.warning(f"No games scheduled for {selected_date}.")
