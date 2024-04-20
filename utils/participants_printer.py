import json
from prettytable import PrettyTable

file_path = 'data/2024_04_14/race-info/race_info_Race_2_Singapore_2024_04_14_16_02_16.json'
with open(file_path, 'r+', encoding='utf-8') as f:
    json_data = json.load(f)

table = PrettyTable()
table.field_names = ['Name', 'Team ID', 'Telemetry Setting']

for driver_data in json_data['classification-data']:
    participant_data = driver_data['participant-data']
    table.add_row([
        participant_data['name'],
        participant_data['team-id'],
        participant_data['telemetry-setting']
    ])

print(table)
