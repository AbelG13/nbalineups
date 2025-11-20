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



import pandas as pd
import ast

df = pd.read_csv("test_pbp.csv")
# df = df[['shotResult', 'qualifiers']]


# print (df.loc[17])
# print(type(df.loc[17]['qualifiers']))

# df.loc[17, 'qualifiers'] = ast.literal_eval(df.loc[17, 'qualifiers'])

# print(type(df.loc[17, 'qualifiers']), df.loc[17, 'qualifiers'])

# if 'fastbreak' in df.loc[17, 'qualifiers']:
#     print("fastbreak")

for idx, row in df.iterrows():
    try:
        row['qualifiers'] = ast.literal_eval(row['qualifiers'])
    except:
        print(idx)
        pass
    if 'fastbreak' in row['qualifiers']:
        print('fastbreak', row['qualifiers'])
    else:
        print("not fastbreak", row['qualifiers'])
    
# # convert string to actual list
# df['qualifiers'] = df['qualifiers'].apply(ast.literal_eval)

# # check type
# print(type(df['qualifiers'][0]))  # should be <class 'list'>

# # now iterate safely
# for idx, row in df.iterrows():
#     if 'fastbreak' in row['qualifiers']:
#         print(row)
