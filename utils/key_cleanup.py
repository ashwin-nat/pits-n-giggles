import json

# Example usage:
file_path = "data/2024_03_30/race-info/race_info_Race_Imola_2024_03_30_13_56_48.json"
key_to_remove = 'key_to_remove'

# Read JSON data from the file
with open(file_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

classification_data = json_data["classification-data"]
for driver_data in classification_data:
    for tyre_stint in driver_data["tyre-set-history"]:
        if "tyre-wear-history" in tyre_stint:
            del tyre_stint["tyre-wear-history"]
            print("removed tyre wear history")

# Write the modified JSON data back into the same file
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)