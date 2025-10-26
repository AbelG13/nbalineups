## ADD GAME NUMBER

from nba_api.stats.static import teams
import pandas as pd
import os

# Get list of all NBA team abbreviations (e.g., 'BOS', 'LAL')
team_abbrevs = [team['abbreviation'] for team in teams.get_teams()]

# For each team abbreviation, load and update its CSV
for team_abbr in team_abbrevs:
    save_dir = "S2"
    csv_path = os.path.join(save_dir, f'S2_{team_abbr}_2025_26.csv')

    # Skip if the CSV doesn't exist (not yet generated from batch runs)
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} as CSV doesn't exist")
        continue

    # Load the full dataset
    df = pd.read_csv(csv_path)

    # Sort and reset index
    df = df.sort_values('game_id').reset_index(drop=True)

    # Map game_id to game_number
    game_id_map = {game_id: i + 1 for i, game_id in enumerate(df['game_id'].unique())}
    df['game_number'] = df['game_id'].map(game_id_map)

    # Save updated CSV
    df.to_csv(csv_path, index=False)


