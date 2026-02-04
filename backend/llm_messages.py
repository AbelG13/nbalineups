import json
import pandas as pd
from nba_api.stats.endpoints import LeagueGameLog

from report import report_data

# --------------------------------------------------------------------
# Injuries list
# --------------------------------------------------------------------
INJURIES = pd.read_csv("data/injuries25.csv")["NAME"].tolist()

# --------------------------------------------------------------------
# League game log cache (for last 5 results)
# --------------------------------------------------------------------
GAME_LOG_DF = None
SEASON = "2025-26"  # adjust if needed


def get_last_5_results(team_abbreviation: str):
    """
    Return last 5 results for a team as a list of short strings.
    Uses LeagueGameLog filtered by TEAM_ABBREVIATION, sorted by GAME_DATE.
    """
    global GAME_LOG_DF

    if GAME_LOG_DF is None:
        log = LeagueGameLog(
            season=SEASON,
            league_id="00",
            player_or_team_abbreviation="T"
        )
        GAME_LOG_DF = log.get_data_frames()[0]

    df_team = GAME_LOG_DF[GAME_LOG_DF["TEAM_ABBREVIATION"] == team_abbreviation]

    if df_team.empty:
        print('last 5 df returned empty')
        return []

    df_team = df_team.sort_values("GAME_DATE", ascending=False).head(5)

    results = []
    for _, row in df_team.iterrows():
        wl = row.get("WL", "")
        matchup = row.get("MATCHUP", "")
        plus_minus = row.get("PLUS_MINUS", "")
        results.append(f"Matchup: {matchup}, Result: {wl}, Plus Minus: {plus_minus}")

    return results


# --------------------------------------------------------------------
# Metric parsing helpers
# --------------------------------------------------------------------
def parse_edge_string(edge_str: str):
    """
    Input example: "CLE ORtg 1.310"
    Output: {"team": "CLE", "stat": "ORtg", "value": 1.31}
    """
    if not isinstance(edge_str, str) or edge_str.strip() == "":
        return None

    parts = edge_str.rsplit(" ", 1)
    if len(parts) != 2:
        return None

    left, val_str = parts
    try:
        value = float(val_str)
    except Exception:
        return None

    left_parts = left.split(" ", 1)
    if len(left_parts) != 2:
        return None

    team, stat = left_parts
    return {"team": team, "stat": stat, "value": round(value, 2)}


def extract_top_metrics(row: pd.Series, limit: int = 8):
    """
    Extract up to `limit` EDGE_i fields from a row and parse them.
    Assumes columns EDGE_1, EDGE_2, ..., EDGE_12 exist.
    """
    metrics = []
    for i in range(1, 13):  # EDGE_1 ... EDGE_12
        col = f"EDGE_{i}"
        if col in row and isinstance(row[col], str) and row[col] != "":
            parsed = parse_edge_string(row[col])
            if parsed:
                metrics.append(parsed)
        if len(metrics) >= limit:
            break
    return metrics


# --------------------------------------------------------------------
# Build LLM message for a single game (two rows: with and without injuries)
# --------------------------------------------------------------------
def build_message_for_game(row_inj: pd.Series, row_noinj: pd.Series):
    game_id = row_inj["GAME_ID"]
    home = row_inj["HOME_TEAM"]
    away = row_inj["VISITOR_TEAM"]

    # Last 5 results
    last5_home = get_last_5_results(home)
    last5_away = get_last_5_results(away)

    # Metrics: baseline from no-injury report, adjusted from injury report
    baseline_metrics = extract_top_metrics(row_noinj, limit=8)
    injury_adjusted_metrics = extract_top_metrics(row_inj, limit=8)

    # Injuries (simple list of names, no team split in this CSV)
    # If you later split by team, you can adjust this section accordingly.
    # For now we just supply the global list to both as "context".
    # If you track team per injury, replace this with team-specific filtering.
    injuries_home = []  # placeholder until you structure injuries by team
    injuries_away = []

    llm_payload = {
        "instructions": {
            "role": "analysis_engine",
            "task": "Analyze an upcoming NBA matchup using the structured data provided.",
            "goals": [
                "Identify the most influential statistical advantages and weaknesses.",
                "Interpret interactions between strong metrics (rebounds -> second-chance points, turnovers -> transition scoring).",
                "Explain how injuries change the expected game flow compared to the baseline.",
                "Describe game-level trends such as pace, scoring environment, paint vs perimeter scoring, turnover volatility, and physicality.",
                "Do NOT predict winners and do NOT produce player prop lines.",
                "Focus only on game style and tendencies."
            ],
            "metric_definition": "All metrics are standardized (z-scores). Higher absolute values indicate stronger advantages. Positive values indicate advantages for the listed team.",
            "home_away_note": "Home-court advantage is minor context. Use lightly.",
            "recent_form_note": "Last 5 games show form but should not dominate the analysis.",
            "output_requirements": [
                "Be concise but substantive.",
                "Ground conclusions directly in the provided metrics.",
                "Highlight only trends with strong statistical support."
            ]
        },
        "game_data": {
            "game_id": game_id,
            "home_team": home,
            "away_team": away,
            "game_time": row_inj.get("GAME_TIME", ""),
            "last_5_games": {
                "home_team_results": last5_home,
                "away_team_results": last5_away,
            },
            "metrics": {
                "baseline_top8": baseline_metrics,
                "injury_adjusted_top8": injury_adjusted_metrics,
            },
            "injuries": {
                "home_team_out": injuries_home,
                "away_team_out": injuries_away,
            },
        },
    }

    return llm_payload


# --------------------------------------------------------------------
# Build messages for all games
# --------------------------------------------------------------------
def build_first_message():
    # With injuries
    df_inj = report_data(INJURIES)
    # Without injuries
    df_noinj = report_data([])

    # Use GAME_ID as the join key
    df_noinj_indexed = df_noinj.set_index("GAME_ID")

    messages = {}

    for _, row_inj in df_inj.iterrows():
        game_id = row_inj["GAME_ID"]

        row_noinj = df_noinj_indexed.loc[game_id]

        msg = build_message_for_game(row_inj, row_noinj)
        messages[str(game_id)] = msg

    return messages


# --------------------------------------------------------------------
# SECOND MESSAGE (player-prop oriented)
# --------------------------------------------------------------------

PLAYER_LOG_DF = None  # cached player-level game log


def load_player_log():
    """
    Load and cache LeagueGameLog at player level for the current season.
    """
    global PLAYER_LOG_DF
    if PLAYER_LOG_DF is not None:
        return PLAYER_LOG_DF

    log = LeagueGameLog(
        season=SEASON,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation="P",  # player rows
    )
    df = log.get_data_frames()[0]
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    PLAYER_LOG_DF = df
    return df


def get_last3_boxscores(player_name: str):
    """
    Return last 3 box scores for a player as a list of simple dicts.
    """
    df = load_player_log()
    df_p = df[df["PLAYER_NAME"] == player_name]

    if df_p.empty:
        return []

    df_p = df_p.sort_values("GAME_DATE", ascending=False).head(3)

    out = []
    for _, r in df_p.iterrows():
        matchup = r.get("MATCHUP", "")

        # Determine home/away + opponent from MATCHUP like "BOS vs. MIA" or "BOS @ MIA"
        if "vs." in matchup:
            home_away = "home"
            opponent = matchup.split("vs.")[-1].strip()
        elif "@" in matchup:
            home_away = "away"
            opponent = matchup.split("@")[-1].strip()
        else:
            print("error in llm message 2")
            home_away = ""
            opponent = ""

        out.append(
            {
                "date": r["GAME_DATE"].strftime("%Y-%m-%d"),
                "team": r.get("TEAM_ABBREVIATION", ""),
                "opponent": opponent,
                "home_away": home_away,
                "minutes": r.get("MIN", None),
                "points": r.get("PTS", None),
                "rebounds": r.get("REB", None),
                "assists": r.get("AST", None),
                "field goals attempted": r.get("FGA", None),
                "turnovers": r.get("TOV", None),
            }
        )

    return out


def get_home_away_players(row: pd.Series):
    """
    Extract unique player names separately for home and away teams
    from HOME_LINEUP_1..3 and AWAY_LINEUP_1..3.
    """
    home = set()
    away = set()

    home_cols = ["HOME_LINEUP_1", "HOME_LINEUP_2", "HOME_LINEUP_3"]
    away_cols = ["AWAY_LINEUP_1", "AWAY_LINEUP_2", "AWAY_LINEUP_3"]

    # Home players
    for col in home_cols:
        if col in row and isinstance(row[col], str):
            for name in row[col].split(","):
                name = name.strip()
                if name:
                    home.add(name)

    # Away players
    for col in away_cols:
        if col in row and isinstance(row[col], str):
            for name in row[col].split(","):
                name = name.strip()
                if name:
                    away.add(name)

    return sorted(home), sorted(away)


def build_second_message_for_game(row: pd.Series, game_trend_analysis: str):
    """
    Build the second LLM payload for a single game.

    Inputs:
      - row: one row from report_data(...) containing GAME_ID, HOME/ AWAY lineups, etc.
      - game_trend_analysis: text output from the first LLM call for this game.
    """
    game_id = str(row["GAME_ID"])
    home_team = row["HOME_TEAM"]
    away_team = row["VISITOR_TEAM"]

    home_players, away_players = get_home_away_players(row)

    # Attach last 3 games per player
    home_payload = []
    for name in home_players:
        home_payload.append(
            {
                "name": name,
                "last_3_games": get_last3_boxscores(name),
            }
        )

    away_payload = []
    for name in away_players:
        away_payload.append(
            {
                "name": name,
                "last_3_games": get_last3_boxscores(name),
            }
        )

    payload = {
        "instructions": {
            "role": "player_prop_analyst",
            "task": (
                "Use the provided game trend analysis and recent player box scores to determine "
                "which players are likely to perform above or below their usual levels in specific "
                "statistical categories."
            ),
            "output_requirements": [
                "Your final output must ONLY be a list of entries in the exact format: "
                "`Player Name – [Stat Category] – Over/Under – Confidence Score`.",
                "Confidence Score must be an integer from 1 to 10 reflecting how strongly the "
                "game trends and recent box scores support the prediction.",
                "Provide 3–5 angles per team.",
                "Do NOT include explanations, reasoning, or analysis. Only output the final list.",
                "Keep the output concise, user-friendly, and free of extra commentary."
            ],
        },
        "game_data": {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
        },
        "trend_analysis": game_trend_analysis,
        "players": {
            "home": home_payload,
            "away": away_payload,
        },
    }

    return payload


def build_all_second_messages(first_layer_outputs: dict):
    """
    Build second-message payloads for all games.

    Parameters
    ----------
    first_layer_outputs : dict
        Maps game_id (str) -> text from the first LLM call.

    Returns
    -------
    dict
        { game_id (str): second_message_payload_dict }
    """
    # You can change INJURIES to [] if you want the no-injury report instead.
    df = report_data(INJURIES)
    messages = {}

    for _, row in df.iterrows():
        game_id = str(row["GAME_ID"])
        game_trend_analysis = first_layer_outputs.get(game_id, "")

        payload = build_second_message_for_game(row, game_trend_analysis)
        messages[game_id] = payload

    return messages