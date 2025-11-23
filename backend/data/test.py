# This file will be used to test the new v3 API structure

import pandas as pd
# from nba_api.stats.endpoints import playbyplayv3   

# # import live playbyplay module
# from nba_api.live.nba.endpoints import playbyplay

# # Replace with a valid game_id to test
# game_id = '0022500248'

# # pbp_df = playbyplayv3.PlayByPlayV3(game_id=game_id).get_data_frames()[0]


# live_pbp = playbyplay.PlayByPlay(game_id=game_id)

# data = live_pbp.get_dict()

# # Extract the list of play actions
# actions = data["game"]["actions"]

# df = pd.DataFrame(actions)

# # print(pbp_df.columns) 
# print(df[['description', 'teamTricode']].head()) 

# from nba_api.stats.static import teams

# # Create empty CSV files for each team
# team_abbrevs = [team['abbreviation'] for team in teams.get_teams()]

# for team in team_abbrevs:
#     df = pd.read_csv("S2\S2_" + team + "_2025_26.csv")

#     # calculate pace with 48 * (poss + opp_poss) / 2 *(minutes_played/5)
#     a = sum(df['possessions'])
#     b = sum(df['opp_possessions'])
#     c = sum(df['minutes_played'])


#     pace = (48 * (a + b) / (2 * (c)))
#     print(team, a,b,c,pace, c/48)



# import pandas as pd
# import ast

# df = pd.read_csv("test_pbp.csv")
# df = df[['shotResult', 'qualifiers']]


# print (df.loc[17])
# print(type(df.loc[17]['qualifiers']))

# df.loc[17, 'qualifiers'] = ast.literal_eval(df.loc[17, 'qualifiers'])

# print(type(df.loc[17, 'qualifiers']), df.loc[17, 'qualifiers'])

# if 'fastbreak' in df.loc[17, 'qualifiers']:
#     print("fastbreak")

# for idx, row in df.iterrows():
#     try:
#         row['qualifiers'] = ast.literal_eval(row['qualifiers'])
#     except:
#         print(idx)
#         pass
#     if 'fastbreak' in row['qualifiers']:
#         print('fastbreak', row['qualifiers'])
#     else:
#         print("not fastbreak", row['qualifiers'])
    
# # convert string to actual list
# df['qualifiers'] = df['qualifiers'].apply(ast.literal_eval)

# # check type
# print(type(df['qualifiers'][0]))  # should be <class 'list'>

# # now iterate safely
# for idx, row in df.iterrows():
#     if 'fastbreak' in row['qualifiers']:
#         print(row)

import requests
import pandas as pd
from typing import List

ESPN_INJURY_URL = "https://www.espn.com/nba/injuries"

class InjuryAPIError(Exception):
    """Custom exception for injury scraping errors."""
    pass

def fetch_espn_injury_tables(timeout: int = 10) -> List[pd.DataFrame]:
    """
    Fetch and parse the injury tables from ESPN's NBA injuries page.

    Returns
    -------
    list[pd.DataFrame]
        List of DataFrames, one per table on the page.

    Raises
    ------
    InjuryAPIError
        If the request fails or no tables are found.
    """
    headers = {
        # Pretend to be a normal Chrome browser on Windows
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.espn.com/nba/"
    }

    try:
        resp = requests.get(ESPN_INJURY_URL, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise InjuryAPIError(f"Error fetching ESPN injuries page: {e}") from e

    try:
        tables = pd.read_html(resp.text)
    except ValueError as e:
        raise InjuryAPIError("No injury tables found on ESPN injuries page") from e

    if not tables:
        raise InjuryAPIError("ESPN injuries page returned no tables")

    return tables

def get_espn_injuries_df(timeout: int = 10) -> pd.DataFrame:
    tables = fetch_espn_injury_tables(timeout=timeout)

    df = pd.concat(tables, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]

    col_map = {
        "TEAM": "Team",
        "PLAYER": "Name",
        "PLAYER NAME": "Name",
        "POS": "Pos",
        "POSITION": "Pos",
        "DATE": "Date",
        "INJURY": "Injury",
        "STATUS": "Status",
    }

    renamed = {}
    for c in df.columns:
        upper = c.upper()
        if upper in col_map:
            renamed[c] = col_map[upper]
    df = df.rename(columns=renamed)

    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].str.strip()

    return df

if __name__ == "__main__":
    try:
        inj_df = get_espn_injuries_df()
        print(inj_df[['NAME', 'Status']].head(15))
        print(inj_df.columns)
    except InjuryAPIError as e:
        print("Failed to fetch injuries:", e)
