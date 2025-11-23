import requests
import pandas as pd
from typing import List
from io import StringIO

ESPN_INJURY_URL = "https://www.espn.com/nba/injuries"

class InjuryAPIError(Exception):
    """Custom exception for injury scraping errors."""
    pass

def fetch_espn_injury_tables(timeout: int = 10) -> List[pd.DataFrame]:
    """
    Fetch and parse the injury tables from ESPN's NBA injuries page.

    Returns
    -------
    list[pd.DataFrame]
        List of DataFrames, one per table on the page.

    Raises
    ------
    InjuryAPIError
        If the request fails or no tables are found.
    """
    headers = {
        # Pretend to be a normal Chrome browser on Windows
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.espn.com/nba/"
    }

    try:
        resp = requests.get(ESPN_INJURY_URL, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise InjuryAPIError(f"Error fetching ESPN injuries page: {e}") from e
    
    # Passing literal html to 'read_html' is deprecated and will be removed in a future version. 
    # To read from a literal string, wrap it in a 'StringIO' object.
    try:
        tables = pd.read_html(StringIO(resp.text))
    except ValueError as e:
        raise InjuryAPIError("No injury tables found on ESPN injuries page") from e

    if not tables:
        raise InjuryAPIError("ESPN injuries page returned no tables")

    return tables

def get_espn_injuries_df(timeout: int = 10) -> pd.DataFrame:
    tables = fetch_espn_injury_tables(timeout=timeout)

    df = pd.concat(tables, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]

    col_map = {
        "TEAM": "Team",
        "PLAYER": "Name",
        "PLAYER NAME": "Name",
        "POS": "Pos",
        "POSITION": "Pos",
        "DATE": "Date",
        "INJURY": "Injury",
        "STATUS": "Status",
    }

    renamed = {}
    for c in df.columns:
        upper = c.upper()
        if upper in col_map:
            renamed[c] = col_map[upper]
    df = df.rename(columns=renamed)

    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].str.strip()

    return df

inj_df = get_espn_injuries_df()
inj_df = inj_df[inj_df['Status'] == 'Out'][['NAME', 'Status']] 


name_corrections = {
    ("Bogdan Bogdanovic"): ("Bogdan Bogdanović"),
    ("Brandon Boston Jr."): ("Brandon Boston"),
    ("Jimmy Butler"): ("Jimmy Butler III"),
    ("Carlton Carrington"): ("Bub Carrington"),
    ("Nicolas Claxton"): ("Nic Claxton"),
    ("Moussa Diabate"): ("Moussa Diabaté"),
    ("Luka Doncic"): ("Luka Dončić"),
    ("Jeff Dowtin"): ("Jeff Dowtin Jr."),
    ("Dante Exum"): ("Danté Exum"),
    ("KyShawn George"): ("Kyshawn George"),
    ("A.J. Green"): ("AJ Green"),
    ("Nah'Shon Hyland"): ("Bones Hyland"),
    ("Trey Jemison"): ("Trey Jemison III"),
    ("Nikola Jokic"): ("Nikola Jokić"),
    ("Nikola Jovic"): ("Nikola Jović"),
    ("Kevin Knox"): ("Kevin Knox II"),
    ("Vit Krejci"): ("Vít Krejčí"),
    ("AJ Lawson"): ("A.J. Lawson"),
    ("Kenyon Martin Jr."): ("KJ Martin"),
    ("Karlo Matkovic"): ("Karlo Matković"),
    ("Vasilije Micic"): ("Vasilije Micić"),
    ("Taze Moore"): ("Tazé Moore"),
    ("Monte Morris"): ("Monté Morris"),
    ("Jusuf Nurkic"): ("Jusuf Nurkić"),
    ("Craig Porter"): ("Craig Porter Jr."),
    ("Kristaps Porzingis"): ("Kristaps Porziņģis"),
    ("Cameron Reddish"): ("Cam Reddish"),
    ("Tidjane Salaun"): ("Tidjane Salaün"),
    ("Alexandre Sarr"): ("Alex Sarr"),
    ("Dennis Schroder"): ("Dennis Schröder"),
    ("K.J. Simpson"): ("KJ Simpson"),
    ("Nikola Topic"): ("Nikola Topić"),
    ("Armel Traore"): ("Armel Traoré"),
    ("Jonas Valanciunas"): ("Jonas Valančiūnas"),
    ("Nikola Vucevic"): ("Nikola Vučević"),
    ("Tristan Da Silva"): ("Tristan da Silva"),
    ("Vlatko Cancar"): ("Vlatko Čančar"),
    ("Dario Saric"): ("Dario Šarić"),
    ("Pacome Dadiet"): ("Pacôme Dadiet"),
    ("Zach Lavine"): ("Zach LaVine"),
    ("PJ Tucker"): ("P.J. Tucker"),
    ("Tobias Harris"): ("Tobias Harris"),
    ("Airious Bailey"): ("Ace Bailey"),
    ("Egor Demin"): ("Egor Dëmin"),
    ("Nolan Traoré"): ("Nolan Traore"),
    ("David Jones"): ("David Jones Garcia"),
    ("Hansen Yang"): ("Yang Hansen"),
    ("Nigel Hayes"): ("Nigel Hayes-Davis"),
    ("Yanic Konan Niederhauser"): ("Yanic Konan Niederhäuser")
}


for old_name, new_name in name_corrections.items():
    inj_df.loc[
        (inj_df["NAME"] == old_name),
        ["NAME"]
    ] = new_name


inj_df.to_csv("injuries25.csv", index=False)



