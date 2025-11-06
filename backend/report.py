# test_schedule_simple.py
from datetime import datetime, date
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams
import pandas as pd
import numpy as np

INJURIES = []

def standards_values():
    nba_teams_data = teams.get_teams()

    # Extract abbreviations
    team_abbreviations = [team['abbreviation'] for team in nba_teams_data]


    edge_1 = []
    edge_2 = []
    edge_3 = []
    edge_4 = []
    edge_5 = []
    edge_6 = []
    edge_7 = []

    for team in team_abbreviations:
        df = pd.read_csv(f"data/S2/S2_{team}_2025_26.csv")

        lineup_agg = df.groupby('lineup').agg({
            'minutes_played': 'sum',
            'points': 'sum',
            'opp_points': 'sum',
            'rebounds': 'sum',
            'opp_rebounds': 'sum',
            'assists': 'sum',
            'opp_assists': 'sum',
            'turnovers': 'sum',
            'opp_turnovers': 'sum'
        }).reset_index()

        top_lineups = lineup_agg.nlargest(3, 'minutes_played')
        # Filter data to only include top 3 lineups
        df_filtered = df[df['lineup'].isin(top_lineups['lineup'])]

        stats = df_filtered.agg({
            'minutes_played': 'sum',
            'points': 'sum',
            'opp_points': 'sum',
            'rebounds': 'sum',
            'opp_rebounds': 'sum',
            'assists': 'sum',
            'opp_assists': 'sum',
            'turnovers': 'sum',
            'opp_turnovers': 'sum'
        })
        # Calculate per-minute stats
        min = stats['minutes_played'] if stats['minutes_played'] > 0 else 1

        pts_per_min = stats['points'] / min
        rbs_per_min = stats['rebounds'] / min
        asts_per_min = stats['assists'] / min
        opp_pts_per_min = stats['opp_points'] / min
        opp_rbs_per_min = stats['opp_rebounds'] / min
        opp_tos_per_min = stats['opp_turnovers'] / min

        edge_one = pts_per_min - opp_pts_per_min  # home pts/min vs away opp pts/min
        edge_two = rbs_per_min - opp_rbs_per_min  # home rbs/min vs away opp rbs/min
        edge_three = asts_per_min / opp_tos_per_min if opp_tos_per_min > 0 else 0  # home asts/min / away opp tos/min

        q1 = df_filtered[df_filtered['period'] == 1]
        q1_min = q1['minutes_played'].sum() if len(q1) > 0 else 1
        q1_pts_per_min = (q1['points'].sum() / q1_min) if q1_min > 0 else 0
        edge_four = q1_pts_per_min



        edge_1.append(edge_one)
        edge_2.append(edge_two)
        edge_3.append(edge_three)
        edge_4.append(edge_four)

    return np.mean(edge_1), np.mean(edge_2), np.mean(edge_3), np.mean(edge_4), \
                np.std(edge_1, ddof=1), np.std(edge_2, ddof=1), np.std(edge_3, ddof=1), \
                np.std(edge_4, ddof=1)     

def get_team_id_to_abbr():
    # Build a map: TEAM_ID -> "LAL", "BOS", etc.
    return {int(t["id"]): t["abbreviation"] for t in teams.get_teams()}

def get_games_for_date(date_obj: datetime):
    # NBA expects MM/DD/YYYY (Eastern calendar date string), but this works fine for a quick test
    date_str = date_obj.strftime("%m/%d/%Y")
    sb = scoreboardv2.ScoreboardV2(game_date=date_str)

    games = sb.game_header.get_data_frame()
    return games  # DataFrame with GAME_ID, GAME_DATE_EST, HOME_TEAM_ID, VISITOR_TEAM_ID, GAME_STATUS_TEXT, etc.

def games():
    team_map = get_team_id_to_abbr()
    today = date.today().strftime("%Y-%m-%d")

    #change string to datetime
    today = datetime.strptime(today, '%Y-%m-%d')
    print(today, type(today))

    #print(f"\nFetching NBA schedule for {today.strftime('%Y-%m-%d')} ...")
    games_df = get_games_for_date(today)

    if games_df.empty:
        print("No games found for this date.")
        return

    # create a new dataframe to store game_id and home team

    rows = []

    # Print a minimal, readable summary
    for _, row in games_df.iterrows():
        game_id = row["GAME_ID"]
        home = team_map.get(int(row["HOME_TEAM_ID"]), row["HOME_TEAM_ID"])
        away = team_map.get(int(row["VISITOR_TEAM_ID"]), row["VISITOR_TEAM_ID"])
        game_time = row.get("GAME_STATUS_TEXT", "")  # pre-game: "7:30 pm ET", or "Final", etc.

        rows.append({"GAME_ID": game_id, "HOME_TEAM": home, "VISITOR_TEAM": away, "GAME_TIME": game_time})

    today_games_df = pd.DataFrame(rows)

    return today_games_df


def report_data():
    games_df = games()

    rows = []
    
    for _, row in games_df.iterrows():
        game_id = row["GAME_ID"]
        home_team = row["HOME_TEAM"]
        away_team = row["VISITOR_TEAM"]
        game_time = row["GAME_TIME"]


        home_data = pd.read_csv(f"data/S2/S2_{home_team}_2025_26.csv")
        away_data = pd.read_csv(f"data/S2/S2_{away_team}_2025_26.csv")

        # Helper function to check if lineup contains injured players
        def has_injured_player(lineup_str, injuries_list):
            if not injuries_list:
                return False
            # Parse the lineup string (it's a tuple string like "('Player1', 'Player2', ...)")
            import ast
            try:
                lineup_tuple = ast.literal_eval(lineup_str)
                players = [p.strip().strip("'\"") for p in lineup_tuple]
                return any(player in injuries_list for player in players)
            except:
                return False

        # Part 1: Get top 3 lineups for each team by minutes played (excluding injured players)
        def get_top_lineups(df, injuries_list, top_n=3):
            # Aggregate by lineup
            lineup_agg = df.groupby('lineup').agg({
                'minutes_played': 'sum',
                'points': 'sum',
                'opp_points': 'sum',
                'rebounds': 'sum',
                'opp_rebounds': 'sum',
                'assists': 'sum',
                'opp_assists': 'sum',
                'turnovers': 'sum',
                'opp_turnovers': 'sum'
            }).reset_index()
            
            # Filter out lineups with injured players
            lineup_agg = lineup_agg[~lineup_agg['lineup'].apply(lambda x: has_injured_player(x, injuries_list))]
            
            # Sort by minutes played descending and get top N
            top_lineups = lineup_agg.nlargest(top_n, 'minutes_played')
            
            return top_lineups['lineup'].tolist(), top_lineups

        home_top_lineups, home_top_lineups_df = get_top_lineups(home_data, INJURIES, 3)
        away_top_lineups, away_top_lineups_df = get_top_lineups(away_data, INJURIES, 3)

        # Filter data to only include top 3 lineups
        home_filtered = home_data[home_data['lineup'].isin(home_top_lineups)]
        away_filtered = away_data[away_data['lineup'].isin(away_top_lineups)]

        max_game_home = home_data['game_number'].max()
        max_game_away = away_data['game_number'].max()

        home_form = home_filtered[home_filtered['game_number'] >= (max_game_home - 10)] if max_game_home >= 10 else home_filtered
        away_form = away_filtered[away_filtered['game_number'] >= (max_game_away - 10)] if max_game_away >= 10 else away_filtered

        # Aggregate stats from top 3 lineups
        home_stats = home_form.agg({
            'minutes_played': 'sum',
            'points': 'sum',
            'opp_points': 'sum',
            'rebounds': 'sum',
            'opp_rebounds': 'sum',
            'assists': 'sum',
            'opp_assists': 'sum',
            'turnovers': 'sum',
            'opp_turnovers': 'sum'
        })

        away_stats = away_form.agg({
            'minutes_played': 'sum',
            'points': 'sum',
            'opp_points': 'sum',
            'rebounds': 'sum',
            'opp_rebounds': 'sum',
            'assists': 'sum',
            'opp_assists': 'sum',
            'turnovers': 'sum',
            'opp_turnovers': 'sum'
        })

        # Calculate per-minute stats
        home_min = home_stats['minutes_played'] if home_stats['minutes_played'] > 0 else 1
        away_min = away_stats['minutes_played'] if away_stats['minutes_played'] > 0 else 1

        home_pts_per_min = home_stats['points'] / home_min
        home_rbs_per_min = home_stats['rebounds'] / home_min
        home_asts_per_min = home_stats['assists'] / home_min
        home_opp_pts_per_min = home_stats['opp_points'] / home_min
        home_opp_rbs_per_min = home_stats['opp_rebounds'] / home_min
        home_opp_tos_per_min = home_stats['opp_turnovers'] / home_min

        away_pts_per_min = away_stats['points'] / away_min
        away_rbs_per_min = away_stats['rebounds'] / away_min
        away_asts_per_min = away_stats['assists'] / away_min
        away_opp_pts_per_min = away_stats['opp_points'] / away_min
        away_opp_rbs_per_min = away_stats['opp_rebounds'] / away_min
        away_opp_tos_per_min = away_stats['opp_turnovers'] / away_min

        # Part 2: Basic Statistical Comparisons
        home_edge_1 = home_pts_per_min - away_opp_pts_per_min  # home pts/min vs away opp pts/min
        home_edge_2 = home_rbs_per_min - away_opp_rbs_per_min  # home rbs/min vs away opp rbs/min
        home_edge_3 = home_asts_per_min / away_opp_tos_per_min if away_opp_tos_per_min > 0 else 0  # home asts/min / away opp tos/min

        away_edge_1 = away_pts_per_min - home_opp_pts_per_min  # away pts/min vs home opp pts/min
        away_edge_2 = away_rbs_per_min - home_opp_rbs_per_min  # away rbs/min vs home opp rbs/min
        away_edge_3 = away_asts_per_min / home_opp_tos_per_min if home_opp_tos_per_min > 0 else 0  # away asts/min / home opp tos/min

        # Part 3: First Quarter Comparisons
        home_q1 = home_filtered[home_filtered['period'] == 1]
        away_q1 = away_filtered[away_filtered['period'] == 1]

        home_q1_form = home_q1[home_q1['game_number'] >= (max_game_home - 10)] if max_game_home >= 10 else home_q1
        away_q1_form = away_q1[away_q1['game_number'] >= (max_game_away - 10)] if max_game_away >= 10 else away_q1

        home_q1_min = home_q1_form['minutes_played'].sum() if len(home_q1_form) > 0 else 1
        away_q1_min = away_q1_form['minutes_played'].sum() if len(away_q1_form) > 0 else 1

        home_q1_pts_per_min = (home_q1_form['points'].sum() / home_q1_min) if home_q1_min > 0 else 0
        away_q1_pts_per_min = (away_q1_form['points'].sum() / away_q1_min) if away_q1_min > 0 else 0

        q1_edge_home = home_q1_pts_per_min - away_q1_pts_per_min
        q1_edge_away = away_q1_pts_per_min - home_q1_pts_per_min

        # Part 4: Collect all edges and pick top 4

        pts_avg, rebs_avg, asts_to_avg, q1_avg, \
            pts_std, rebs_std, asts_to_std, q1_std = standards_values()

        edges = [
            {"name": f"{home_team} Pts/Min", "value": home_edge_1, "team": home_team, "advantage": (home_edge_1-pts_avg) / pts_std if pts_std > 0 else 0},
            {"name": f"{home_team} Reb/Min", "value": home_edge_2, "team": home_team, "advantage": (home_edge_2-rebs_avg) / rebs_std if rebs_std > 0 else 0},
            {"name": f"{home_team} Ast/Tov", "value": home_edge_3, "team": home_team, "advantage": (home_edge_3-asts_to_avg) / asts_to_std if asts_to_std > 0 else 0},
            {"name": f"{away_team} Pts/Min", "value": away_edge_1, "team": away_team, "advantage": (away_edge_1-pts_avg) / pts_std if pts_std > 0 else 0},
            {"name": f"{away_team} Reb/Min", "value": away_edge_2, "team": away_team, "advantage": (away_edge_2-rebs_avg) / rebs_std if rebs_std > 0 else 0},
            {"name": f"{away_team} Ast/Tov", "value": away_edge_3, "team": away_team, "advantage": (away_edge_3-asts_to_avg) / asts_to_std if asts_to_std > 0 else 0},
            {"name": f"{home_team} Q1 Pts/Min", "value": q1_edge_home, "team": home_team, "advantage": (q1_edge_home-q1_avg) / q1_std if q1_std > 0 else 0},
            {"name": f"{away_team} Q1 Pts/Min", "value": q1_edge_away, "team": away_team, "advantage": (q1_edge_away-q1_avg) / q1_std if q1_std > 0 else 0},
        ]
        # Sort by absolute value to get biggest advantages
        edges_sorted = sorted(edges, key=lambda x: x['advantage'], reverse=True)
        
        # # Debugging... Cleanly print edges_sorted
        # for edge in edges_sorted:
        #     print(f"{edge['name']}: value {edge['value']:.3f},  advantage {edge['advantage']:.3f}")
        
        
        top_4_edges = edges_sorted[:4]

        # Format lineup strings for output (remove quotes and parentheses)
        def format_lineup(lineup_str):
            import ast
            try:
                lineup_tuple = ast.literal_eval(lineup_str)
                return ', '.join([p.strip().strip("'\"") for p in lineup_tuple])
            except:
                return lineup_str

        rows.append({
            "GAME_ID": game_id,
            "HOME_TEAM": home_team,
            "VISITOR_TEAM": away_team,
            "GAME_TIME": game_time,
            "HOME_LINEUP_1": format_lineup(home_top_lineups[0]) if len(home_top_lineups) > 0 else "",
            "HOME_LINEUP_2": format_lineup(home_top_lineups[1]) if len(home_top_lineups) > 1 else "",
            "HOME_LINEUP_3": format_lineup(home_top_lineups[2]) if len(home_top_lineups) > 2 else "",
            "AWAY_LINEUP_1": format_lineup(away_top_lineups[0]) if len(away_top_lineups) > 0 else "",
            "AWAY_LINEUP_2": format_lineup(away_top_lineups[1]) if len(away_top_lineups) > 1 else "",
            "AWAY_LINEUP_3": format_lineup(away_top_lineups[2]) if len(away_top_lineups) > 2 else "",
            "EDGE_1": top_4_edges[0]['name'] + f" {top_4_edges[0]['advantage']:.3f}" if len(top_4_edges) > 0 else "",
            "EDGE_2": top_4_edges[1]['name'] + f" {top_4_edges[1]['advantage']:.3f}" if len(top_4_edges) > 1 else "",
            "EDGE_3": top_4_edges[2]['name'] + f" {top_4_edges[2]['advantage']:.3f}" if len(top_4_edges) > 2 else "",
            "EDGE_4": top_4_edges[3]['name'] + f" {top_4_edges[3]['advantage']:.3f}" if len(top_4_edges) > 3 else ""
        })

    # Convert rows to DataFrame and return
    report_df = pd.DataFrame(rows)
    return report_df


# if __name__ == "__main__":
#     rep = report_data()    
#     print(rep[['EDGE_1', 'EDGE_2', 'EDGE_3', 'EDGE_4']])