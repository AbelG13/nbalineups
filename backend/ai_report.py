"""
AI Report Generation Module
Generates AI-powered pregame reports using Google Gemini API (free tier available)
"""
import os
import json
import pandas as pd
from typing import List, Dict, Optional
from report import report_data
from dotenv import load_dotenv

# Try to import Gemini library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Load environment variables
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, '.env')

# Try loading from backend directory first, then fall back to default behavior
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    load_dotenv()  # Fall back to default behavior (current directory)

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug: Print if API key was found (without showing the actual key)
if GEMINI_API_KEY:
    print(f"✓ GEMINI_API_KEY loaded successfully (length: {len(GEMINI_API_KEY)} characters)")
    print(f"  Looking for .env file at: {ENV_PATH}")
else:
    print(f"✗ GEMINI_API_KEY not found in environment")
    print(f"  Expected .env file location: {ENV_PATH}")
    print(f"  .env file exists: {os.path.exists(ENV_PATH)}")

# Configure Gemini if API key is available
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"✓ Gemini API configured successfully")
    except Exception as e:
        print(f"Warning: Failed to configure Gemini: {e}")


def get_injuries_list() -> List[str]:
    """Load injuries from CSV file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    injuries_path = os.path.join(script_dir, 'data', 'injuries25.csv')
    if os.path.exists(injuries_path):
        df = pd.read_csv(injuries_path)
        return df["NAME"].tolist() if "NAME" in df.columns else []
    return []


def get_game_edges_data(game_id: str, home_team: str, away_team: str, injuries: List[str]) -> Dict:
    """
    Get standardized edges data for a specific game.
    Returns a dictionary with all 14 edges (7 for each team).
    """
    from report import games, standards_values
    import ast
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    home_csv_path = os.path.join(data_dir, 'S2', f'S2_{home_team}_5man_2025_26.csv')
    away_csv_path = os.path.join(data_dir, 'S2', f'S2_{away_team}_5man_2025_26.csv')
    
    if not os.path.exists(home_csv_path) or not os.path.exists(away_csv_path):
        return None
    
    home_data = pd.read_csv(home_csv_path)
    away_data = pd.read_csv(away_csv_path)
    
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
    
    def has_injured_player(lineup_str, injuries_list):
        if not injuries_list:
            return False
        try:
            lineup_tuple = ast.literal_eval(lineup_str)
            players = [p.strip().strip("'\"") for p in lineup_tuple]
            return any(player in injuries_list for player in players)
        except:
            return False
    
    def get_top_lineups(df, injuries_list, top_n=3):
        lineup_agg = df.groupby('lineup').agg(FIELDS).reset_index()
        lineup_agg = lineup_agg[~lineup_agg['lineup'].apply(lambda x: has_injured_player(x, injuries_list))]
        top_lineups = lineup_agg.nlargest(top_n, 'minutes_played')
        return top_lineups['lineup'].tolist(), top_lineups
    
    home_top_lineups, _ = get_top_lineups(home_data, injuries, 3)
    away_top_lineups, _ = get_top_lineups(away_data, injuries, 3)
    
    home_filtered = home_data[home_data['lineup'].isin(home_top_lineups)]
    away_filtered = away_data[away_data['lineup'].isin(away_top_lineups)]
    
    home_stats = home_filtered.agg(FIELDS)
    away_stats = away_filtered.agg(FIELDS)
    
    home_poss = home_stats['possessions'] / 100 if home_stats['possessions'] > 0 else 1
    home_opp_poss = home_stats['opp_possessions'] / 100 if home_stats['opp_possessions'] > 0 else 1
    away_poss = away_stats['possessions'] / 100 if away_stats['possessions'] > 0 else 1
    away_opp_poss = away_stats['opp_possessions'] / 100 if away_stats['opp_possessions'] > 0 else 1
    
    m1, m2, m3, m4, m5, m6, m7, s1, s2, s3, s4, s5, s6, s7, l1, l2, l3, l4, l5, l6, l7 = standards_values()
    
    # Calculate per 100 possession stats
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
    
    # Calculate standardized edges
    home_edge_1 = ((0.5 * (home_pts_per_poss + away_opp_pts_per_poss) - l1) - m1) / s1
    home_edge_2 = ((0.5 * (home_rbs_per_poss + away_opp_rbs_per_poss) - l2) - m2) / s2
    home_edge_3 = ((0.5 * (home_second_chance_per_poss + away_opp_second_chance_per_poss) - l3) - m3) / s3
    home_edge_4 = ((0.5 * (home_fastbreak_per_poss + away_opp_fastbreak_per_poss) - l4) - m4) / s4
    home_edge_5 = ((0.5 * (home_from_turnover_per_poss + away_opp_from_turnover_per_poss) - l5) - m5) / s5
    home_edge_6 = ((0.5 * (home_points_in_paint_per_poss + away_opp_points_in_paint_per_poss) - l6) - m6) / s6
    home_edge_7 = ((0.5 * (home_forced_tos_per_poss + away_tos_per_poss) - l7) - m7) / s7
    
    away_edge_1 = ((0.5 * (away_pts_per_poss + home_opp_pts_per_poss) - l1) - m1) / s1
    away_edge_2 = ((0.5 * (away_rbs_per_poss + home_opp_rbs_per_poss) - l2) - m2) / s2
    away_edge_3 = ((0.5 * (away_second_chance_per_poss + home_opp_second_chance_per_poss) - l3) - m3) / s3
    away_edge_4 = ((0.5 * (away_fastbreak_per_poss + home_opp_fastbreak_per_poss) - l4) - m4) / s4
    away_edge_5 = ((0.5 * (away_from_turnover_per_poss + home_opp_from_turnover_per_poss) - l5) - m5) / s5
    away_edge_6 = ((0.5 * (away_points_in_paint_per_poss + home_opp_points_in_paint_per_poss) - l6) - m6) / s6
    away_edge_7 = ((0.5 * (away_forced_tos_per_poss + home_tos_per_poss) - l7) - m7) / s7
    
    edges = [
        {"stat": "ORtg", "team": home_team, "value": home_edge_1},
        {"stat": "REB/100 Poss", "team": home_team, "value": home_edge_2},
        {"stat": "SecondChance/100 Poss", "team": home_team, "value": home_edge_3},
        {"stat": "FastBreak/100 Poss", "team": home_team, "value": home_edge_4},
        {"stat": "PtsOffTurnover/100 Poss", "team": home_team, "value": home_edge_5},
        {"stat": "PointsInPaint/100 Poss", "team": home_team, "value": home_edge_6},
        {"stat": "ForcedTO/100 Poss", "team": home_team, "value": home_edge_7},
        {"stat": "ORtg", "team": away_team, "value": away_edge_1},
        {"stat": "REB/100 Poss", "team": away_team, "value": away_edge_2},
        {"stat": "SecondChance/100 Poss", "team": away_team, "value": away_edge_3},
        {"stat": "FastBreak/100 Poss", "team": away_team, "value": away_edge_4},
        {"stat": "PtsOffTurnover/100 Poss", "team": away_team, "value": away_edge_5},
        {"stat": "PointsInPaint/100 Poss", "team": away_team, "value": away_edge_6},
        {"stat": "ForcedTO/100 Poss", "team": away_team, "value": away_edge_7},
    ]
    
    return {
        "game_id": game_id,
        "home_team": home_team,
        "away_team": away_team,
        "edges": edges
    }


def format_edges_for_ai(edges_data: Dict) -> str:
    """Format edges data as a readable string for AI."""
    if not edges_data or not edges_data.get("edges"):
        return "No edges data available"
    
    lines = []
    for edge in sorted(edges_data["edges"], key=lambda x: abs(x["value"]), reverse=True):
        stat_name = edge["stat"]
        team = edge["team"]
        value = edge["value"]
        lines.append(f"{team} {stat_name}: {value:.3f}")
    
    return "\n".join(lines)


def generate_ai_report(game_id: str, home_team: str, away_team: str) -> Optional[str]:
    """
    Generate AI report for a game using Google Gemini API (free tier available).
    
    Args:
        game_id: NBA game ID
        home_team: Home team abbreviation
        away_team: Away team abbreviation
    
    Returns:
        AI-generated report text or None if error
    """
    # Get the three inputs
    injuries = get_injuries_list()
    no_injuries = []
    
    # Get edges with injuries
    edges_with_injuries = get_game_edges_data(game_id, home_team, away_team, injuries)
    
    # Get edges without injuries
    edges_without_injuries = get_game_edges_data(game_id, home_team, away_team, no_injuries)
    
    if not edges_with_injuries or not edges_without_injuries:
        return None
    
    # Format data for AI
    injuries_text = ", ".join(injuries) if injuries else "No injuries reported"
    edges_with_injuries_text = format_edges_for_ai(edges_with_injuries)
    edges_without_injuries_text = format_edges_for_ai(edges_without_injuries)
    
    # Create prompt
    prompt = f"""You are an expert NBA analyst providing concise, data-driven betting insights.

Game: {away_team} @ {home_team}

INJURED PLAYERS:
{injuries_text}

STANDARDIZED EDGES (with injuries - current):
{edges_with_injuries_text}

STANDARDIZED EDGES (without injuries - baseline):
{edges_without_injuries_text}

These standardized values are z-scores (std deviations from league average). Reference exact values when citing edges.

RESPONSE RULES (follow strictly):
- Output only bullet points using the dot character "•" (no intro/outro text).
- Exactly 4 or 5 bullets total.
- First 3-4 bullets: matchup takeaways. Each bullet <= 2 short sentences, must cite specific teams/stats/values.
- Last bullet reserved for betting advice, begin with "• Betting angle:" and tie directly to the cited stats.
- Be concise, factual, and base every claim on the provided edges/injuries."""
    
    try:
        if not GEMINI_API_KEY:
            return "Error: GEMINI_API_KEY not configured. Please set it in your .env file. Get a free API key at https://makersuite.google.com/app/apikey"
        
        if not GEMINI_AVAILABLE:
            return "Error: Google Generative AI library not installed. Please install with: pip install google-generativeai"
        
        model_names_to_try = [
            'gemini-2.5-flash',      # Latest and fastest
            'gemini-2.0-flash',      # Stable 2.0 version
            'gemini-2.5-pro',        # Latest pro version
            'gemini-2.0-flash-exp'   # Experimental 2.0
        ]
        
        for model_name in model_names_to_try:
            try:
                print(f"Trying model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                print(f"✓ Successfully used model: {model_name}")
                return response.text
            except Exception as e:
                error_msg = str(e)
                print(f"⚠ {model_name} failed: {error_msg[:150]}")
                # Continue to next model
                continue
        
        # If all models failed, list available models and raise error
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name.split('/')[-1]
                    available_models.append(model_name)
        except Exception:
            pass
        
        available_info = f"Available models: {', '.join(available_models[:10])}" if available_models else "Could not list available models"
        raise Exception(
            f"All Gemini models failed. Tried: {', '.join(model_names_to_try)}. "
            f"{available_info}. "
            f"Please check your API key permissions and model availability."
        )
    except Exception as e:
        print(f"Error generating AI report: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating report: {str(e)}"


def get_ai_reports_for_all_games() -> Dict[str, str]:
    """
    Generate AI reports for all games today using Gemini API.
    Returns a dictionary mapping game_id to report text.
    """
    from report import games
    
    games_df = games()
    if games_df is None or games_df.empty:
        return {}
    
    reports = {}
    for _, row in games_df.iterrows():
        game_id = str(row["GAME_ID"])
        home_team = row["HOME_TEAM"]
        away_team = row["VISITOR_TEAM"]
        
        report = generate_ai_report(game_id, home_team, away_team)
        if report:
            reports[game_id] = report
    
    return reports

