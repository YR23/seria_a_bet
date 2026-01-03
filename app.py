import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(page_title="Serie A Predictions", page_icon="⚽", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border: 2px solid #1f77b4;
        border-radius: 10px;
        padding: 20px;
    }

    div[data-testid="stMetric"] label {
        font-size: 2rem !important;
        font-weight: bold !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# API configuration
api_key = "cd6fa0bf318d477b838c0704e282c625"
url = "https://api.football-data.org/v4/competitions/SA/standings"

# Set up headers with API key
headers = {
    "X-Auth-Token": api_key
}

# Function to calculate score
def calculate_score(predicted_position, actual_position):
    """
    Calculate score based on prediction accuracy:
    - 5 points: Exact match for champion (position 1)
    - 4 points: Exact match for non-champion position
    - 2 points: Off by 1 position
    - 1 point: Off by 2 positions
    - 0 points: Off by more than 2 positions
    """
    if predicted_position == actual_position:
        if predicted_position == 1:
            return 5  # Exact champion prediction
        else:
            return 4  # Exact non-champion prediction

    difference = abs(predicted_position - actual_position)

    if difference == 1:
        return 2  # Off by 1
    elif difference == 2:
        return 1  # Off by 2
    else:
        return 0  # Off by more than 2

# Fetch standings
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_standings():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']

        # Create a dictionary mapping team shortName to actual position
        actual_positions = {}
        for entry in table:
            actual_positions[entry['team']['shortName']] = entry['position']

        return actual_positions
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

# Load team mappings
@st.cache_data
def load_team_mappings():
    with open('team_mapping.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Calculate scores for all users
def calculate_all_scores(actual_positions, team_mapping):
    scores = {}

    for user, predictions in team_mapping.items():
        total_score = 0

        for predicted_pos, team_name in predictions.items():
            predicted_pos = int(predicted_pos)
            actual_pos = actual_positions.get(team_name, None)

            if actual_pos is not None:
                score = calculate_score(predicted_pos, actual_pos)
                total_score += score

        scores[user] = total_score

    return scores

# Main app
st.title("⚽ Serie A Predictions Leaderboard")

# Get data
actual_positions = get_standings()
team_mapping = load_team_mappings()

if actual_positions:
    # Calculate scores
    scores = calculate_all_scores(actual_positions, team_mapping)

    # Determine winner
    yamdem_score = scores['Yamdem']
    baruch_score = scores['Baruch']

    if yamdem_score > baruch_score:
        yamdem_emoji = "👑"
        baruch_emoji = "🥈"
    elif baruch_score > yamdem_score:
        yamdem_emoji = "🥈"
        baruch_emoji = "👑"
    else:
        yamdem_emoji = "🤝"
        baruch_emoji = "🤝"

    # Display scores in columns
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label=f"{yamdem_emoji} Yamdem",
            value=f"{yamdem_score} points"
        )

    with col2:
        st.metric(
            label=f"{baruch_emoji} Baruch",
            value=f"{baruch_score} points"
        )

    # Create detailed table
    st.markdown("---")
    st.subheader("📊 Detailed Predictions Table")

    # Create reverse mappings (team -> position predicted)
    yamdem_reverse = {v: int(k) for k, v in team_mapping['Yamdem'].items()}
    baruch_reverse = {v: int(k) for k, v in team_mapping['Baruch'].items()}

    # Build table data
    table_data = []
    for position in range(1, 9):  # Positions 1-8
        # Find actual team in this position
        actual_team = None
        for team, pos in actual_positions.items():
            if pos == position:
                actual_team = team
                break

        if actual_team:
            # Yamdem's prediction for this position
            yamdem_bet_team = team_mapping['Yamdem'].get(str(position), "N/A")
            yamdem_predicted_pos = yamdem_reverse.get(actual_team, "N/A")
            yamdem_predicted_pos_str = f"{yamdem_predicted_pos}" if yamdem_predicted_pos != "N/A" else "N/A"
            # Calculate points based on where they predicted the actual team would finish
            if yamdem_predicted_pos != "N/A":
                yamdem_points = calculate_score(yamdem_predicted_pos, position)
            else:
                yamdem_points = 0

            # Baruch's prediction for this position
            baruch_bet_team = team_mapping['Baruch'].get(str(position), "N/A")
            baruch_predicted_pos = baruch_reverse.get(actual_team, "N/A")
            baruch_predicted_pos_str = f"{baruch_predicted_pos}" if baruch_predicted_pos != "N/A" else "N/A"
            # Calculate points based on where they predicted the actual team would finish
            if baruch_predicted_pos != "N/A":
                baruch_points = calculate_score(baruch_predicted_pos, position)
            else:
                baruch_points = 0

            table_data.append({
                "Position": position,
                "Actual Team": actual_team,
                "Yamdem Bet": yamdem_bet_team,
                "Yamdem Actual Team Bet": yamdem_predicted_pos_str,
                "Yamdem Points": yamdem_points,
                "Baruch Bet": baruch_bet_team,
                "Baruch Actual Team Bet": baruch_predicted_pos_str,
                "Baruch Points": baruch_points
            })

    import pandas as pd
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
