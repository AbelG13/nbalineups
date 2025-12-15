from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
import sys

# Allow importing from backend root (for report module)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = CURRENT_DIR
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

# Set data directory path
DATA_DIR = os.path.join(BACKEND_ROOT, 'data')

try:
    from report import report_data
except Exception as e:
    print(f"Warning: Could not import report_data from report module: {e}")
    import traceback
    traceback.print_exc()
    report_data = None

try:
    from ai_report import generate_ai_report, get_ai_reports_for_all_games
except Exception as e:
    print(f"Warning: Could not import AI report functions: {e}")
    import traceback
    traceback.print_exc()
    generate_ai_report = None
    get_ai_reports_for_all_games = None

app = FastAPI()

@app.get("/")
def root():
    return {"message": "NBA Lineups backend running"}


@app.get("/players")
def get_players():
    try:
        csv_path = os.path.join(DATA_DIR, "active25.csv")
        df = pd.read_csv(csv_path)
        df['image_url'] = df['player_id'].apply(lambda x: f"https://cdn.nba.com/headshots/nba/latest/1040x760/{x}.png")
        df = df.fillna("N/A")  # Replace NaN 
        players = df.to_dict(orient="records")
        return JSONResponse(content=players)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/lineup-stats/{team}")
def get_lineup_stats(
    team: str,
    season: Optional[str] = Query("2024-25", description="Season (2024-25 or 2025-26)"),
    periods: Optional[str] = Query(None, description="Filter by periods (1-5) as comma-separated string"),
    game_min: Optional[int] = Query(1, description="Minimum game number"),
    game_max: Optional[int] = Query(82, description="Maximum game number"),
    lineup_size: Optional[int] = Query(5, description="Lineup size (2, 3, 4, or 5)")
):
    try:
        # Parse periods string into list of integers
        periods_list = None
        if periods:
            periods_list = [int(p.strip()) for p in periods.split(',')]
        
        # Debug: Print received parameters
        print(f"Team: {team}")
        print(f"Season: {season}")
        print(f"Periods string: {periods}")
        print(f"Periods list: {periods_list}")
        print(f"Game range: {game_min} - {game_max}")
        
        # Construct the CSV file path based on season and lineup size
        if season == "2024-25":
            # 2024-25 only has 5-man lineups
            csv_path = os.path.join(DATA_DIR, "S1", f"S1_{team}_2024_25.csv")
        elif season == "2025-26":
            # Validate lineup size
            if lineup_size not in [2, 3, 4, 5]:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid lineup_size: {lineup_size}. Must be 2, 3, 4, or 5"}
                )
            csv_path = os.path.join(DATA_DIR, "S2", f"S2_{team}_{lineup_size}man_2025_26.csv")
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid season: {season}. Must be '2024-25' or '2025-26'"}
            )
        
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            return JSONResponse(content=[])
        
        # Read the CSV file
        df = pd.read_csv(csv_path)
        print(f"Total rows before filtering: {len(df)}")
        
        # Apply filters
        if periods_list:
            print(f"Filtering by periods: {periods_list}")
            df = df[df['period'].isin(periods_list)]
            print(f"Rows after period filtering: {len(df)}")
        
        df = df[(df['game_number'] >= game_min) & (df['game_number'] <= game_max)]
        print(f"Rows after game range filtering: {len(df)}")
        
        # Aggregate by lineup
        if not df.empty:
            # Base aggregation dictionary
            agg_dict = {
                'points': 'sum',
                'opp_points': 'sum',
                'rebounds': 'sum',
                'opp_rebounds': 'sum',
                'assists': 'sum',
                'opp_assists': 'sum',
                'turnovers': 'sum',
                'opp_turnovers': 'sum',
                'fouls_committed': 'sum',
                'fouls_drawn': 'sum',
                'minutes_played': 'sum',
                'team_avg_height': 'first',
                'team': 'first',
                'opponent': 'first'
            }
            
            # Add advanced stats if they exist in the CSV (for 2025-26 season)
            advanced_fields = [
                'possessions', 'opp_possessions',
                'fastbreak', 'opp_fastbreak',
                'from_turnover', 'opp_from_turnover',
                'second_chance', 'opp_second_chance',
                'points_in_paint', 'opp_points_in_paint',
                'unscaled_pace'
            ]
            
            for field in advanced_fields:
                if field in df.columns:
                    agg_dict[field] = 'sum'
            
            aggregated = df.groupby('lineup').agg(agg_dict).reset_index()
            
            # Add net columns
            aggregated['net_points'] = aggregated['points'] - aggregated['opp_points']
            aggregated['net_rebounds'] = aggregated['rebounds'] - aggregated['opp_rebounds']
            aggregated['net_assists'] = aggregated['assists'] - aggregated['opp_assists']
            aggregated['net_turnovers'] = aggregated['turnovers'] - aggregated['opp_turnovers']
            aggregated['net_fouls'] = aggregated['fouls_committed'] - aggregated['fouls_drawn']
            
            # Convert to list of dictionaries
            data = aggregated.to_dict('records')
            print(f"Final aggregated lineups: {len(data)}")
        else:
            data = []
        
        return JSONResponse(content=data)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error loading lineup stats for {team}: {str(e)}"}
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pregame reports endpoint
@app.get("/pregame-reports")
def get_pregame_reports():
    try:
        if report_data is None:
            return JSONResponse(status_code=500, content={"error": "report_data not available"})
        df = report_data()
        # Ensure DataFrame exists
        if df is None or df.empty:
            return JSONResponse(content=[])
        return JSONResponse(content=df.to_dict(orient="records"))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_pregame_reports: {error_details}")
        return JSONResponse(status_code=500, content={"error": str(e), "details": error_details})

# AI report endpoint for a specific game
@app.get("/ai-report/{game_id}")
def get_ai_report(
    game_id: str,
    home_team: Optional[str] = Query(None, description="Home team abbreviation (optional, will lookup if not provided)"),
    away_team: Optional[str] = Query(None, description="Away team abbreviation (optional, will lookup if not provided)")
):
    try:
        if generate_ai_report is None:
            return JSONResponse(status_code=500, content={"error": "AI report generation not available"})
        
        # If team info is provided, use it directly (more reliable)
        if home_team and away_team:
            report = generate_ai_report(game_id, home_team, away_team)
            if report is None:
                return JSONResponse(status_code=500, content={"error": "Failed to generate AI report"})
            return JSONResponse(content={"game_id": game_id, "home_team": home_team, "away_team": away_team, "report": report})
        
        # Otherwise, try to lookup from pregame reports
        if report_data is None:
            return JSONResponse(status_code=500, content={"error": "report_data not available and team info not provided"})
        
        df = report_data()
        if df is None or df.empty:
            return JSONResponse(status_code=404, content={"error": "No games found. Please provide home_team and away_team query parameters."})
        
        # Find the game - handle both string and int game_id formats
        # NBA game IDs can be strings like "0022501216" or integers
        if 'GAME_ID' not in df.columns:
            return JSONResponse(status_code=500, content={"error": "GAME_ID column not found in reports"})
        
        # Normalize both sides for comparison - convert to string and strip any whitespace
        game_id_str = str(game_id).strip()
        
        # Try multiple matching strategies
        # Strategy 1: Direct string match
        game_row = df[df['GAME_ID'].astype(str).str.strip() == game_id_str]
        
        # Strategy 2: If no match and game_id looks numeric, try integer comparison
        if game_row.empty and game_id_str.isdigit():
            try:
                game_id_int = int(game_id_str)
                # Try matching as integer (handles cases where leading zeros were lost)
                game_row = df[df['GAME_ID'].astype(int) == game_id_int]
                # Also try matching where we pad with zeros (NBA game IDs are typically 10 digits)
                if game_row.empty and len(game_id_str) < 10:
                    padded_id = game_id_str.zfill(10)
                    game_row = df[df['GAME_ID'].astype(str).str.zfill(10) == padded_id]
            except (ValueError, TypeError):
                pass
        
        if game_row.empty:
            # Debug: print available game IDs to help troubleshoot
            available_ids = df['GAME_ID'].astype(str).tolist() if not df.empty else []
            print(f"Game ID lookup failed. Looking for: '{game_id}' (received as {type(game_id).__name__})")
            print(f"Available game IDs in report ({len(available_ids)}): {available_ids}")
            return JSONResponse(
                status_code=404, 
                content={
                    "error": f"Game {game_id} not found in today's games. Please provide home_team and away_team as query parameters.",
                    "available_game_ids": available_ids,  # Show all for debugging
                    "debug": {
                        "searched_for": game_id_str,
                        "total_games": len(df)
                    }
                }
            )
        
        home_team = game_row.iloc[0]['HOME_TEAM']
        away_team = game_row.iloc[0]['VISITOR_TEAM']
        
        report = generate_ai_report(game_id, home_team, away_team)
        if report is None:
            return JSONResponse(status_code=500, content={"error": "Failed to generate AI report"})
        
        return JSONResponse(content={"game_id": game_id, "home_team": home_team, "away_team": away_team, "report": report})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_ai_report: {error_details}")
        return JSONResponse(status_code=500, content={"error": str(e), "details": error_details})

# AI reports for all games today
@app.get("/ai-reports")
def get_all_ai_reports():
    try:
        if get_ai_reports_for_all_games is None:
            return JSONResponse(status_code=500, content={"error": "AI report generation not available"})
        
        reports = get_ai_reports_for_all_games()
        return JSONResponse(content=reports)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_all_ai_reports: {error_details}")
        return JSONResponse(status_code=500, content={"error": str(e), "details": error_details})

