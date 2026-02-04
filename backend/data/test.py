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

# Import report_data function from report.py
# from report import report_data

# # Input 1
# injuries = pd.read_csv("data/injuries25.csv")["NAME"].tolist()
# print(injuries)
# no_injuries = []
# # Input 2
# injuries_report = report_data(injuries)
# # Input 3
# no_injuries_report = report_data(no_injuries)

# print(injuries_report[['EDGE_1', 'EDGE_2']])
# print(no_injuries_report[['EDGE_1', 'EDGE_2']])


# who played in game 0022500057

# from nba_api.live.nba.endpoints import playbyplay

# game_id = '0022500242'
# pbp_df = pd.DataFrame(playbyplay.PlayByPlay(game_id=game_id).get_dict()["game"]["actions"])

# pbp_df.to_csv('test_pbp.csv', index=False)

# from nba_api.stats.endpoints import scheduleleaguev2

# # Fetch the full 2024–25 NBA schedule
# sched = scheduleleaguev2.ScheduleLeagueV2(
#     league_id='00', 
#     season='2025-26'
# )
# df = sched.get_data_frames()[0]  # 'SeasonGames' table

# # Filter for regular season games
# df_reg = df[df['gameId'].str.startswith('0022')]


# game_ids = df_reg['gameId'].unique().tolist()
# print(game_ids[200:201])
# Create or update 2,3,and 4 man lineups

# from nba_api.stats.static import teams
from nba_api.stats.endpoints import TeamGameLog, LeagueGameLog
# import pandas as pd

# TEAM_ID = 1610612747  # LAL
# gamelog = LeagueGameLog(
#     season="2025-26",
#     league_id="00",
#     player_or_team_abbreviation="T"  # T = teams, P = players
# )

# df = gamelog.get_data_frames()[0]

# def last_5_games(team_abbrev, df):
#     team_abbrev = team_abbrev.upper()

#     team_games = (
#         df[df["TEAM_ABBREVIATION"] == team_abbrev]
#         .sort_values("GAME_DATE", ascending=False)
#         .head(5)
#     )

#     return team_games

# last_5 = last_5_games("LAL", df)



# print(last_5[[
#     "GAME_DATE",
#     "MATCHUP",
#     "WL",
#     "PTS",
#     "PLUS_MINUS"
# ]])


SEASON = '2025-26'
log = LeagueGameLog(
    season=SEASON,
    season_type_all_star="Regular Season",
    player_or_team_abbreviation="P",  # player rows
)
df = log.get_data_frames()[0]
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

df.to_csv('test.csv', index=False)

