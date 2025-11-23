# test_schedule_simple.py
from datetime import datetime, date
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams
import pandas as pd
import numpy as np
import os
import ast


INJURIES = pd.read_csv("data/injuries25.csv")["NAME"].tolist()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
FIELDS = {
                'minutes_played': 'sum',
                'points': 'sum',
                'opp_points': 'sum',
                'rebounds': 'sum',
                'opp_rebounds': 'sum',
                'assists': 'sum',
                'opp_assists': 'sum',
                'turnovers': 'sum',
                'opp_turnovers': 'sum',
                'fastbreak': 'sum',
                'from_turnover': 'sum',
                'second_chance': 'sum',
                'points_in_paint': 'sum',
                'opp_from_turnover': 'sum',
                'opp_fastbreak': 'sum',
                'opp_second_chance': 'sum',
                'opp_points_in_paint': 'sum',
                'possessions': 'sum',
                'opp_possessions': 'sum',
            }

def standards_values():
    # try:
        nba_teams_data = teams.get_teams()

        # Extract abbreviations
        team_abbreviations = [team['abbreviation'] for team in nba_teams_data]

        # League averages that will be used to calculate edges
        league_ORtg = []
        league_REB_per100 = []
        league_SecondCh_per100 = []
        league_FBP_per100 = []
        league_PtsOffTO_per100 = []
        league_PITP_per100 = []
        league_forcedTO_per100 = []

        # Differentials used to find distribution
        d_ORtg = []
        d_REB_per100 = []
        d_SecondCh_per100 = []
        d_FBP_per100 = []
        d_PtsOffTO_per100 = []
        d_PITP_per100 = []
        d_forcedTO_per100 = []

        for team in team_abbreviations:
            csv_path = os.path.join(DATA_DIR, 'S2', f'S2_{team}_2025_26.csv')
            df = pd.read_csv(csv_path)

            lineup_agg = df.groupby('lineup').agg(FIELDS).reset_index()

            top_lineups = lineup_agg.nlargest(3, 'minutes_played')
            # Filter data to only include top 3 lineups
            df_filtered = df[df['lineup'].isin(top_lineups['lineup'])]

            stats = df_filtered.agg(FIELDS)

            # Calculate per 100 possessions stats
            poss = stats['possessions'] / 100 if stats['possessions'] > 0 else 1

            league_ORtg.append(stats['points'] / poss)
            league_REB_per100.append(stats['rebounds'] / poss)
            league_SecondCh_per100.append(stats['second_chance'] / poss)
            league_FBP_per100.append(stats['fastbreak'] / poss)
            league_PtsOffTO_per100.append(stats['from_turnover'] / poss)
            league_PITP_per100.append(stats['points_in_paint'] / poss)
            league_forcedTO_per100.append(stats['opp_turnovers'] / poss)

        league_ORtg, league_REB_per100, league_SecondCh_per100, league_FBP_per100, \
            league_PtsOffTO_per100, league_PITP_per100, league_forcedTO_per100 = \
            np.mean(league_ORtg), np.mean(league_REB_per100), np.mean(league_SecondCh_per100), \
            np.mean(league_FBP_per100), np.mean(league_PtsOffTO_per100), np.mean(league_PITP_per100), \
            np.mean(league_forcedTO_per100)


        for team in team_abbreviations:
            csv_path = os.path.join(DATA_DIR, 'S2', f'S2_{team}_2025_26.csv')
            df = pd.read_csv(csv_path)

            lineup_agg = df.groupby('lineup').agg(FIELDS).reset_index()

            top_lineups = lineup_agg.nlargest(3, 'minutes_played')
            # Filter data to only include top 3 lineups
            df_filtered = df[df['lineup'].isin(top_lineups['lineup'])]

            stats = df_filtered.agg(FIELDS)

            # Calculate per 100 possessions stats
            poss = stats['possessions'] / 100 if stats['possessions'] > 0 else 1
            opp_poss = stats['opp_possessions'] / 100 if stats['opp_possessions'] > 0 else 1

            pts_per_poss = stats['points'] / poss
            opp_pts_per_poss = stats['opp_points'] / opp_poss
            
            rbs_per_poss = stats['rebounds'] / poss
            opp_rbs_per_poss = stats['opp_rebounds'] / opp_poss

            second_chance_per_poss = stats['second_chance'] / poss
            opp_second_chance_per_poss = stats['opp_second_chance'] / opp_poss

            fastbreak_per_poss = stats['fastbreak'] / poss
            opp_fastbreak_per_poss = stats['opp_fastbreak'] / opp_poss

            from_turnover_per_poss = stats['from_turnover'] / poss
            opp_from_turnover_per_poss = stats['opp_from_turnover'] / opp_poss

            points_in_paint_per_poss = stats['points_in_paint'] / poss
            opp_points_in_paint_per_poss = stats['opp_points_in_paint'] / opp_poss

            forced_tos_per_poss = stats['opp_turnovers'] / poss
            tos_per_poss = stats['turnovers'] / opp_poss

            e_ORtg = 0.5 * (pts_per_poss+opp_pts_per_poss)
            e_RBS_per_poss = 0.5 * (rbs_per_poss + opp_rbs_per_poss)
            e_secondCh_per_poss = 0.5 * (second_chance_per_poss + opp_second_chance_per_poss)
            e_FBP_per_poss = 0.5 * (fastbreak_per_poss + opp_fastbreak_per_poss)
            e_PtsOffTO_per_poss = 0.5 * (from_turnover_per_poss + opp_from_turnover_per_poss)
            e_PITP_per_poss = 0.5 * (points_in_paint_per_poss + opp_points_in_paint_per_poss)
            e_TO_per_poss = 0.5 * (forced_tos_per_poss + tos_per_poss)
            
            d_ORtg.append(e_ORtg - league_ORtg)
            d_REB_per100.append(e_RBS_per_poss - league_REB_per100)
            d_SecondCh_per100.append(e_secondCh_per_poss - league_SecondCh_per100)
            d_FBP_per100.append(e_FBP_per_poss - league_FBP_per100)
            d_PtsOffTO_per100.append(e_PtsOffTO_per_poss - league_PtsOffTO_per100)
            d_PITP_per100.append(e_PITP_per_poss - league_PITP_per100)
            d_forcedTO_per100.append(e_TO_per_poss - league_forcedTO_per100)

        # Return default values if no data was found
        if len(d_ORtg) == 0 or len(d_REB_per100) == 0 or len(d_SecondCh_per100) == 0 or len(d_FBP_per100) == 0 or len(d_PtsOffTO_per100) == 0 or len(d_PITP_per100) == 0 or len(d_forcedTO_per100) == 0:
            print("Warning: No team data found for standards_values, using defaults")
            return 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0
        
        # order is ORtg, REB_per100, SecondCh_per100, FBP_per100, PtsOffTO_per100, PITP_per100, TO_per100
        return np.mean(d_ORtg), np.mean(d_REB_per100), np.mean(d_SecondCh_per100), np.mean(d_FBP_per100), \
                np.mean(d_PtsOffTO_per100), np.mean(d_PITP_per100), np.mean(d_forcedTO_per100), \
                np.std(d_ORtg, ddof=1), np.std(d_REB_per100, ddof=1), np.std(d_SecondCh_per100, ddof=1), \
                np.std(d_FBP_per100, ddof=1), np.std(d_PtsOffTO_per100, ddof=1), np.std(d_PITP_per100, ddof=1), \
                np.std(d_forcedTO_per100, ddof=1), league_ORtg, league_REB_per100, league_SecondCh_per100, \
                league_FBP_per100, league_PtsOffTO_per100, league_PITP_per100, league_forcedTO_per100

        
    # except Exception as e:
    #     print(f"Error in standards_values(): {e}")
    #     import traceback
    #     traceback.print_exc()
    #     # Return default values on error
    #     return 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0     

def get_team_id_to_abbr():
    # Build a map: TEAM_ID -> "LAL", "BOS", etc.
    return {int(t["id"]): t["abbreviation"] for t in teams.get_teams()}

def get_games_for_date(date_obj: datetime):
    # NBA expects MM/DD/YYYY (Eastern calendar date string), but this works fine for a quick test
    date_str = date_obj.strftime("%m/%d/%Y")
    try:
        sb = scoreboardv2.ScoreboardV2(game_date=date_str)
        games = sb.game_header.get_data_frame()
        return games  # DataFrame with GAME_ID, GAME_DATE_EST, HOME_TEAM_ID, VISITOR_TEAM_ID, GAME_STATUS_TEXT, etc.
    except Exception as e:
        print(f"Error fetching games for date {date_str}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def games():
    try:
        team_map = get_team_id_to_abbr()
        today = date.today().strftime("%Y-%m-%d")
        #change string to datetime
        today = datetime.strptime(today, '%Y-%m-%d')
        print(f"Fetching NBA schedule for {today.strftime('%Y-%m-%d')} ...")

        games_df = get_games_for_date(today)

        if games_df.empty:
            print("No games found for this date.")
            return pd.DataFrame()  # Return empty DataFrame instead of None

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
    except Exception as e:
        print(f"Error in games() function: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()  # Return empty DataFrame on error


def report_data():
    try:
        games_df = games()
        
        # Handle case where no games are found
        if games_df is None or games_df.empty:
            print("No games found for today")
            return pd.DataFrame()

        rows = []
        
        for _, row in games_df.iterrows():
            game_id = row["GAME_ID"]
            home_team = row["HOME_TEAM"]
            away_team = row["VISITOR_TEAM"]
            game_time = row["GAME_TIME"]

            home_csv_path = os.path.join(DATA_DIR, 'S2', f'S2_{home_team}_2025_26.csv')
            away_csv_path = os.path.join(DATA_DIR, 'S2', f'S2_{away_team}_2025_26.csv')
            
            # Skip if files don't exist
            if not os.path.exists(home_csv_path) or not os.path.exists(away_csv_path):
                print(f"Warning: CSV files not found for {home_team} or {away_team}, skipping game {game_id}")
                continue
                
            home_data = pd.read_csv(home_csv_path)
            away_data = pd.read_csv(away_csv_path)

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
                lineup_agg = df.groupby('lineup').agg(FIELDS).reset_index()
                
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

            home_filtered.to_csv("test_data.csv", index=False)

            # Aggregate stats from top 3 lineups
            home_stats = home_filtered.agg(FIELDS)
            away_stats = away_filtered.agg(FIELDS)

            # Calculate per 100 possessions stats
            home_poss = home_stats['possessions'] / 100 if home_stats['possessions'] > 0 else 1
            home_opp_poss = home_stats['opp_possessions'] / 100 if home_stats['opp_possessions'] > 0 else 1
            away_poss = away_stats['possessions'] / 100 if away_stats['possessions'] > 0 else 1
            away_opp_poss = away_stats['opp_possessions'] / 100 if away_stats['opp_possessions'] > 0 else 1

            m1,m2,m3,m4,m5,m6,m7,s1,s2,s3,s4,s5,s6,s7,l1,l2,l3,l4,l5,l6,l7 = standards_values()

            home_pts_per_poss = home_stats['points'] / home_poss
            home_opp_pts_per_poss = home_stats['opp_points'] / home_opp_poss
            away_pts_per_poss = away_stats['points'] / away_poss
            away_opp_pts_per_poss = away_stats['opp_points'] / away_opp_poss

            home_rbs_per_poss = home_stats['rebounds'] / home_poss
            home_opp_rbs_per_poss = home_stats['opp_rebounds'] / home_opp_poss
            away_rbs_per_poss = away_stats['rebounds'] / away_poss
            away_opp_rbs_per_poss = away_stats['opp_rebounds'] / away_opp_poss

            home_second_chance_per_poss = home_stats['second_chance'] / home_poss
            home_opp_second_chance_per_poss = home_stats['opp_second_chance'] / home_opp_poss
            away_second_chance_per_poss = away_stats['second_chance'] / away_poss
            away_opp_second_chance_per_poss = away_stats['opp_second_chance'] / away_opp_poss

            home_fastbreak_per_poss = home_stats['fastbreak'] / home_poss
            home_opp_fastbreak_per_poss = home_stats['opp_fastbreak'] / home_opp_poss
            away_fastbreak_per_poss = away_stats['fastbreak'] / away_poss
            away_opp_fastbreak_per_poss = away_stats['opp_fastbreak'] / away_opp_poss

            home_from_turnover_per_poss = home_stats['from_turnover'] / home_poss
            home_opp_from_turnover_per_poss = home_stats['opp_from_turnover'] / home_opp_poss
            away_from_turnover_per_poss = away_stats['from_turnover'] / away_poss
            away_opp_from_turnover_per_poss = away_stats['opp_from_turnover'] / away_opp_poss

            home_points_in_paint_per_poss = home_stats['points_in_paint'] / home_poss
            home_opp_points_in_paint_per_poss = home_stats['opp_points_in_paint'] / home_opp_poss
            away_points_in_paint_per_poss = away_stats['points_in_paint'] / away_poss
            away_opp_points_in_paint_per_poss = away_stats['opp_points_in_paint'] / away_opp_poss

            home_tos_per_poss = home_stats['turnovers'] / home_poss
            home_forced_tos_per_poss = home_stats['opp_turnovers'] / home_opp_poss
            away_tos_per_poss = away_stats['turnovers'] / away_poss
            away_forced_tos_per_poss = away_stats['opp_turnovers'] / away_opp_poss

            # Part 2: Basic Statistical Comparisons
            # order is ORtg, REB_per100, SecondCh_per100, FBP_per100, PtsOffTO_per100, PITP_per100, TO_per100

            home_edge_1 = ((0.5 * (home_pts_per_poss + away_opp_pts_per_poss) - l1) - m1) / s1
            home_edge_2 = (( 0.5 * (home_rbs_per_poss + away_opp_rbs_per_poss) - l2) - m2) / s2
            home_edge_3 = ((0.5 * (home_second_chance_per_poss + away_opp_second_chance_per_poss) - l3) - m3) / s3
            home_edge_4 = ((0.5 * (home_fastbreak_per_poss + away_opp_fastbreak_per_poss) - l4) - m4) / s4
            home_edge_5 = ((0.5 * (home_from_turnover_per_poss + away_opp_from_turnover_per_poss) - l5) - m5) / s5
            home_edge_6 = ((0.5 * (home_points_in_paint_per_poss + away_opp_points_in_paint_per_poss) - l6) - m6) / s6
            home_edge_7 = ((0.5 * (home_forced_tos_per_poss + away_tos_per_poss) - l7) - m7) / s7

            away_edge_1 = ((0.5 * (away_pts_per_poss + home_opp_pts_per_poss) - l1) - m1) / s1
            away_edge_2 = (( 0.5 * (away_rbs_per_poss + home_opp_rbs_per_poss) - l2) - m2) / s2
            away_edge_3 = ((0.5 * (away_second_chance_per_poss + home_opp_second_chance_per_poss) - l3) - m3) / s3
            away_edge_4 = ((0.5 * (away_fastbreak_per_poss + home_opp_fastbreak_per_poss) - l4) - m4) / s4
            away_edge_5 = ((0.5 * (away_from_turnover_per_poss + home_opp_from_turnover_per_poss) - l5) - m5) / s5
            away_edge_6 = ((0.5 * (away_points_in_paint_per_poss + home_opp_points_in_paint_per_poss) - l6) - m6) / s6
            away_edge_7 = ((0.5 * (away_forced_tos_per_poss + home_tos_per_poss) - l7) - m7) / s7

            edges = [
                {"name": f"{home_team} ORtg", "team": home_team, "advantage": home_edge_1},
                {"name": f"{home_team} REB/100 Poss", "team": home_team, "advantage": home_edge_2},
                {"name": f"{home_team} SecondChance/100 Poss", "team": home_team, "advantage": home_edge_3},
                {"name": f"{home_team} FastBreak/100 Poss", "team": home_team, "advantage": home_edge_4},
                {"name": f"{home_team} PtsOffTurnover/100 Poss", "team": home_team, "advantage": home_edge_5},
                {"name": f"{home_team} PointsInPaint/100 Poss", "team": home_team, "advantage": home_edge_6},
                {"name": f"{home_team} ForcedTO/100 Poss", "team": home_team, "advantage": home_edge_7},

                {"name": f"{away_team} ORtg", "team": away_team, "advantage": away_edge_1},
                {"name": f"{away_team} REB/100 Poss", "team": away_team, "advantage": away_edge_2},
                {"name": f"{away_team} SecondChance/100 Poss", "team": away_team, "advantage": away_edge_3},
                {"name": f"{away_team} FastBreak/100 Poss", "team": away_team, "advantage": away_edge_4},
                {"name": f"{away_team} PtsOffTurnover/100 Poss", "team": away_team, "advantage": away_edge_5},
                {"name": f"{away_team} PointsInPaint/100 Poss", "team": away_team, "advantage": away_edge_6},
                {"name": f"{away_team} ForcedTO/100 Poss", "team": away_team, "advantage": away_edge_7},
            ]
            # Add a column named rank value (absolute value of advantage) and sort by absolute value to get biggest advantages
            for i in range(len(edges)):
                edges[i]['rank_value'] = abs(edges[i]['advantage'])
            edges_sorted = sorted(edges, key=lambda x: x['rank_value'], reverse=True)
            
            # Turn edges_sorted to a DataFrame
            edges_df = pd.DataFrame(edges_sorted)

            # create csv if not created, otherwise append data
            if os.path.exists('test_edges.csv'):
                edges_df.to_csv('test_edges.csv', mode='a', header=False, index=False)
            else:
                edges_df.to_csv('test_edges.csv', index=False)

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
    except Exception as e:
        print(f"Error in report_data(): {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()  # Return empty DataFrame on error


if __name__ == "__main__":
    rep = report_data()    
    print(rep[['EDGE_1', 'EDGE_2', 'EDGE_3', 'EDGE_4']])