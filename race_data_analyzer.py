import json
import argparse
from f1_types import F1Utils
from overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode

def printFastestRecord(fastest_dict, description, toStringFunction=F1Utils.millisecondsToMinutesSecondsMilliseconds):

    fastest_driver_index = fastest_dict['driver-index']
    fastest_lap_num = fastest_dict['lap-number']
    fastest_time = toStringFunction(fastest_dict['time'])

    print(description)
    print("    Driver name: " + json_data["classification-data"][fastest_driver_index]["participant-data"]["name"])
    print("    Time: " + fastest_time)
    print("    Lap number: " + str(fastest_lap_num))

def printFastestTimes(json_data):

    def getFastestTimeDict(json_data, best_time_lap_num_key, best_time_key):

        fastest_dict = {
            'driver-index' : None,
            'lap-number'  : None,
            'time' : None
        }

        for driver_index, driver_data in enumerate(json_data["classification-data"]):
            session_history = driver_data.get("session-history", None)
            if session_history:
                if not fastest_dict['driver-index'] and not fastest_dict['lap-number'] and not fastest_dict['time']:
                    fastest_lap_num = session_history[best_time_lap_num_key]
                    fastest_dict['driver-index'] = driver_index
                    fastest_dict['lap-number'] = fastest_lap_num
                    fastest_dict['time'] = session_history["lap-history-data"][fastest_lap_num-1][best_time_key]
                else:
                    best_time_lap_num = session_history[best_time_lap_num_key]
                    best_lap_time = session_history["lap-history-data"][best_time_lap_num-1][best_time_key]
                    if best_lap_time < fastest_dict['time']:
                        fastest_dict['driver-index'] = driver_index
                        fastest_dict['lap-number'] = best_time_lap_num
                        fastest_dict['time'] = best_lap_time

        return fastest_dict

    fastest_data = {
        'lap' : getFastestTimeDict(json_data=json_data,
                                    best_time_lap_num_key="best-lap-time-lap-num",
                                    best_time_key="lap-time-in-ms"),
        's1' : getFastestTimeDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-1-lap-num",
                                    best_time_key="sector-1-time-in-ms"),
        's2' : getFastestTimeDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-2-lap-num",
                                    best_time_key="sector-2-time-in-ms"),
        's3' : getFastestTimeDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-3-lap-num",
                                    best_time_key="sector-3-time-in-ms"),
    }
    print("Overall fastest records")
    printFastestRecord(fastest_data['lap'], 'Fastest Lap:')
    printFastestRecord(fastest_data['s1'], 'Sector 1:', F1Utils.millisecondsToSecondsMilliseconds)
    printFastestRecord(fastest_data['s2'], 'Sector 2:', F1Utils.millisecondsToSecondsMilliseconds)
    printFastestRecord(fastest_data['s3'], 'Sector 3:', F1Utils.millisecondsToSecondsMilliseconds)

def printDriverFastestTimes(json_data, driver_name):

    driver_data = None
    driver_index = None
    for index, classification_data in enumerate(json_data["classification-data"]):
        if classification_data["driver-name"] == driver_name:
            driver_data = classification_data
            driver_index = index
            break

    if not driver_data:
        print('Invalid Name')

    session_history = driver_data.get("session-history", None)
    if session_history:
        fastest_data = {
            'lap' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-lap-time-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-lap-time-lap-num"]]["lap-time-in-ms"]
            },
            's1' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-1-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-1-lap-num"]]["sector-1-time-in-ms"]
            },
            's2' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-2-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-2-lap-num"]]["sector-2-time-in-ms"]
            },
            's3' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-3-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-3-lap-num"]]["sector-3-time-in-ms"]
            },
        }

        print("Fastest records for " + driver_name)
        printFastestRecord(fastest_data['lap'], 'Fastest Lap:')
        printFastestRecord(fastest_data['s1'], 'Sector 1:', F1Utils.millisecondsToSecondsMilliseconds)
        printFastestRecord(fastest_data['s2'], 'Sector 2:', F1Utils.millisecondsToSecondsMilliseconds)
        printFastestRecord(fastest_data['s3'], 'Sector 3:', F1Utils.millisecondsToSecondsMilliseconds)
    else:
        print("Session history not available for " + driver_name)


def printOvertakeInfo(json_data, driver_name):

    overtakes = json_data.get('overtakes', None)
    overtakes_printed = False
    if overtakes:
        overtakes_records = overtakes.get('records', None)
        if overtakes_records:
            overtake_analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE, args.file_name)
            print(overtake_analyzer.getFormattedString(driver_name=args.driver_name))
            overtakes_printed = True

    if not overtakes_printed:
        print('No overtakes data')

def printSeparator():

    print('-' * 75)

def printTyreStintRecords(json_data):

    class TyreStintRecords:

        def __init__(self, json_data):

            self.m_records = {}
            self.__analyse(json_data)

        def __analyse(self, json_data):

            for index, driver_data in enumerate(json_data["classification-data"]):
                for tyre_set_history_item in driver_data["tyre-set-history"]:
                    tyre_set_data = tyre_set_history_item["tyre-set-data"]
                    compound = tyre_set_data["actual-tyre-compound"]
                    if compound not in self.m_records:
                        self.m_records[compound] = {
                            "longest-stint-driver-name" : driver_data["driver-name"],
                            "longest-stint-length" : tyre_set_history_item["stint-length"],
                            "lowest-wear-per-lap-driver-name" : driver_data["driver-name"],
                            "lowest-wear-per-lap-value" : float(tyre_set_data["wear"])/tyre_set_history_item["stint-length"]
                        }
                    else:
                        if tyre_set_history_item["stint-length"] > self.m_records[compound]["longest-stint-length"]:
                            # New longest stint
                            self.m_records[compound]["longest-stint-length"] = tyre_set_history_item["stint-length"]
                            self.m_records[compound]["longest-stint-driver-name"] = driver_data["driver-name"]
                        tyre_wear_per_lap = float(tyre_set_data["wear"]) / tyre_set_history_item["stint-length"]
                        if tyre_wear_per_lap < self.m_records[compound]["lowest-wear-per-lap-value"]:
                            self.m_records[compound]["lowest-wear-per-lap-value"] = tyre_wear_per_lap
                            self.m_records[compound]["lowest-wear-per-lap-driver-name"] = driver_data["driver-name"]


    tyre_stint_records = TyreStintRecords(json_data)
    for compound, records in tyre_stint_records.m_records.items():
        print ("Compound: " + compound)
        print("    Longest stint of " + str(records["longest-stint-length"]) + " laps by " + records["longest-stint-driver-name"])
        print("    Lowest tyre wear per lap of " + str(records["lowest-wear-per-lap-value"]) + "% by " + records["lowest-wear-per-lap-driver-name"])

if __name__ == "__main__":

    # Parse the command line args
    parser = argparse.ArgumentParser(description="Parse the race data JSON file and perform analysis")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--driver-name", type=str, help="Name of the driver whose specific info is required")

    args = parser.parse_args()

    with open(args.file_name, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    printFastestTimes(json_data)
    printSeparator()

    printOvertakeInfo(json_data, driver_name=args.driver_name)
    printSeparator()
    if args.driver_name:
        printDriverFastestTimes(json_data, args.driver_name)
        printSeparator()

    printTyreStintRecords(json_data)
    printSeparator()