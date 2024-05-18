import json
from prettytable import PrettyTable
import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.f1_types import F1Utils

file_path = 'data/2024_05_05/race-info/race_info_Race_Brazil_2024_05_05_16_23_32.json'
with open(file_path, 'r+', encoding='utf-8') as f:
    json_data = json.load(f)

table = PrettyTable()
table.field_names = [
    'Position',
    'Name',
    'Team ID',
    'Result',
    # 'Telemetry Setting',
    'Start Position',
    'Best Lap',
    'Race Time',
    'Time plus pens',
    'CC Warnings',
    'Penalties'
]

prev_race_time_sec = None
for driver_data in json_data['classification-data']:
    final_classification = driver_data['final-classification']
    participant_data = driver_data['participant-data']
    lap_data = driver_data['lap-data']

    position = driver_data["track-position"]
    driver_name = participant_data['name']
    team_id = participant_data['team-id']
    result = final_classification['result-status']
    telemetry_setting = participant_data['telemetry-setting']
    start_position = final_classification['grid-position']
    best_lap = final_classification['best-lap-time-str']
    race_time = final_classification['total-race-time-str']
    ccw = lap_data["corner-cutting-warnings"]
    penalties = lap_data["penalties"]
    time_plus_pens = F1Utils.floatSecondsToMinutesSecondsMilliseconds(final_classification['total-race-time'] + penalties)

    table.add_row([
        position,
        driver_name,
        team_id,
        result,
        # telemetry_setting,
        start_position,
        best_lap,
        race_time,
        time_plus_pens,
        ccw,
        penalties,
    ])


print(table)
