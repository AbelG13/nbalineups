## ADD GAME NUMBER

from nba_api.stats.static import teams
import pandas as pd
import os
from itertools import combinations
import ast

# Get list of all NBA team abbreviations (e.g., 'BOS', 'LAL')
team_abbrevs = [team['abbreviation'] for team in teams.get_teams()]

# For each team abbreviation, load and update its CSV
for team_abbr in team_abbrevs:
    save_dir = "S2"
    csv_path = os.path.join(save_dir, f'S2_{team_abbr}_5man_2025_26.csv')

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



# Create or update 2,3,and 4 man lineups

def parse_lineup(lineup_str):
    try:
        # Handle NaN values (pandas might read them as string "nan" or actual NaN)
        if pd.isna(lineup_str) or (isinstance(lineup_str, str) and lineup_str.lower() == 'nan'):
            return None
        raw = ast.literal_eval(lineup_str)
        return tuple(p.strip().strip("'\"") for p in raw)
    except Exception:
        return None

def explode_to_x_man(df, x):
    """
    df: 5-man lineup DataFrame with a 'lineup' column as string
    x: 2, 3, or 4

    Returns: new DataFrame where each original row is duplicated
             for every x-man combo contained in its lineup.
             Only the 'lineup' field changes.
    """
    df = df.copy()
    # parse the original 5-man lineup string into a tuple of players
    df["parsed"] = df["lineup"].map(parse_lineup)

    # for each row, build all x-man combos from the 5 players
    df["x_lineups"] = df["parsed"].apply(
        lambda players: [tuple(sorted(c)) for c in combinations(players, x)] if players and len(players) >= x else []
    )

    # explode: each row → one row per x-man combo
    exploded = df.explode("x_lineups").reset_index(drop=True)

    # Filter out rows where x_lineups is None or empty
    exploded = exploded[exploded["x_lineups"].notna()]

    # replace the lineup column with the x-man combo
    exploded["lineup"] = exploded["x_lineups"].apply(lambda combo: str(combo) if combo else None)

    # drop helper columns
    exploded = exploded.drop(columns=["parsed", "x_lineups"])

    return exploded




for team_abbr in team_abbrevs:

    # save into the S2 folder
    save_dir = "S2"
    csv_path = os.path.join(save_dir, f'S2_{team_abbr}_5man_2025_26.csv')

    # Skip if the CSV doesn't exist (not yet generated from batch runs)
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} as CSV doesn't exist")
        continue

    # Load the full dataset
    df = pd.read_csv(csv_path)

    df2 = explode_to_x_man(df, 2)
    filename2 = f'S2_{team_abbr}_2man_2025_26.csv'
    filepath2 = os.path.join(save_dir, filename2)
    df2.to_csv(filepath2, index=False)
    
    df3 = explode_to_x_man(df, 3)
    filename3 = f'S2_{team_abbr}_3man_2025_26.csv'
    filepath3 = os.path.join(save_dir, filename3)
    df3.to_csv(filepath3, index=False)
    
    df4 = explode_to_x_man(df, 4)
    filename4 = f'S2_{team_abbr}_4man_2025_26.csv'
    filepath4 = os.path.join(save_dir, filename4)
    df4.to_csv(filepath4, index=False)








    

