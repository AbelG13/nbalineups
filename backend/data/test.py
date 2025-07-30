from nba_api.stats.endpoints import playbyplayv2, boxscoretraditionalv2, boxscoretraditionalv3
import pandas as pd
from nba_api.stats.endpoints import scheduleleaguev2
from nba_api.stats.static import teams
import time
import random
import numpy as np
import unicodedata
import os

#time how long it takes to run
time_start = time.time()
def infer_lineup_for_team(start_index, pbp_df, team_players, team_side, max_lookahead=150):
    """
    Infer the lineup (5 players) on the court at the start of a quarter for a single team.

    Args:
        start_index: index in pbp_df where the quarter starts (EVENTMSGTYPE == 12).
        pbp_df: play-by-play DataFrame.
        team_players: list of all players on the team (from box score).
        team_side: 'home' or 'away'
        max_lookahead: how many rows to check after quarter start

    Returns:
        on_court: list of 5 players inferred to be on the court
    """
    on = set()
    off = set()

    for i in range(start_index, min(start_index + max_lookahead, len(pbp_df))):
        row = pbp_df.iloc[i]

        # Ignore events with no team description on this side
        description = row['HOMEDESCRIPTION'] if team_side == 'home' else row['VISITORDESCRIPTION']
        if pd.isna(description):
            continue

        # UPDATED
        # If row is a foul with na player 2, skip the event
        if row['EVENTMSGTYPE'] == 6 and pd.isna(row['PLAYER2_NAME']):
            continue

        # Substitution event
        if row['EVENTMSGTYPE'] == 8:
            player_out = row['PLAYER1_NAME']
            player_in = row['PLAYER2_NAME']
            # Only consider subs for this team
            if player_out in team_players or player_in in team_players:
                if player_out and player_out not in on and player_out not in off:
                    on.add(player_out)
                if player_in and player_in not in on and player_in not in off:
                    off.add(player_in)

        else:
            # UPDATED
            players = [row['PLAYER1_NAME'], row['PLAYER2_NAME'], row['PLAYER3_NAME']]
            
            # # Debugging.. remove accent marks from names in pbp
            # players = [
            #     unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII') if isinstance(name, str) else name
            #     for name in players
            # ]
            for player in players:
                if pd.isna(player):
                    continue
                if player in team_players:
                    if player not in on:
                        if player not in off:
                            on.add(player)

        if len(on) == 5:
            break

    if len(on) < 5:
        if game_id == '0022400223': 
            on.add('Tobais Harris')
        elif game_id == '0022400230':
            on.add('Gradey Dick')
        elif game_id == '0022400290':
            on.add('Dillon Brooks')
        elif game_id == '0022400762':
            on.add('Zach Lavine')
        elif game_id == '0022400771':
            on.add('Corey Kispert')
        elif game_id == '0022400903':
            on.add('Dorian Finney-Smith')
        elif game_id == '0022400985':
            on.add('Justin Edwards')
        elif game_id == '0022401102':
            on.add('Peyton Watson')
        elif game_id == '0022401131':
            on.add('Alec Burks')
        elif game_id == '0022401162':
            on.add('Jaden Springer')
        elif game_id == '0022400679':
            on.add('Josh Green')
        elif game_id == '0022400031':
            on.add('Tazé Moore')
        else:
            print(f"[⚠️ Warning : {start_index}] Could not infer full lineup for {team_side} (found {len(list(on))} players), {row['GAME_ID']}, FINAL SCORE: {home_team} {away_team} {pbp_df.iloc[-1]['SCORE']}")
            print(list(on))

    return list(on)

# Fetch the full 2024–25 NBA schedule
sched = scheduleleaguev2.ScheduleLeagueV2(
    league_id='00', 
    season='2024-25'
)
df = sched.get_data_frames()[0]  # 'SeasonGames' table

# Filter for regular season games
df_reg = df[df['gameId'].str.startswith('0022')]

game_ids = df_reg['gameId'].unique().tolist()


# Get all NBA teams
nba_teams_data = teams.get_teams()

# Extract abbreviations
team_abbreviations = [team['abbreviation'] for team in nba_teams_data]

# Fields for lineup stats
stat_fields = [
    'game_id', 'lineup', 'period', 'points', 'opp_points',
    'rebounds', 'opp_rebounds', 'assists', 'opp_assists',
    'turnovers', 'opp_turnovers', 'fouls_committed', 'fouls_drawn'
]

# Create the dictionary
team_lineup_stats = {
    team: pd.DataFrame(columns=stat_fields)
    for team in team_abbreviations
}
count = 0
for idx,id in enumerate(game_ids[1250:]):
    
    # Load game
    game_id = id
    for attempt in range(3):
        try:
            pbp_df = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
            box_df = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id).get_data_frames()[0]
            box_df['full_name'] = box_df['firstName'] + ' ' + box_df['familyName']
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for game {game_id}: {str(e)}")
            time.sleep(int(np.random.choice([21, 33,42])))

    # Debug.. rows are in wrong order
    if game_id == "0022400316":
        # Special fix: swap the event numbers
        row_188 = pbp_df[pbp_df['EVENTNUM'] == 188]
        row_191 = pbp_df[pbp_df['EVENTNUM'] == 191]

        # Drop them from the DataFrame
        pbp_df = pbp_df[~pbp_df['EVENTNUM'].isin([188, 191])]

        # Append them in the desired order (substitution before rebound)
        pbp_df = pd.concat([pbp_df, row_188, row_191], ignore_index=True)

        # Optional: sort by EVENTNUM or reset index
        pbp_df = pbp_df.sort_values(by='EVENTNUM').reset_index(drop=True)

    # avoid rate limits
    if idx % 1 == 0:
        if idx%25 == 0:
            print(idx)
        time.sleep(1)

    # Build player-to-team map
    player_team_map = dict(zip(box_df['full_name'], box_df['teamTricode']))

    teams = box_df['teamTricode'].unique()
    try:
        home_team = teams[1]
        away_team = teams[0]
    except:
        print(f"[⚠️ Warning : {game_id}] Could not resolve teams, {game_id}")
        # print(teams)
        continue

    # Get starters
    home_starters = box_df[(box_df['teamTricode'] == home_team) & (box_df['position'].notnull())].head(5)['full_name'].tolist()
    away_starters = box_df[(box_df['teamTricode'] == away_team) & (box_df['position'].notnull())].head(5)['full_name'].tolist()
    home_on_court = home_starters.copy()
    away_on_court = away_starters.copy()

    lineup_tracking = []

    team_rosters = {
        'home': set(box_df[box_df['teamTricode'] == home_team]['full_name']),
        'away': set(box_df[box_df['teamTricode'] == away_team]['full_name']),
    }

    for idx, row in pbp_df.iterrows():
        event_type = row['EVENTMSGTYPE']
        event_desc = row['HOMEDESCRIPTION'] or row['VISITORDESCRIPTION']
        player1 = row['PLAYER1_NAME']
        team_involved = None
        
        #Debugging.. remove ejection -- come back to later and fix
        if game_id == "0022400770":
            pbp_df = pbp_df[~pbp_df['EVENTNUM'].isin([341, 347])]

        if row['EVENTMSGTYPE'] == 12 and row['PERIOD'] > 1:
            home_on_court = infer_lineup_for_team(idx + 1, pbp_df, list(team_rosters['home']), 'home')
            away_on_court = infer_lineup_for_team(idx + 1, pbp_df, list(team_rosters['away']), 'away')
        
        
        # Substitution logic with team lookup
        if event_type == 8:
            player_out = row['PLAYER1_NAME']
            player_in = row['PLAYER2_NAME']

            # Debugging.. fix player name (poor fix, improve later)
            if player_out == "Armel Traoré":
                player_out = "Armel Traore"

            team_code = player_team_map.get(player_out)

            if team_code == home_team:
                lineup = home_on_court
            elif team_code == away_team:
                lineup = away_on_court
            else:
                print(f"[⚠️ Unknown team] Could not resolve team for sub: {player_out} -> {player_in}, {game_id}")
                continue

            # Debugging.. fix player name (poor fix, improve later)
            if player_out == "Armel Traore":
                player_out = "Armel Traoré"

            if player_out in lineup:
                lineup.remove(player_out)
            else:
                print(f"[⚠️ Sub Error: idx {idx}] Tried to sub OUT {player_out} who wasn't on court, {game_id}")
                break

            if len(lineup) < 5:
                lineup.append(player_in)
            else:
                print(f"[⚠️ Sub Error] More than 5 players on court after sub: {player_in}, {game_id}")

            if team_code == home_team:
                home_on_court = lineup
                team_involved = 'home'
            else:
                away_on_court = lineup
                team_involved = 'away'

        else:
            # For non-sub events, infer team from player involved if possible
            if player1 in player_team_map:
                team_involved = 'home' if player_team_map[player1] == home_team else 'away'

        # Log current state
        lineup_tracking.append({
            'play_index': idx,
            'game_id': row['GAME_ID'],
            'event_code': row['EVENTMSGTYPE'],
            'period': row['PERIOD'],
            'time': row['PCTIMESTRING'],
            'description': event_desc,
            'player_involved': player1,
            'team_involved': team_involved,
            'home_on_court': tuple(sorted(home_on_court)),
            'away_on_court': tuple(sorted(away_on_court)),
        })

    lineup_df = pd.DataFrame(lineup_tracking)

    periods = 5

    # Get list of unique lineups for home and away
    unique_lineups_home = set(lineup_df['home_on_court'])
    unique_lineups_away = set(lineup_df['away_on_court'])
    count1=0
    count2=0
    for period in range(1, periods + 1):
        for lineup in unique_lineups_home: 
            new_lineup_df = lineup_df[(lineup_df['period'] == period) & (lineup_df['home_on_court'] == lineup)]

            # continue if lineup is empty
            if len(new_lineup_df) == 0:
                continue
                
            # Calculate stats

            made_2pt = made_fts = made_3pt = missed_2pt = missed_fts = missed_3pt = rebounds = assists = turnovers = fouls_committed = 0
            opp_made_2pt = opp_made_fts = opp_made_3pt = opp_missed_2pt = opp_missed_fts = opp_missed_3pt = opp_rebounds = opp_assists = opp_turnovers = fouls_drawn = 0

            for _, row in new_lineup_df.iterrows():
                team_involved = row['team_involved']
                is_us = team_involved == 'home'
                if_not_us = team_involved == 'away'
                desc = str(row['description'])

                if is_us:
                    if row['event_code'] == 1 and 'AST' in desc:
                        assists += 1
                    if row['event_code'] == 1 and '3PT' not in desc:
                        made_2pt += 1
                    if row['event_code'] == 1 and '3PT' in desc:
                        made_3pt += 1
                    if row['event_code'] == 3 and "MISS" not in desc:
                        made_fts += 1
                    if row['event_code'] == 4:
                        rebounds += 1
                    if row['event_code'] == 5:
                        turnovers += 1
                    if row['event_code'] == 6:
                        fouls_committed += 1
                    if row['event_code'] == 2 and '3PT' not in desc:
                        missed_2pt += 1
                    if row['event_code'] == 2 and '3PT' in desc:
                        missed_3pt += 1
                    if row['event_code'] == 3 and "MISS" in desc:
                        missed_fts += 1
                elif if_not_us:
                    if row['event_code'] == 1 and 'AST' in desc:
                        opp_assists += 1
                    if row['event_code'] == 1 and '3PT' not in desc:
                        opp_made_2pt += 1
                    if row['event_code'] == 1 and '3PT' in desc:
                        opp_made_3pt += 1
                    if row['event_code'] == 3 and "MISS" not in desc:
                        opp_made_fts += 1
                    if row['event_code'] == 4:
                        # print(count1, desc)
                        # count1 += 1
                        opp_rebounds += 1
                    if row['event_code'] == 5:
                        opp_turnovers += 1
                    if row['event_code'] == 6:
                        fouls_drawn += 1
                    if row['event_code'] == 2 and '3PT' not in desc:
                        opp_missed_2pt += 1
                    if row['event_code'] == 2 and '3PT' in desc:
                        opp_missed_3pt += 1
                    if row['event_code'] == 3 and "MISS" in desc:
                        opp_missed_fts += 1

            record = {
                'game_id': game_id,
                'team': home_team,
                'opponent': away_team,
                'lineup': lineup,
                'period': period,
                'points': 2*made_2pt + 3*made_3pt + made_fts,
                'opp_points': 2*opp_made_2pt + 3*opp_made_3pt + opp_made_fts,
                'rebounds': rebounds,
                'opp_rebounds': opp_rebounds,
                'assists': assists,
                'opp_assists': opp_assists,
                'turnovers': turnovers,
                'opp_turnovers': opp_turnovers,
                'fouls_committed': fouls_committed,
                'fouls_drawn': fouls_drawn
            }


            team_lineup_stats[home_team] = pd.concat(
                [team_lineup_stats[home_team], pd.DataFrame([record])],
                ignore_index=True
            )

        for lineup in unique_lineups_away: 
            new_lineup_df = lineup_df[(lineup_df['period'] == period) & (lineup_df['away_on_court'] == lineup)]


            # continue if lineup is empty
            if len(new_lineup_df) == 0:
                continue

            # Calculate stats

            made_2pt = made_fts = made_3pt = missed_2pt = missed_fts = missed_3pt = rebounds = assists = turnovers = fouls_committed = 0
            opp_made_2pt = opp_made_fts = opp_made_3pt = opp_missed_2pt = opp_missed_fts = opp_missed_3pt = opp_rebounds = opp_assists = opp_turnovers = fouls_drawn = 0
            
            for _, row in new_lineup_df.iterrows():
                team_involved = row['team_involved']
                is_us = team_involved == 'away'
                if_not_us = team_involved == 'home'
                desc = str(row['description'])

                if is_us:
                    if row['event_code'] == 1 and 'AST' in desc:
                        assists += 1
                    if row['event_code'] == 1 and '3PT' not in desc:
                        made_2pt += 1
                    if row['event_code'] == 1 and '3PT' in desc:
                        made_3pt += 1
                    if row['event_code'] == 3 and "MISS" not in desc:
                        made_fts += 1
                    if row['event_code'] == 4:
                        # print(count2, desc)
                        # count2 += 1
                        rebounds += 1
                    if row['event_code'] == 5:
                        turnovers += 1
                    if row['event_code'] == 6:
                        fouls_committed += 1
                    if row['event_code'] == 2 and '3PT' not in desc:
                        missed_2pt += 1
                    if row['event_code'] == 2 and '3PT' in desc:
                        missed_3pt += 1
                    if row['event_code'] == 3 and "MISS" in desc:
                        missed_fts += 1
                elif if_not_us:
                    if row['event_code'] == 1 and 'AST' in desc:
                        opp_assists += 1
                    if row['event_code'] == 1 and '3PT' not in desc:
                        opp_made_2pt += 1
                    if row['event_code'] == 1 and '3PT' in desc:
                        opp_made_3pt += 1
                    if row['event_code'] == 3 and "MISS" not in desc:
                        opp_made_fts += 1
                    if row['event_code'] == 4:
                        
                        opp_rebounds += 1
                    if row['event_code'] == 5:
                        opp_turnovers += 1
                    if row['event_code'] == 6:
                        fouls_drawn += 1
                    if row['event_code'] == 2 and '3PT' not in desc:
                        opp_missed_2pt += 1
                    if row['event_code'] == 2 and '3PT' in desc:
                        opp_missed_3pt += 1
                    if row['event_code'] == 3 and "MISS" in desc:
                        opp_missed_fts += 1

            record = {
                'game_id': game_id,
                'team': away_team,
                'opponent': home_team,
                'lineup': lineup,
                'period': period,
                'points': 2*made_2pt + 3*made_3pt + made_fts,
                'opp_points': 2*opp_made_2pt + 3*opp_made_3pt + opp_made_fts,
                'rebounds': rebounds,
                'opp_rebounds': opp_rebounds,
                'assists': assists,
                'opp_assists': opp_assists,
                'turnovers': turnovers,
                'opp_turnovers': opp_turnovers,
                'fouls_committed': fouls_committed,
                'fouls_drawn': fouls_drawn
            }


            team_lineup_stats[away_team] = pd.concat(
                [team_lineup_stats[away_team], pd.DataFrame([record])],
                ignore_index=True
            )
    


# for team in team_lineup_stats.keys():
#     print(team_lineup_stats[team])


time_end = time.time()
time_total = time_end - time_start
print(f"Time taken: {time_total}")


# for team in team_lineup_stats.keys():
#     df = team_lineup_stats[team]
#     # Step 1: Sort the DataFrame by game_id (and optionally by period if needed)
#     df = df.sort_values('game_id').reset_index(drop=True)
#     # Step 2: Create a mapping of each unique game_id to a game number (1 to 82)
#     game_id_map = {game_id: i+1 for i, game_id in enumerate(df['game_id'].unique())}
#     # Step 3: Map the game_id in your DataFrame to the corresponding game_number
#     df['game_number'] = df['game_id'].map(game_id_map)
#     # save to csv
#     df.to_csv(f'{team}_2024_25.csv', index=False)

for team in team_lineup_stats.keys():
    df = team_lineup_stats[team]
    csv_path = f'{team}_2024_25.csv'

    # If file exists, append without header
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        # First batch — write with header
        df.to_csv(csv_path, index=False)



### ADD GAME NUMBER

# from nba_api.stats.static import teams
# import pandas as pd
# import os

# # Get list of all NBA team abbreviations (e.g., 'BOS', 'LAL')
# team_abbrevs = [team['abbreviation'] for team in teams.get_teams()]

# # For each team abbreviation, load and update its CSV
# for team_abbr in team_abbrevs:
#     csv_path = f'{team_abbr}_2024_25.csv'

#     # Skip if the CSV doesn't exist (not yet generated from batch runs)
#     if not os.path.exists(csv_path):
#         print(f"Skipping {team_abbr} as CSV doesn't exist")
#         continue

#     # Load the full dataset
#     df = pd.read_csv(csv_path)

#     # Sort and reset index
#     df = df.sort_values('game_id').reset_index(drop=True)

#     # Map game_id to game_number
#     game_id_map = {game_id: i + 1 for i, game_id in enumerate(df['game_id'].unique())}
#     df['game_number'] = df['game_id'].map(game_id_map)

#     # Save updated CSV
#     df.to_csv(csv_path, index=False)
