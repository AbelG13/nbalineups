# import requests
# import csv
# import time
# API_KEY = "795ba448-8b30-43d6-8d6f-f61c746ce333"  
# BASE_URL = "https://api.balldontlie.io/v1/players"

# HEADERS = {
#     "Authorization": API_KEY
# }

# all_players = []
# cursor = None
# count = 0
# while True:
#     params = {"per_page": 100}
#     if cursor:
#         params["cursor"] = cursor

#     response = requests.get(BASE_URL, headers=HEADERS, params=params)
#     if response.status_code != 200:
#         print("Error:", response.status_code, response.text)
#         break

#     data = response.json()
#     all_players.extend(data["data"])

#     # pagination
#     meta = data.get("meta", {})
#     cursor = meta.get("next_cursor")
#     if not cursor:
#         break
#     count += 1
#     print(f"Fetched {count} pages")
#     if count % 5 == 0:
#         time.sleep(61)




# print(f"\nTotal players fetched: {len(all_players)}")

# fieldnames = list(all_players[0].keys())

# with open("nba_players_full.csv", "w", encoding="utf-8", newline="") as f:
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(all_players)


# print("Saved to nba_players_full.csv")

# from nba_api.stats.static import players
# nba_players = players.get_players()

# # convert to pandas dataframe
# import pandas as pd
# df = pd.DataFrame(nba_players)
# df.to_csv('nba_players.csv', index=False)


import pandas as pd 
import ast

df1 = pd.read_csv("nba_players_full.csv")
df2 = pd.read_csv("nba_players.csv")

# Mapping of simplified names → corrected official names
name_corrections = {
    ("Bogdan", "Bogdanovic"): ("Bogdan", "Bogdanović"),
    ("Brandon", "Boston Jr."): ("Brandon", "Boston"),
    ("Jimmy", "Butler"): ("Jimmy", "Butler III"),
    ("Carlton", "Carrington"): ("Bub", "Carrington"),
    ("Nicolas", "Claxton"): ("Nic", "Claxton"),
    ("Moussa", "Diabate"): ("Moussa", "Diabaté"),
    ("Luka", "Doncic"): ("Luka", "Dončić"),
    ("Jeff", "Dowtin"): ("Jeff", "Dowtin Jr."),
    ("Dante", "Exum"): ("Danté", "Exum"),
    ("KyShawn", "George"): ("Kyshawn", "George"),
    ("A.J.", "Green"): ("AJ", "Green"),
    ("Nah'Shon", "Hyland"): ("Bones", "Hyland"),
    ("Trey", "Jemison"): ("Trey", "Jemison III"),
    ("Nikola", "Jokic"): ("Nikola", "Jokić"),
    ("Nikola", "Jovic"): ("Nikola", "Jović"),
    ("Kevin", "Knox"): ("Kevin", "Knox II"),
    ("Vit", "Krejci"): ("Vít", "Krejčí"),
    ("AJ", "Lawson"): ("A.J.", "Lawson"),
    ("Kenyon", "Martin Jr."): ("KJ", "Martin"),
    ("Karlo", "Matkovic"): ("Karlo", "Matković"),
    ("Vasilije", "Micic"): ("Vasilije", "Micić"),
    ("Taze", "Moore"): ("Tazé", "Moore"),
    ("Monte", "Morris"): ("Monté", "Morris"),
    ("Jusuf", "Nurkic"): ("Jusuf", "Nurkić"),
    ("Craig", "Porter"): ("Craig", "Porter Jr."),
    ("Kristaps", "Porzingis"): ("Kristaps", "Porziņģis"),
    ("Cameron", "Reddish"): ("Cam", "Reddish"),
    ("Tidjane", "Salaun"): ("Tidjane", "Salaün"),
    ("Alexandre", "Sarr"): ("Alex", "Sarr"),
    ("Dennis", "Schroder"): ("Dennis", "Schröder"),
    ("K.J.", "Simpson"): ("KJ", "Simpson"),
    ("Nikola", "Topic"): ("Nikola", "Topić"),
    ("Armel", "Traore"): ("Armel", "Traoré"),
    ("Jonas", "Valanciunas"): ("Jonas", "Valančiūnas"),
    ("Nikola", "Vucevic"): ("Nikola", "Vučević"),
    ("Tristan", "Da Silva"): ("Tristan", "da Silva"),
    ("Vlatko", "Cancar"): ("Vlatko", "Čančar"),
    ("Dario", "Saric"): ("Dario", "Šarić"),
}

# Apply corrections
for (old_first, old_last), (new_first, new_last) in name_corrections.items():
    df1.loc[
        (df1["first_name"] == old_first) & (df1["last_name"] == old_last),
        ["first_name", "last_name"]
    ] = new_first, new_last

# join df1 and df2 on first_name and last_name

merged_df = pd.merge(df1, df2, on=["first_name", "last_name"], how="right")


# filter out players that are not active
filtered_df = merged_df[merged_df["is_active"] == True].copy()

# Convert the 'team' column from a string representation of a dictionary to an actual dictionary
filtered_df['team'] = filtered_df['team'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Now, extract the 'abbreviation' from the 'team' dictionary
filtered_df.loc[:, 'team_abbreviation'] = filtered_df['team'].apply(lambda x: x.get('abbreviation', None) if isinstance(x, dict) else None)

#rename id_x to player_id
filtered_df.rename(columns={'id_y': 'player_id'}, inplace=True)

# Save the updated DataFrame to CSV
filtered_df[['player_id', 'first_name', 'last_name', 'position', 'team_abbreviation']].to_csv("active_nba_players.csv", index=False)



