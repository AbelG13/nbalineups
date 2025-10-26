# test_schedule_simple.py
from datetime import datetime
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams

def get_team_id_to_abbr():
    # Build a map: TEAM_ID -> "LAL", "BOS", etc.
    return {int(t["id"]): t["abbreviation"] for t in teams.get_teams()}

def get_games_for_date_very_simple(date_obj: datetime):
    # NBA expects MM/DD/YYYY (Eastern calendar date string), but this works fine for a quick test
    date_str = date_obj.strftime("%m/%d/%Y")
    sb = scoreboardv2.ScoreboardV2(game_date=date_str)

    games = sb.game_header.get_data_frame()
    return games  # DataFrame with GAME_ID, GAME_DATE_EST, HOME_TEAM_ID, VISITOR_TEAM_ID, GAME_STATUS_TEXT, etc.

def main():
    team_map = get_team_id_to_abbr()
    today = '2025-10-8'
    #change string to datetime
    today = datetime.strptime(today, '%Y-%m-%d')
    print(today, type(today))

    #print(f"\nFetching NBA schedule for {today.strftime('%Y-%m-%d')} ...")
    games_df = get_games_for_date_very_simple(today)

    if games_df.empty:
        print("No games found for this date.")
        return

    # Print a minimal, readable summary
    for _, row in games_df.iterrows():
        game_id = row["GAME_ID"]
        home = team_map.get(int(row["HOME_TEAM_ID"]), row["HOME_TEAM_ID"])
        away = team_map.get(int(row["VISITOR_TEAM_ID"]), row["VISITOR_TEAM_ID"])
        status = row.get("GAME_STATUS_TEXT", "")  # pre-game: "7:30 pm ET", or "Final", etc.
        est_when = row.get("GAME_DATE_EST", "")   # raw string from NBA (Eastern time)

        print(f"- {away} @ {home} | status: {status} | GAME_DATE_EST: {est_when} | game_id: {game_id}")

if __name__ == "__main__":
    main()
