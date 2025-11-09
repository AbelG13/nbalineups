from nba_api.stats.endpoints import boxscoretraditionalv2, boxscoretraditionalv3
import pandas as pd

# Use a recent game ID from your data
game_id = '0022500191'  # 2025-26 season game

print("=" * 80)
print("BOXSCORE TRADITIONAL V2 - Testing 2025-26 Season")
print("=" * 80)

try:
    box_v2 = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    df_v2 = box_v2.get_data_frames()[0]
    print(f"\nNumber of rows: {len(df_v2)}")
    print(f"Number of columns: {len(df_v2.columns)}")
    
    if len(df_v2) > 0:
        print(f"\nColumn names:")
        print(df_v2.columns.tolist())
        print(f"\nFirst few rows:")
        print(df_v2[['PLAYER_NAME', 'TEAM_ABBREVIATION']].head())
    else:
        print("\n V2 returned EMPTY DataFrame - V2 may not support 2025-26 season!")
    
except Exception as e:
    print(f"V2 Error: {e}")

print("\n" + "=" * 80)
print("BOXSCORE TRADITIONAL V3 - Testing 2025-26 Season")
print("=" * 80)

try:
    box_v3 = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    
    # Check the raw data structure
    raw_data = box_v3.data_sets[0].data
    print(f"\nNumber of headers: {len(raw_data['headers'])}")
    print(f"Number of data rows: {len(raw_data['data'])}")
    if raw_data['data']:
        print(f"Number of columns in first data row: {len(raw_data['data'][0])}")
    
    print(f"\nHeaders: {raw_data['headers']}")
    
    # Manual workaround: Create DataFrame manually
    if len(raw_data['data']) > 0 and len(raw_data['data'][0]) != len(raw_data['headers']):
        print(f"\n Column mismatch detected!")
        print(f"   Headers: {len(raw_data['headers'])}")
        print(f"   Data columns: {len(raw_data['data'][0])}")
        
        # Try to create DataFrame by truncating extra columns
        print("\n Attempting workaround: Truncating data to match headers...")
        truncated_data = [row[:len(raw_data['headers'])] for row in raw_data['data']]
        df_v3_manual = pd.DataFrame(truncated_data, columns=raw_data['headers'])
        
        print(f"\nManual DataFrame created successfully!")
        print(f"Shape: {df_v3_manual.shape}")
        print(f"\nFirst few rows:")
        print(df_v3_manual[['teamName', 'firstName', 'familyName']].head(30))
        print(df_v3_manual.columns.tolist())
        
        print("\n V3 WORKS with manual DataFrame creation!")
    else:
        # Standard approach
        df_v3 = box_v3.get_data_frames()[0]
        print(f"\nStandard DataFrame creation worked!")
        print(df_v3[['firstName', 'familyName', 'teamTricode']].head())
    
except Exception as e:
    print(f"V3 Error: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("\nIf V2 is empty and V3 has the column mismatch:")
print("  → Use V3 with manual DataFrame creation (truncate extra columns)")
print("  → This is a temporary fix until nba_api updates")