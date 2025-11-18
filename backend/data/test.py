# This file will be used to test the new v3 API structure

import pandas as pd
from nba_api.stats.endpoints import playbyplayv3   

# import live playbyplay module
from nba_api.live.nba.endpoints import playbyplay

# Replace with a valid game_id to test
game_id = '0022500248'

# pbp_df = playbyplayv3.PlayByPlayV3(game_id=game_id).get_data_frames()[0]


live_pbp = playbyplay.PlayByPlay(game_id=game_id)

data = live_pbp.get_dict()

# Extract the list of play actions
actions = data["game"]["actions"]

df = pd.DataFrame(actions)

# print(pbp_df.columns) 
print(df[['description', 'teamTricode']].head()) 

