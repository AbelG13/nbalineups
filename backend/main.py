from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
import sys
import ast
from itertools import product

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

app = FastAPI()


def parse_lineup_cell(lineup_val):
    """Parse lineup column value (string tuple/list or already list) into set of player names."""
    if pd.isna(lineup_val) or (isinstance(lineup_val, str) and lineup_val.strip().lower() in ('nan', '')):
        return set()
    if isinstance(lineup_val, (list, tuple)):
        return set(p.strip().strip("'\"") for p in lineup_val)
    if isinstance(lineup_val, str):
        try:
            raw = ast.literal_eval(lineup_val)
            return set(p.strip().strip("'\"") for p in raw)
        except (SyntaxError, ValueError):
            return set()
    return set()


def lineup_matches(lineup_players, on_players, off_players):
    """Check if lineup set contains all on_players and none of off_players."""
    lineup_set = {p.strip() for p in lineup_players}
    on_set = set(on_players)
    off_set = set(off_players)
    if on_set and not on_set.issubset(lineup_set):
        return False
    if off_set and lineup_set.intersection(off_set):
        return False
    return True


def _json_serializable(val):
    """Convert numpy/pandas scalars to native Python for JSON."""
    if hasattr(val, "item"):
        return val.item()
    if isinstance(val, (list, tuple)):
        return [_json_serializable(x) for x in val]
    if isinstance(val, dict):
        return {k: _json_serializable(v) for k, v in val.items()}
    return val


def _take_first(series):
    """Return first element of a Series. Used for agg when no groupby (string 'first' fails in some pandas)."""
    return series.iloc[0]


@app.get("/")
def root():
    return {"message": "NBA Lineups backend running"}


@app.get("/players")
def get_players():
    try:
        csv_path = os.path.join(DATA_DIR, "active25.csv")
        df = pd.read_csv(csv_path)
        # Deduplicate by player_id so consumers (e.g. Lineup Builder) get unique keys
        df = df.drop_duplicates(subset=["player_id"], keep="first")
        df["image_url"] = df["player_id"].apply(lambda x: f"https://cdn.nba.com/headshots/nba/latest/1040x760/{x}.png")
        df = df.fillna("N/A")
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


@app.get("/lineup-stats/{team}/on-off")
def get_lineup_stats_on_off(
    team: str,
    season: Optional[str] = Query("2025-26", description="Season (2025-26 only for on/off)"),
    periods: Optional[str] = Query(None, description="Filter by periods (1-5) as comma-separated string"),
    game_min: Optional[int] = Query(1, description="Minimum game number"),
    game_max: Optional[int] = Query(82, description="Maximum game number"),
    players: Optional[str] = Query(None, description="Comma-separated player names for on/off combinations"),
):
    """Same flow as get_lineup_stats: load CSV, apply filters, then aggregate.
    Difference: we filter by lineup (on/off combination) first per record, then aggregate to one row per combination.
    Build a table of records (one per combination) with same stat columns as normal + on_players, off_players, combination.
    """
    try:
        if season != "2025-26":
            return JSONResponse(
                status_code=400,
                content={"error": "On/Off feature is only available for 2025-26 season (5-man data)."}
            )
        player_list = [p.strip() for p in (players or "").split(",") if p.strip()]
        if not player_list:
            return JSONResponse(content=[])

        # Same path as normal 5-man 2025-26
        csv_path = os.path.join(DATA_DIR, "S2", f"S2_{team}_5man_2025_26.csv")
        if not os.path.exists(csv_path):
            return JSONResponse(content=[])

        df = pd.read_csv(csv_path)
        if df.empty:
            return JSONResponse(content=[])

        # Same filters as normal get_lineup_stats: periods, then game_number
        periods_list = None
        if periods:
            periods_list = [int(p.strip()) for p in periods.split(",")]
        if periods_list:
            df = df[df["period"].isin(periods_list)]
        df = df[(df["game_number"] >= game_min) & (df["game_number"] <= game_max)]
        if df.empty:
            return JSONResponse(content=[])

        # Parse lineup column for filtering (string tuple -> set of player names)
        df = df.copy()
        df["_lineup_set"] = df["lineup"].map(parse_lineup_cell)

        # Same agg_dict as get_lineup_stats: only columns that exist
        agg_dict = {
            "points": "sum",
            "opp_points": "sum",
            "rebounds": "sum",
            "opp_rebounds": "sum",
            "assists": "sum",
            "opp_assists": "sum",
            "turnovers": "sum",
            "opp_turnovers": "sum",
            "fouls_committed": "sum",
            "fouls_drawn": "sum",
            "minutes_played": "sum",
            "team_avg_height": "first",
            "team": "first",
            "opponent": "first",
        }
        advanced_fields = [
            "possessions", "opp_possessions",
            "fastbreak", "opp_fastbreak",
            "from_turnover", "opp_from_turnover",
            "second_chance", "opp_second_chance",
            "points_in_paint", "opp_points_in_paint",
            "unscaled_pace",
        ]
        for field in advanced_fields:
            if field in df.columns:
                agg_dict[field] = "sum"
        # Only aggregate columns that exist in df (avoid KeyError)
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

        # Build list of combinations (on_players, off_players)
        combinations = []
        for bits in product([True, False], repeat=len(player_list)):
            on_players = [player_list[i] for i, b in enumerate(bits) if b]
            off_players = [player_list[i] for i, b in enumerate(bits) if not b]
            combinations.append((on_players, off_players))

        # One record per combination: filter by lineup, then aggregate (same as normal but no groupby)
        rows = []
        for on_players, off_players in combinations:
            mask = df["_lineup_set"].apply(
                lambda s: lineup_matches(s, on_players, off_players) if isinstance(s, set) else False
            )
            sub = df.loc[mask]
            if sub.empty:
                row = _on_off_empty_row(team, list(agg_dict.keys()), on_players, off_players, player_list)
            else:
                # Drop lineup columns so agg only sees numeric/categorical
                sub_agg = sub.drop(columns=["lineup", "_lineup_set"], errors="ignore")
                # Use callable for 'first' (DataFrame.agg with 'first' string can fail without groupby in some pandas)
                agg_sub = {}
                for k, v in agg_dict.items():
                    if k not in sub_agg.columns:
                        continue
                    agg_sub[k] = _take_first if v == "first" else v
                ser = sub_agg.agg(agg_sub)
                row = ser.to_dict()
                # Ensure all agg columns present (fill missing with 0/first)
                for k in agg_dict:
                    if k not in row:
                        row[k] = 0 if agg_dict[k] == "sum" else (team if k == "team" else "" if k == "opponent" else 0)
                row["on_players"] = on_players
                row["off_players"] = off_players
                row["combination"] = {player_list[i]: (player_list[i] in on_players) for i in range(len(player_list))}
            rows.append(row)

        # Add net columns to each record (same formulas as get_lineup_stats)
        for row in rows:
            p = row.get("points") or 0
            op = row.get("opp_points") or 0
            row["net_points"] = p - op
            row["net_rebounds"] = (row.get("rebounds") or 0) - (row.get("opp_rebounds") or 0)
            row["net_assists"] = (row.get("assists") or 0) - (row.get("opp_assists") or 0)
            row["net_turnovers"] = (row.get("turnovers") or 0) - (row.get("opp_turnovers") or 0)
            row["net_fouls"] = (row.get("fouls_committed") or 0) - (row.get("fouls_drawn") or 0)

        # Ensure JSON-serializable (numpy -> native Python)
        data = [_json_serializable(rec) for rec in rows]
        return JSONResponse(content=data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"On/Off lineup stats failed: {str(e)}"}
        )


def _on_off_empty_row(team, agg_keys, on_players, off_players, player_list):
    """One row of zeros for a combination with no matching lineups."""
    row = {}
    for k in agg_keys:
        if k == "team":
            row[k] = team
        elif k == "opponent":
            row[k] = ""
        elif k == "team_avg_height":
            row[k] = 0
        else:
            row[k] = 0
    row["on_players"] = on_players
    row["off_players"] = off_players
    row["combination"] = {player_list[i]: (player_list[i] in on_players) for i in range(len(player_list))}
    return row


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
