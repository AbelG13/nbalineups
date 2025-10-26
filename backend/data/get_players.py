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

# with open("playersBDL25.csv", "w", encoding="utf-8", newline="") as f:
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(all_players)


# print("Saved to playersBDL25.csv")

# from nba_api.stats.static import players
# nba_players = players.get_players()

# # convert to pandas dataframe
# import pandas as pd
# df = pd.DataFrame(nba_players)
# df.to_csv('playersAPI25.csv', index=False)

#### IF STATIC API DOES NOT WORK USE THIS ENDPOINT ####

# from nba_api.stats.endpoints import commonallplayers
# import pandas as pd

# # Get all players
# players_df = commonallplayers.CommonAllPlayers(is_only_current_season=0).get_data_frames()[0]

# # Rename columns
# renamed = players_df.rename(columns={
#     'PERSON_ID': 'id',
#     'DISPLAY_FIRST_LAST': 'full_name',
#     'DISPLAY_LAST_COMMA_FIRST': 'last_comma_first',
#     'ROSTERSTATUS': 'is_active'
# })

# # Split last_comma_first safely
# def split_last_comma_first(name):
#     if isinstance(name, str) and ',' in name:
#         last, first = name.split(',', 1)
#         return pd.Series([last.strip(), first.strip()])
#     else:
#         # If no comma, put entire name as full_name in first_name and leave last_name blank
#         return pd.Series(['', name.strip() if isinstance(name, str) else ''])

# renamed[['last_name', 'first_name']] = renamed['last_comma_first'].apply(split_last_comma_first)

# # Convert is_active to boolean
# renamed['is_active'] = renamed['is_active'].apply(lambda x: True if x == 1 else False)

# # Drop helper column
# renamed = renamed.drop(columns=['last_comma_first'])

# # Debugging

# # where full name is Yang Hansen, change first name to Yang and last name to Hansen
# renamed.loc[renamed['full_name'] == 'Yang Hansen', 'first_name'] = 'Yang'
# renamed.loc[renamed['full_name'] == 'Yang Hansen', 'last_name'] = 'Hansen'


# renamed[['id', 'full_name', 'is_active', 'last_name', 'first_name']].to_csv("playersAPI25.csv", index=False)

import pandas as pd 
import ast

df1 = pd.read_csv("playersBDL25.csv")
df2 = pd.read_csv("playersAPI25.csv")

# Debugging... Mapping of simplified names → corrected official names
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
    ("Pacome", "Dadiet"): ("Pacôme", "Dadiet"),
    ("Zach", "Lavine"): ("Zach", "LaVine"),
    ("PJ", "Tucker"): ("P.J.", "Tucker"),
    ("Tobias", "Harris"): ("Tobias", "Harris"),
    ("Airious", "Bailey"): ("Ace", "Bailey"),
    ("Egor", "Demin"): ("Egor", "Dëmin"),
    ("Nolan", "Traoré"): ("Nolan", "Traore"),
    ("David", "Jones"): ("David", "Jones Garcia"),
    ("Hansen", "Yang"): ("Yang", "Hansen"),
    ("Nigel", "Hayes"): ("Nigel", "Hayes-Davis"),
    ("Yanic Konan", "Niederhauser"): ("Yanic Konan", "Niederhäuser")




}

# Apply corrections
for (old_first, old_last), (new_first, new_last) in name_corrections.items():
    df1.loc[
        (df1["first_name"] == old_first) & (df1["last_name"] == old_last),
        ["first_name", "last_name"]
    ] = new_first, new_last

df1.to_csv("playersBDL25.csv", index=False)

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
filtered_df[['player_id', 'first_name', 'last_name', 'position', 'team_abbreviation']].to_csv("active25.csv", index=False)



