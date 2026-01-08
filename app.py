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
def get_standings():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']

        # Create a dictionary mapping team shortName to actual position
        actual_positions = {}
        team_crests = {}
        for entry in table:
            actual_positions[entry['team']['shortName']] = entry['position']
            team_crests[entry['team']['shortName']] = entry['team']['crest']

        return actual_positions, table, team_crests
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None, None, None

# Load team mappings
def load_team_mappings():
    with open('team_mapping.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Fetch upcoming fixtures
def get_upcoming_fixtures():
    fixtures_url = "https://api.football-data.org/v4/competitions/SA/matches"
    params = {"status": "SCHEDULED"}
    response = requests.get(fixtures_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        matches = data.get('matches', [])

        # Group matches by matchday and get the next matchday
        if matches:
            next_matchday = matches[0]['season']['currentMatchday'] + 1
            next_round_matches = [m for m in matches if m['matchday'] == next_matchday]
            return next_round_matches[:10]  # Limit to 10 matches
        return []
    else:
        st.error(f"Error fetching fixtures: {response.status_code}")
        return []

# Fetch last round results
def get_last_round_results():
    fixtures_url = "https://api.football-data.org/v4/competitions/SA/matches"
    params = {"status": "FINISHED"}
    response = requests.get(fixtures_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        matches = data.get('matches', [])

        # Get the most recent matchday
        if matches:
            last_matchday = matches[-1]['season']['currentMatchday']
            last_round_matches = [m for m in matches if m['matchday'] == last_matchday]
            return last_round_matches[:10]  # Limit to 10 matches
        return []
    else:
        st.error(f"Error fetching last round results: {response.status_code}")
        return []

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
actual_positions, full_table, team_crests = get_standings()
team_mapping = load_team_mappings()

if actual_positions and full_table:
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

    # Create detailed predictions display
    st.markdown("---")
    st.subheader("📊 Detailed Predictions")

    import pandas as pd

    # Function to format status
    def format_status(predicted_pos, actual_pos):
        difference = actual_pos - predicted_pos

        if difference == 0:
            return "✓ EXACT!"
        elif difference > 0:
            return f"↓ (actual: {actual_pos}, diff: +{difference})"
        else:
            return f"↑ (actual: {actual_pos}, diff: {difference})"

    # Build predictions data for both users
    def build_predictions_table(user_name):
        predictions_data = []
        for predicted_pos in range(1, 9):
            team_name = team_mapping[user_name].get(str(predicted_pos), "N/A")
            if team_name != "N/A":
                actual_pos = actual_positions.get(team_name, None)
                if actual_pos is not None:
                    score = calculate_score(predicted_pos, actual_pos)
                    status = format_status(predicted_pos, actual_pos)
                    crest = team_crests.get(team_name, "")
                    # Create team display with logo
                    team_display = f'<img src="{crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {team_name}'
                    predictions_data.append({
                        "Position": f"Position {predicted_pos}",
                        "Team": team_display,
                        "Result": status,
                        "Score": score
                    })
        return pd.DataFrame(predictions_data)

    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {yamdem_emoji} Yamdem's Predictions")
        yamdem_df = build_predictions_table('Yamdem')

        # Apply styling to the dataframe
        def highlight_exact(row):
            if "EXACT" in str(row['Result']):
                return ['background-color: #90EE90'] * len(row)
            return [''] * len(row)

        styled_yamdem = yamdem_df.style.apply(highlight_exact, axis=1)
        st.write(styled_yamdem.to_html(escape=False), unsafe_allow_html=True)
        st.markdown(f"### **TOTAL SCORE: {yamdem_score} points**")

    with col2:
        st.markdown(f"### {baruch_emoji} Baruch's Predictions")
        baruch_df = build_predictions_table('Baruch')

        styled_baruch = baruch_df.style.apply(highlight_exact, axis=1)
        st.write(styled_baruch.to_html(escape=False), unsafe_allow_html=True)
        st.markdown(f"### **TOTAL SCORE: {baruch_score} points**")

    # Display current Serie A standings
    st.markdown("---")
    st.subheader("📋 Current Serie A Standings (Top 10)")

    standings_data = []
    for entry in full_table[:10]:  # Get top 10
        crest = entry['team']['crest']
        team_name = entry['team']['shortName']
        team_display = f'<img src="{crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {team_name}'
        standings_data.append({
            "Position": entry['position'],
            "Team": team_display,
            "Games": entry['playedGames'],
            "Goal Diff": entry['goalDifference'],
            "Points": entry['points']
        })

    standings_df = pd.DataFrame(standings_data)
    st.write(standings_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Display last round results
    st.markdown("---")
    st.subheader("⚽ Last Round Results")

    last_results = get_last_round_results()
    if last_results:
        results_data = []
        for match in last_results:
            home_team = match['homeTeam']['shortName']
            away_team = match['awayTeam']['shortName']
            home_crest = match['homeTeam']['crest']
            away_crest = match['awayTeam']['crest']
            home_score = match['score']['fullTime']['home']
            away_score = match['score']['fullTime']['away']
            match_date = match['utcDate']

            # Format date
            from datetime import datetime
            dt = datetime.strptime(match_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = dt.strftime("%b %d")

            # Create team displays with logos
            home_display = f'<img src="{home_crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {home_team}'
            away_display = f'<img src="{away_crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {away_team}'

            results_data.append({
                "Date": formatted_date,
                "Home": home_display,
                "Score": f"{home_score} - {away_score}",
                "Away": away_display
            })

        results_df = pd.DataFrame(results_data)
        st.write(results_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No recent results available.")

    # Display upcoming fixtures
    st.markdown("---")
    st.subheader("📅 Next Round Fixtures")

    fixtures = get_upcoming_fixtures()
    if fixtures:
        fixtures_data = []
        for match in fixtures:
            home_team = match['homeTeam']['shortName']
            away_team = match['awayTeam']['shortName']
            home_crest = match['homeTeam']['crest']
            away_crest = match['awayTeam']['crest']
            match_date = match['utcDate']

            # Format date
            from datetime import datetime
            dt = datetime.strptime(match_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = dt.strftime("%b %d, %H:%M")

            # Create team displays with logos
            home_display = f'<img src="{home_crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {home_team}'
            away_display = f'<img src="{away_crest}" width="20" height="20" style="vertical-align: middle; margin-right: 5px;"> {away_team}'

            fixtures_data.append({
                "Date & Time": formatted_date,
                "Home": home_display,
                "vs": "vs",
                "Away": away_display
            })

        fixtures_df = pd.DataFrame(fixtures_data)
        st.write(fixtures_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No upcoming fixtures available.")
