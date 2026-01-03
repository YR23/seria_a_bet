import requests
import pandas as pd

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
    print("Success! Here are the standings:")
    print("-" * 50)

    # Parse the JSON response
    data = response.json()

    # Extract the standings table
    table = data['standings'][0]['table']

    # Create a list of dictionaries with the desired columns
    standings_data = []
    for entry in table:
        standings_data.append({
            'position': entry['position'],
            'shortName': entry['team']['shortName'],
            'points': entry['points'],
            'crest': entry['team']['crest']
        })

    # Create DataFrame
    df = pd.DataFrame(standings_data)

    # Print the DataFrame
    print(df)
else:
    print(f"Error: {response.status_code}")
    print(response.text)