import requests
import pandas as pd
import json

# API configuration
api_key = "cd6fa0bf318d477b838c0704e282c625"
url = "https://api.football-data.org/v4/competitions/SA/standings"

# Set up headers with API key
headers = {
    "X-Auth-Token": api_key
}

# Make the GET request
response = requests.get(url, headers=headers)

# Check if request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Extract the standings table
    table = data['standings'][0]['table']

    # Create a dictionary mapping team shortName to actual position
    actual_positions = {}
    for entry in table:
        actual_positions[entry['team']['shortName']] = entry['position']

    # Load team mappings
    with open('team_mapping.json', 'r', encoding='utf-8') as f:
        team_mapping = json.load(f)

    # Scoring function
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

    # Calculate scores for each user
    print("=" * 60)
    print("SERIA A PREDICTION SCORES")
    print("=" * 60)

    for user, predictions in team_mapping.items():
        print(f"\n{user}'s Predictions:")
        print("-" * 60)
        total_score = 0

        for predicted_pos, team_name in predictions.items():
            predicted_pos = int(predicted_pos)
            actual_pos = actual_positions.get(team_name, None)

            if actual_pos is None:
                print(f"  Position {predicted_pos}: {team_name} - NOT FOUND")
                continue

            score = calculate_score(predicted_pos, actual_pos)
            total_score += score

            # Display result
            difference = actual_pos - predicted_pos
            if difference == 0:
                status = "✓ EXACT!"
            elif difference > 0:
                status = f"↓ (actual: {actual_pos}, diff: +{difference})"
            else:
                status = f"↑ (actual: {actual_pos}, diff: {difference})"

            print(f"  Position {predicted_pos}: {team_name:12} {status:30} Score: {score}")

        print("-" * 60)
        print(f"  TOTAL SCORE: {total_score} points")
        print()

    print("=" * 60)

else:
    print(f"Error: {response.status_code}")
    print(response.text)
