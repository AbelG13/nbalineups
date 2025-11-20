from nba_api.stats.endpoints import boxscoretraditionalv3 
from nba_api.live.nba.endpoints import playbyplay
import pandas as pd
from nba_api.stats.endpoints import scheduleleaguev2
from nba_api.stats.static import teams, players
import time
import random
import numpy as np
import unicodedata
import os
from datetime import datetime
import ast

#time how long it takes to run
time_start = time.time()

# Active player csv
additional_data = pd.read_csv('playersBDL25.csv')
api_data = pd.read_csv('active25.csv')
PLAYER_LOOKUP = {p["id"]: p["full_name"] for p in players.get_players()}

def idToName(id):
    try:
        name = api_data[api_data['player_id'] == id]['first_name'].values[0] + ' ' + api_data[api_data['player_id'] == id]['last_name'].values[0]
    except:
        try:
            name = PLAYER_LOOKUP.get(id)
        except:
            name = "none"
            print("player id not found: " + str(id))
    return name

def infer_lineup_for_team(pbp_df, team_side):
    """
    Infer the lineup (5 players) on the court at the start of a quarter for a single team.

    Args:
        pbp_df: play-by-play DataFrame.
        team_side: 'home' or 'away'

    Returns:
        on_court: list of 5 players inferred to be on the court
    """
    on = set()
    off = set()

    pbp_df = pbp_df[(pbp_df['actionType'] == 'substitution' and pbp_df['teamTricode'] == team_side)]

    for row in pbp_df.iterrows():
        if row['subType'] == 'in':
            off.add(idToName(row['personId']))
        elif row['subType'] == 'out' and idToName(row['personId']) not in off:
            on.add(idToName(row['personId']))
        
        if len(on) == 5:
            break

    return list(on)


def parse_pctimestring_iso(s):
    # s looks like "PT11M24.00S"
    s = s.removeprefix("PT")
    minutes, seconds = s.split("M")
    seconds = seconds.rstrip("S")

    return int(minutes) * 60 + float(seconds)   # total seconds

def elapsed_time(idx, row, df):
    if row['actionType'] == 'period' and row['subType'] == 'start':
        return 0

    t_current = parse_pctimestring_iso(row['clock'])
    t_prev = parse_pctimestring_iso(df.loc[idx - 1, 'clock'])

    delta_min = (t_prev - t_current) / 60
    return delta_min

# Safely convert stringified lists/dicts in 'qualifiers' column **once**
def safe_literal_eval(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (SyntaxError, ValueError):
            return x  # or return None, depending on what you want
    return x

# Fetch the full 2024–25 NBA schedule
sched = scheduleleaguev2.ScheduleLeagueV2(
    league_id='00', 
    season='2025-26'
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


height_dict = dict()
test = False
start= 125
end= 250
for idx,id in enumerate(game_ids[start:end]):
    # Load game
    game_id = id
    for attempt in range(3):
        try:
            double_break = False
            pbp_df = pd.DataFrame(playbyplay.PlayByPlay(game_id=game_id).get_dict()["game"]["actions"])
            box_df = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id).get_data_frames()[0]

            # Add full name column to box_df
            box_df['full_name'] = box_df['firstName'] + ' ' + box_df['familyName']
            break
        except Exception as e:
            if "'NoneType' object has no attribute 'keys'" in str(e) or "Expecting value" in str(e):
                print(f"Game {game_id} not played yet: {str(e)}. Further games likely not played either. Last played game is {idx + start - 1}")
                double_break = True
                break  
            elif "columns passed" in str(e):
                print("game in progress, wait till it finishes")
            else:
                print(f"Attempt {attempt + 1} failed for game {game_id}: {str(e)}")
                time.sleep(int(np.random.choice([21, 33,42])))
    if double_break:
        break


    # # Apply the function to the 'qualifiers' column
    # pbp_df['qualifiers'] = pbp_df['qualifiers'].apply(safe_literal_eval)

    if test:
        pbp_df.to_csv('test_pbp.csv', index=False)


    # avoid rate limits
    if idx % 1 == 0:
        if idx%25 == 0:
            print(idx+start)
        time.sleep(0.5)

    # Build player-to-team map
    player_team_map = dict(zip(box_df['full_name'], box_df['teamTricode']))

    # If Hansen Yang is in dictionary, reverse it to Yang Hansen
    if 'Hansen Yang' in player_team_map:
        player_team_map['Yang Hansen'] = player_team_map.pop('Hansen Yang')

    team_codes = box_df['teamTricode'].unique()
    try:
        home_team = team_codes[1]
        away_team = team_codes[0]
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
        if row['personId'] == 0 or row['subType'] == 'technical':
            continue
        event_type = row['actionType']
        event_desc = row['description']
        player_id = row['personId']
        player_name = idToName(player_id)
        if player_name == "none":
            print(row)        
        team_involved = 'home' if row['teamTricode'] == home_team else 'away'
                
        
        # Substitution logic with team lookup
        if event_type == 'substitution':
            
            if row['teamTricode'] == home_team:
                if row['subType'] == 'in':
                    home_on_court.append(player_name)
                elif row['subType'] == 'out':
                    home_on_court.remove(player_name)
                else:
                    print(f"[⚠️ Unknown subType] Could not resolve subType for sub")
                    continue
            elif row['teamTricode'] == away_team:
                if row['subType'] == 'in':
                    away_on_court.append(player_name)
                elif row['subType'] == 'out':
                    away_on_court.remove(player_name)
                else:
                    print(f"[⚠️ Unknown subType] Could not resolve subType for sub")
                    continue
            else:
                print(f"[⚠️ Unknown team] Could not resolve team for sub")

        
        if len(home_on_court) != 5 or len(away_on_court) != 5:
            # subs in progress
            continue


        

        # calculate average height of home and away
        total_height = 0
        if tuple(sorted(home_on_court)) not in height_dict:
            for player in sorted(home_on_court):
                first_name, last_name = player.split(' ', 1)
                
                # Debugging... fix player name (poor fix, improve later)
                if first_name == 'Yanic':
                    first_name = "Yanic Konan"
                    last_name = "Niederhäuser"
                if last_name == 'Lavine':
                    last_name = 'LaVine' # capitalize the V

                height = additional_data[(additional_data['first_name'] == first_name) & (additional_data['last_name'] == last_name)]['height']
                if len(height) == 0:
                    print(f"[⚠️ Height Error] Could not resolve height {height} for home player: {first_name} (first) {last_name} (last), {game_id}")
                    continue
                feet, inches = str(height.dropna().reset_index(drop=True)[0]).split('-')
                total_height += int(feet) * 12 + int(inches)
            avg_home_height = total_height / len(home_on_court)
            height_dict[tuple(sorted(home_on_court))] = avg_home_height

        total_height = 0
        
        if tuple(sorted(away_on_court)) not in height_dict:
            for player in sorted(away_on_court):
                first_name, last_name = player.split(' ', 1)
                
                # Debugging... fix player name (poor fix, improve later)
                if first_name == 'Yanic':
                    first_name = "Yanic Konan"
                    last_name = "Niederhäuser"
                if last_name == 'Lavine':
                    last_name = 'LaVine'
                if first_name == 'Tobais' and last_name == 'Harris':
                    first_name = 'Tobias'

                height = additional_data[(additional_data['first_name'] == first_name) & (additional_data['last_name'] == last_name)]['height']
                if len(height) == 0:
                    print(f"[⚠️ Height Error] Could not resolve height {height} for away player: {first_name} (first) {last_name} (last), {game_id}")
                    continue
                feet, inches = str(height.dropna().reset_index(drop=True)[0]).split('-')
                total_height += int(feet) * 12 + int(inches)
            avg_away_height = total_height / len(away_on_court)
            height_dict[tuple(sorted(away_on_court))] = avg_away_height

        # Log current state
        lineup_tracking.append({
            'play_index': idx,
            'game_id': game_id,
            'action_type': row['actionType'],
            'period': row['period'],
            'time': row['clock'],
            'elapsed_time': elapsed_time(idx, row, pbp_df),
            'description': event_desc,
            'player_involved': player_name,
            'team_abbreviation': row['teamTricode'],
            'team_involved': team_involved,
            'home_on_court': tuple(sorted(home_on_court)),
            'away_on_court': tuple(sorted(away_on_court)),
            'avg_home_height': height_dict[tuple(sorted(home_on_court))],
            'avg_away_height': height_dict[tuple(sorted(away_on_court))],
            'shot_result': row['shotResult'],
            'subtype': row['subType'],
            'qualifiers': row['qualifiers']
        })

    lineup_df = pd.DataFrame(lineup_tracking)

    if test:
        lineup_df.to_csv(f'test_lineup.csv', index=False)

    periods = 8

    # Get list of unique lineups for home and away
    unique_lineups_home = set(lineup_df['home_on_court'])
    unique_lineups_away = set(lineup_df['away_on_court'])

    for period in range(1, periods + 1):

        for lineup in unique_lineups_home: 
            new_lineup_df = lineup_df[(lineup_df['period'] == period) & (lineup_df['home_on_court'] == lineup)]

            # continue if lineup is empty
            if new_lineup_df.empty:
                continue
                
            # Calculate stats

            made_2pt = made_fts = made_3pt = missed_2pt = missed_fts = missed_3pt = rebounds = assists \
            = turnovers = fouls_committed = minutes_played = off_rebounds = fastbreak_2 = from_turnover_2 = second_chance_2 \
            = fastbreak_3 = from_turnover_3 = second_chance_3 = points_in_paint = opp_made_2pt = opp_made_fts = opp_made_3pt \
            = opp_missed_2pt = opp_missed_fts = opp_missed_3pt = opp_rebounds = opp_assists = opp_turnovers = fouls_drawn \
            = opp_off_rebounds = opp_fastbreak_2 = opp_from_turnover_2 = opp_second_chance_2 = opp_fastbreak_3 = \
            opp_from_turnover_3 = opp_second_chance_3 = opp_points_in_paint = 0

            for _, row in new_lineup_df.iterrows():
                team_involved = row['team_involved']
                is_us = team_involved == 'home'
                if_not_us = team_involved == 'away'
                desc = str(row['description'])
                action = row['action_type']
                minutes_played += row['elapsed_time']
                result = row['shot_result']
                subtype = row['subtype']

                # # convert string to actual list
                # try:
                #     row['qualifiers'] = ast.literal_eval(row['qualifiers'])
                # except:
                #     pass
                qualifiers = row['qualifiers']

                if is_us:
                    if action in ['2pt', '3pt'] and 'AST' in desc:
                        assists += 1
                    if action == '2pt' and result == 'Made':
                        made_2pt += 1
                        if 'fastbreak' in qualifiers:
                            fastbreak_2 += 1
                        if 'fromturnover' in qualifiers:
                            from_turnover_2 += 1
                        if '2ndchance' in qualifiers:
                            second_chance_2 += 1
                        if 'pointsinthepaint' in qualifiers:
                            points_in_paint += 1
                    if action == '3pt' and result == 'Made':
                        made_3pt += 1
                        if 'fastbreak' in qualifiers:
                            fastbreak_3 += 1
                        if 'fromturnover' in qualifiers:
                            from_turnover_3 += 1
                        if '2ndchance' in qualifiers:
                            second_chance_3 += 1
                    if action == 'freethrow' and result == 'Made':
                        made_fts += 1
                    if action == 'rebound':
                        rebounds += 1
                    if action == 'turnover':
                        turnovers += 1
                    if action == 'foul':
                        fouls_committed += 1
                    if action == '2pt' and result == 'Missed':
                        missed_2pt += 1
                    if action == '3pt' and result == 'Missed':
                        missed_3pt += 1
                    if action == 'freethrow' and result == 'Missed':
                        missed_fts += 1
                    if action == 'rebound' and subtype == 'offensive':
                        off_rebounds += 1                   

                elif if_not_us:
                    if action in ['2pt', '3pt'] and 'AST' in desc:
                        opp_assists += 1
                    if action == '2pt' and result == 'Made':
                        opp_made_2pt += 1
                        if 'fastbreak' in qualifiers:
                            opp_fastbreak_2 += 1
                        if 'fromturnover' in qualifiers:
                            opp_from_turnover_2 += 1
                        if '2ndchance' in qualifiers:
                            opp_second_chance_2 += 1
                        if 'pointsinthepaint' in qualifiers:
                            opp_points_in_paint += 1
                    if action == '3pt' and result == 'Made':
                        opp_made_3pt += 1
                        if 'fastbreak' in qualifiers:
                            opp_fastbreak_3 += 1
                        if 'fromturnover' in qualifiers:
                            opp_from_turnover_3 += 1
                        if '2ndchance' in qualifiers:
                            opp_second_chance_3 += 1
                    if action == 'freethrow' and result == 'Made':
                        opp_made_fts += 1
                    if action == 'rebound':
                        opp_rebounds += 1
                    if action == 'turnover':
                        opp_turnovers += 1
                    if action == 'foul':
                        fouls_drawn += 1
                    if action == '2pt' and result == 'Missed':
                        opp_missed_2pt += 1
                    if action == '3pt' and result == 'Missed':
                        opp_missed_3pt += 1
                    if action == 'freethrow' and result == 'Missed':
                        opp_missed_fts += 1
                    if action == 'rebound' and subtype == 'offensive':
                        opp_off_rebounds += 1

            # possession calculation
            poss_calc = made_2pt + missed_2pt + made_3pt + missed_3pt - off_rebounds + turnovers + 0.44 * made_fts + missed_fts
            opp_poss_calc = opp_made_2pt + opp_missed_2pt + opp_made_3pt + opp_missed_3pt - opp_off_rebounds + opp_turnovers + 0.44 * opp_made_fts + opp_missed_fts

            record = {
                'game_id': game_id,
                'team': home_team,
                'opponent': away_team,
                'team_avg_height': row['avg_home_height'],
                'opp_avg_height': row['avg_away_height'],
                'lineup': lineup,
                'minutes_played': minutes_played,
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
                'fouls_drawn': fouls_drawn,
                'possessions': poss_calc,
                'opp_possessions': opp_poss_calc,
                'fastbreak' : fastbreak_2*2 + fastbreak_3 *3,
                'from_turnover' : from_turnover_2*2 + from_turnover_3*3,
                'second_chance' : second_chance_2*2 + second_chance_3*3,
                'points_in_paint' : points_in_paint*2,
                'opp_from_turnover': opp_from_turnover_2*2 + opp_from_turnover_3*3,
                'opp_fastbreak': opp_fastbreak_2*2 + opp_fastbreak_3*3,
                'opp_second_chance': opp_second_chance_2*2 + opp_second_chance_3*3,
                'opp_points_in_paint': opp_points_in_paint*2,
                'unscaled_pace': poss_calc + opp_poss_calc# Multiple by 24/minutes_played AFTER aggregation
    
            
            }


            team_lineup_stats[home_team] = pd.concat(
                [team_lineup_stats[home_team], pd.DataFrame([record])],
                ignore_index=True
            )

        for lineup in unique_lineups_away: 
            new_lineup_df = lineup_df[(lineup_df['period'] == period) & (lineup_df['away_on_court'] == lineup)]


            # continue if lineup is empty
            if new_lineup_df.empty:
                continue
            
            # Calculate stats

            made_2pt = made_fts = made_3pt = missed_2pt = missed_fts = missed_3pt = rebounds = assists \
            = turnovers = fouls_committed = minutes_played = off_rebounds = fastbreak_2 = from_turnover_2 = second_chance_2 \
            = fastbreak_3 = from_turnover_3 = second_chance_3 = points_in_paint = opp_made_2pt = opp_made_fts = opp_made_3pt \
            = opp_missed_2pt = opp_missed_fts = opp_missed_3pt = opp_rebounds = opp_assists = opp_turnovers = fouls_drawn \
            = opp_off_rebounds = opp_fastbreak_2 = opp_from_turnover_2 = opp_second_chance_2 = opp_fastbreak_3 = \
            opp_from_turnover_3 = opp_second_chance_3 = opp_points_in_paint = 0


            for i, row in new_lineup_df.iterrows():
                team_involved = row['team_involved']
                is_us = team_involved == 'away'
                if_not_us = team_involved == 'home'
                desc = str(row['description'])
                action = row['action_type']
                minutes_played += row['elapsed_time']
                result = row['shot_result']
                subtype = row['subtype']

                # # convert string to actual list
                # try:
                #     row['qualifiers'] = ast.literal_eval(row['qualifiers'])
                # except:
                #     pass
                qualifiers = row['qualifiers']

                if is_us:
                    if action in ['2pt', '3pt'] and 'AST' in desc:
                        assists += 1
                    if action == '2pt' and result == 'Made':
                        made_2pt += 1
                        if 'fastbreak' in qualifiers:
                            fastbreak_2 += 1
                        if 'fromturnover' in qualifiers:
                            from_turnover_2 += 1
                        if '2ndchance' in qualifiers:
                            second_chance_2 += 1
                        if 'pointsinthepaint' in qualifiers:
                            points_in_paint += 1
                    if action == '3pt' and result == 'Made':
                        made_3pt += 1
                        if 'fastbreak' in qualifiers:
                            fastbreak_3 += 1
                        if 'fromturnover' in qualifiers:
                            from_turnover_3 += 1
                        if '2ndchance' in qualifiers:
                            second_chance_3 += 1
                    if action == 'freethrow' and result == 'Made':
                        made_fts += 1
                    if action == 'rebound':
                        rebounds += 1
                    if action == 'turnover':
                        turnovers += 1
                    if action == 'foul':
                        fouls_committed += 1
                    if action == '2pt' and result == 'Missed':
                        missed_2pt += 1
                    if action == '3pt' and result == 'Missed':
                        missed_3pt += 1
                    if action == 'freethrow' and result == 'Missed':
                        missed_fts += 1
                    if action == 'rebound' and subtype == 'offensive':
                        off_rebounds += 1                   

                elif if_not_us:
                    if action in ['2pt', '3pt'] and 'AST' in desc:
                        opp_assists += 1
                    if action == '2pt' and result == 'Made':
                        opp_made_2pt += 1
                        if 'fastbreak' in qualifiers:
                            opp_fastbreak_2 += 1
                        if 'fromturnover' in qualifiers:
                            opp_from_turnover_2 += 1
                        if '2ndchance' in qualifiers:
                            opp_second_chance_2 += 1
                        if 'pointsinthepaint' in qualifiers:
                            opp_points_in_paint += 1
                    if action == '3pt' and result == 'Made':
                        opp_made_3pt += 1
                        if 'fastbreak' in qualifiers:
                            opp_fastbreak_3 += 1
                        if 'fromturnover' in qualifiers:
                            opp_from_turnover_3 += 1
                        if '2ndchance' in qualifiers:
                            opp_second_chance_3 += 1
                    if action == 'freethrow' and result == 'Made':
                        opp_made_fts += 1
                    if action == 'rebound':
                        opp_rebounds += 1
                    if action == 'turnover':
                        opp_turnovers += 1
                    if action == 'foul':
                        fouls_drawn += 1
                    if action == '2pt' and result == 'Missed':
                        opp_missed_2pt += 1
                    if action == '3pt' and result == 'Missed':
                        opp_missed_3pt += 1
                    if action == 'freethrow' and result == 'Missed':
                        opp_missed_fts += 1
                    if action == 'rebound' and subtype == 'offensive':
                        opp_off_rebounds += 1

            # possession calculation
            poss_calc = made_2pt + missed_2pt + made_3pt + missed_3pt - off_rebounds + turnovers + 0.44 * made_fts + missed_fts
            opp_poss_calc = opp_made_2pt + opp_missed_2pt + opp_made_3pt + opp_missed_3pt - opp_off_rebounds + opp_turnovers + 0.44 * opp_made_fts + opp_missed_fts

            record = {
                'game_id': game_id,
                'team': away_team,
                'opponent': home_team,
                'team_avg_height': row['avg_away_height'],
                'opp_avg_height': row['avg_home_height'],
                'lineup': lineup,
                'minutes_played': minutes_played,
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
                'fouls_drawn': fouls_drawn,
                'possessions': poss_calc,
                'opp_possessions': opp_poss_calc,
                'fastbreak' : fastbreak_2*2 + fastbreak_3 *3,
                'from_turnover' : from_turnover_2*2 + from_turnover_3*3,
                'second_chance' : second_chance_2*2 + second_chance_3*3,
                'points_in_paint' : points_in_paint*2,
                'opp_from_turnover': opp_from_turnover_2*2 + opp_from_turnover_3*3,
                'opp_fastbreak': opp_fastbreak_2*2 + opp_fastbreak_3*3,
                'opp_second_chance': opp_second_chance_2*2 + opp_second_chance_3*3,
                'opp_points_in_paint': opp_points_in_paint*2,
                'unscaled_pace': poss_calc + opp_poss_calc# Multiple by 24/minutes_played AFTER aggregation
            
            }

            team_lineup_stats[away_team] = pd.concat(
                [team_lineup_stats[away_team], pd.DataFrame([record])],
                ignore_index=True
            )
    
time_end = time.time()
time_total = time_end - time_start
print(f"Time taken: {time_total}")


# Create empty CSV files for each team
team_abbrevs = [team['abbreviation'] for team in teams.get_teams()]

columns = [
    'game_id',
    'team',
    'opponent',
    'team_avg_height',
    'opp_avg_height',
    'lineup',
    'minutes_played',
    'period',
    'points',
    'opp_points',
    'rebounds',
    'opp_rebounds',
    'assists',
    'opp_assists',
    'turnovers',
    'opp_turnovers',
    'fouls_committed',
    'fouls_drawn',
    'possessions',
    'opp_possessions',
    'fastbreak',
    'from_turnover',
    'second_chance',
    'points_in_paint',
    'opp_from_turnover',
    'opp_fastbreak',
    'opp_second_chance',
    'opp_points_in_paint',
    'unscaled_pace'
]

# Hou test case, save as test_team
if test:
    df = team_lineup_stats['HOU']
    df = df[columns]
    df.to_csv("test_team.csv", index=False)


if not test:
    # Define the subfolder where you want to save files
    save_dir = os.path.join("S2")

    # Create the folder if it doesn’t exist
    os.makedirs(save_dir, exist_ok=True)

    # Create empty files if they don’t exist
    for abbrev in team_abbrevs:
        filename = f"S2_{abbrev}_2025_26.csv"
        file_path = os.path.join(save_dir, filename)
        if not os.path.exists(file_path):
            pd.DataFrame(columns=columns).to_csv(file_path, index=False)

    # Append or write team data
    for team in team_lineup_stats.keys():
        df = team_lineup_stats[team]
        # Reorder columns explicitly before writing
        df = df[columns]
        csv_path = os.path.join(save_dir, f"S2_{team}_2025_26.csv")

        # If file exists, append without header
        if os.path.exists(csv_path):
            df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            # First batch — write with header
            df.to_csv(csv_path, index=False)



