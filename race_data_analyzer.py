import json
import argparse
from f1_types import F1Utils
from overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode
from prettytable import PrettyTable

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
        return

    session_history = driver_data.get("session-history", None)
    if session_history:
        fastest_data = {
            'lap' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-lap-time-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-lap-time-lap-num"]-1]["lap-time-in-ms"]
            },
            's1' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-1-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-1-lap-num"]-1]["sector-1-time-in-ms"]
            },
            's2' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-2-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-2-lap-num"]-1]["sector-2-time-in-ms"]
            },
            's3' : {
                'driver-index' : driver_index,
                'lap-number'  : session_history["best-sector-3-lap-num"],
                'time' : session_history["lap-history-data"][session_history["best-sector-3-lap-num"]-1]["sector-3-time-in-ms"]
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

def printSeparator(count=75):

    print('-' * count)

def printTyreStintRecords(json_data):

    class TyreStintRecords:

        def __init__(self, json_data):

            self.m_records = {}
            self.__analyse(json_data)

        def __analyse(self, json_data):

            for index, driver_data in enumerate(json_data["classification-data"]):
                for tyre_set_history_item in driver_data["tyre-set-history"]:
                    if not "tyre-set-data" in tyre_set_history_item or tyre_set_history_item["tyre-set-data"] is None:
                        continue
                    tyre_set_data = tyre_set_history_item["tyre-set-data"]
                    compound = tyre_set_data["actual-tyre-compound"]
                    if isinstance(compound, int):
                        # cunts who have telemetry disabled can fuck themselves
                        continue
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

def printStintHistoryForDriver(json_data, driver_name):

    driver_data = None
    driver_index = None
    for index, classification_data in enumerate(json_data["classification-data"]):
        if classification_data["driver-name"] == driver_name:
            driver_data = classification_data
            driver_index = index
            break

    if driver_index is not None and driver_data is not None:
        tyre_set_history = driver_data.get('tyre-set-history', None)
        if not tyre_set_history:
            print('Tyre set history data not available :(')
            return

        for stint_index, history_item in enumerate(tyre_set_history):

            compound_str =  history_item["tyre-set-data"]["visual-tyre-compound"] + " - " +  \
                            history_item["tyre-set-data"]["actual-tyre-compound"]
            start_lap = history_item["start-lap"]
            end_lap = history_item["end-lap"]
            tyre_age = history_item["stint-length"]
            tyre_wear = history_item["tyre-set-data"]["wear"]
            wear_per_lap = float(tyre_wear) / tyre_age
            wear_per_lap_str = f"{wear_per_lap:.2f}" + "%"
            lifespan = history_item["tyre-set-data"]["usable-life"]

            print('Stint ' + str(stint_index+1) + ': ' + compound_str)
            table  = PrettyTable()
            table.header = False
            table.align = "l"


            table.add_row(['Compound', compound_str])
            table.add_row(['Start Lap', str(start_lap)])
            table.add_row(['End Lap', str(end_lap)])
            table.add_row(['Tyre Age', str(tyre_age) + ' laps'])
            table.add_row(['Tyre wear', str(tyre_wear) + "%"])
            table.add_row(['Tyre wear per lap', wear_per_lap_str])
            table.add_row(['Game suggested max lifespan', str(lifespan) + ' laps'])


            # Indent the table output by 4 characters
            table_str = str(table)
            indented_table_str = "\n".join([" " * 4 + line for line in table_str.split("\n")])
            print(indented_table_str)
    else:
        print('Invalid driver name')

def printERSDataForDriver(json_data, driver_name):

    driver_data = None
    driver_index = None
    for index, classification_data in enumerate(json_data["classification-data"]):
        if classification_data["driver-name"] == driver_name:
            driver_data = classification_data
            driver_index = index
            break

    if driver_index is not None and driver_data is not None:
        if "per-lap-info" in driver_data:

            print('ERS per lap')
            table  = PrettyTable()
            table.align = "c"
            table.field_names = [
                "Lap",
                "ERS remaining",
                "ERS deployed",
                "Harvested - MGU-H",
                "Harvested - MGU-K",
                "Harvested - Total"]

            for lap_info in driver_data["per-lap-info"]:
                lap_number = lap_info["lap-number"]
                if "car-status-data" in lap_info:
                    ers_max_capacity            = lap_info["car-status-data"]["ers-max-capacity"]
                    ers_rem_val                 = lap_info["car-status-data"]["ers-store-energy"]
                    ers_deployed_val            = lap_info["car-status-data"]["ers-deployed-this-lap"]
                    ers_harvested_mguh_val      = lap_info["car-status-data"]["ers-harvested-this-lap-mguh"]
                    ers_harvested_mguk_val      = lap_info["car-status-data"]["ers-harvested-this-lap-mguk"]

                    ers_rem_perc                = F1Utils.floatToStr((ers_rem_val / ers_max_capacity) * 100.0) + "%"
                    ers_deployed_perc           = F1Utils.floatToStr((ers_deployed_val / ers_max_capacity) * 100.0) + "%"
                    ers_harvested_mguh_perc     = F1Utils.floatToStr((ers_harvested_mguh_val / ers_max_capacity) * 100.0) + "%"
                    ers_harvested_mguk_perc     = F1Utils.floatToStr((ers_harvested_mguk_val / ers_max_capacity) * 100.0) + "%"
                    ers_harvested_total_perc    = \
                        F1Utils.floatToStr(((ers_harvested_mguh_val + ers_harvested_mguk_val) / ers_max_capacity)\
                                            * 100.0) + "%"
                else:
                    ers_rem_perc                = '---'
                    ers_deployed_perc           = '---'
                    ers_harvested_mguh_perc     = '---'
                    ers_harvested_mguk_perc     = '---'
                    ers_harvested_total_perc    = '---'

                table.add_row([
                    str(lap_number),
                    ers_rem_perc,
                    ers_deployed_perc,
                    ers_harvested_mguh_perc,
                    ers_harvested_mguk_perc,
                    ers_harvested_total_perc])

            # Indent the table output by 4 characters
            table_str = str(table)
            indented_table_str = "\n".join([" " * 4 + line for line in table_str.split("\n")])
            print(indented_table_str)
        else:
            print('ERS per lap data is not available')
    else:
        print('Invalid driver name')

def printParticipantInfo(json_data):

    table  = PrettyTable()
    table.align = "c"
    table.field_names = [
        "Name",
        "Team",
        "Driver number",
        "Platform",
        "Show Name",
        "Telemetry Setting"]

    for classification_data in json_data["classification-data"]:
        participant_data = classification_data["participant-data"]
        table.add_row([
            participant_data["name"],
            participant_data["team-id"],
            str(participant_data["race-number"]),
            participant_data["platform"],
            str(participant_data["show-online-names"]),
            participant_data["telemetry-setting"]])

    # Indent the table output by 4 characters
    table_str = str(table)
    indented_table_str = "\n".join([" " * 4 + line for line in table_str.split("\n")])
    print(indented_table_str)

if __name__ == "__main__":

    # Parse the command line args
    parser = argparse.ArgumentParser(description="Parse the race data JSON file and perform analysis")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--driver-name", type=str, help="Name of the driver whose specific info is required")
    parser.add_argument('--players-info', action='store_true', help="Show only player info")

    args = parser.parse_args()

    with open(args.file_name, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    if args.players_info:
        printParticipantInfo(json_data)

    else:
        print("Fastest times records (all drivers)")
        printFastestTimes(json_data)
        printSeparator()

        print("Overtake records")
        printOvertakeInfo(json_data, driver_name=args.driver_name)
        printSeparator()
        if args.driver_name:
            print("Fastest lap time records (for " + args.driver_name + ")")
            printDriverFastestTimes(json_data, args.driver_name)
            printSeparator()

        print("Tyre stint records (all players)")
        printTyreStintRecords(json_data)
        printSeparator()

        if args.driver_name:
            print("Tyre stint history (for " + args.driver_name + ")")
            printStintHistoryForDriver(json_data, args.driver_name)
            printSeparator()

        if args.driver_name:
            print("ERS history (for " + args.driver_name + ")")
            printERSDataForDriver(json_data, args.driver_name)