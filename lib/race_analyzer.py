# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from typing import Dict, Any, Optional
from lib.f1_types import F1Utils

def _isATwat(driver_data: Dict[str, Any]) -> bool:
    """
    Check if a given driver is a Twat.

    Arguments:
        - driver_data: A dictionary containing the driver data

    Returns:
        True if the driver is indeed a Twat, False otherwise
    """

    # Let's simplify this. skip player if telemetry is off. fuck 'em
    participant_data = driver_data.get("participant-data")
    return participant_data['telemetry-setting'] == "Restricted" if participant_data else True

def getFastestTimesJson(json_data: Dict[str, Any], driver_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate the fastest lap and sector times for a given driver from the provided JSON data.

    Parameters:
        - json_data: Driver data dictionary containing the "classification-data" key.
        - driver_name: A string representing the driver's name. Default is None.

    Returns:
        - A dictionary with the fastest lap and sector times for the specified driver.
    """

    # If specific driver data is requeste
    if driver_data:
        session_history = driver_data.get("session-history", None)
        driver_index = driver_data["index"]
        if session_history:
            return {
                'lap' : {
                    'driver-name'   : driver_data["driver-name"],
                    'team-id'       : driver_data["participant-data"]["team-id"],
                    'driver-index'  : driver_index,
                    'lap-number'    : session_history["best-lap-time-lap-num"],
                    'time'          : session_history["lap-history-data"]\
                                        [session_history["best-lap-time-lap-num"]-1]["lap-time-in-ms"],
                    'time-str'      : F1Utils.millisecondsToMinutesSecondsMilliseconds(
                                        session_history["lap-history-data"]\
                                            [session_history["best-lap-time-lap-num"]-1]["lap-time-in-ms"])
                },
                's1' : {
                    'driver-name'   : driver_data["driver-name"],
                    'team-id'       : driver_data["participant-data"]["team-id"],
                    'driver-index'  : driver_index,
                    'lap-number'    : session_history["best-sector-1-lap-num"],
                    'time'          : session_history["lap-history-data"]\
                                        [session_history["best-sector-1-lap-num"]-1]["sector-1-time-in-ms"],
                    'time-str'      : F1Utils.millisecondsToSecondsMilliseconds(session_history["lap-history-data"]\
                                        [session_history["best-sector-1-lap-num"]-1]["sector-1-time-in-ms"])
                },
                's2' : {
                    'driver-name'   : driver_data["driver-name"],
                    'team-id'       : driver_data["participant-data"]["team-id"],
                    'driver-index'  : driver_index,
                    'lap-number'    : session_history["best-sector-2-lap-num"],
                    'time'          : session_history["lap-history-data"]\
                                        [session_history["best-sector-2-lap-num"]-1]["sector-2-time-in-ms"],
                    'time-str'      : F1Utils.millisecondsToSecondsMilliseconds(session_history["lap-history-data"]\
                                        [session_history["best-sector-2-lap-num"]-1]["sector-2-time-in-ms"])
                },
                's3' : {
                    'driver-name'   : driver_data["driver-name"],
                    'team-id'       : driver_data["participant-data"]["team-id"],
                    'driver-index'  : driver_index,
                    'lap-number'    : session_history["best-sector-3-lap-num"],
                    'time'          : session_history["lap-history-data"]\
                                        [session_history["best-sector-3-lap-num"]-1]["sector-3-time-in-ms"],
                    'time-str'      : F1Utils.millisecondsToSecondsMilliseconds(session_history["lap-history-data"]\
                                        [session_history["best-sector-3-lap-num"]-1]["sector-3-time-in-ms"])
                },
            }
        return None

    def getFastestTimesDict(json_data: Dict[str, Any], best_time_lap_num_key: str, best_time_key: str):
        """
        Generates a dictionary containing the driver index, lap number, and fastest lap/sectors in the given JSON data.

        Arguments:
            - json_data: A dictionary containing the classification data
            - best_time_lap_num_key: The key to access the best lap number in the session history
            - best_time_key: The key to access the best lap time in the session history

        Returns:
            A dictionary with keys 'driver-index', 'lap-number', and 'time' representing the fastest lap details
        """

        fastest_dict = {
            'driver-index' : None,
            'lap-number'  : None,
            'time' : None
        }

        for driver_data in json_data["classification-data"]:
            if _isATwat(driver_data):
                continue
            driver_index = driver_data["index"]
            session_history = driver_data.get("session-history", None)
            if session_history:
                if (fastest_dict['driver-index'] is None) or \
                    (fastest_dict['lap-number'] is None) or \
                        (fastest_dict['time'] is None):
                    fastest_lap_num = session_history[best_time_lap_num_key]
                    fastest_dict['driver-name'] = driver_data["driver-name"]
                    fastest_dict['team-id'] = driver_data["participant-data"]["team-id"]
                    fastest_dict['driver-index'] = driver_index
                    fastest_dict['lap-number'] = fastest_lap_num
                    fastest_lap_index = fastest_lap_num - 1
                    if 0 <= fastest_lap_index < len(session_history["lap-history-data"]):
                        fastest_dict['time'] = session_history["lap-history-data"][fastest_lap_num-1][best_time_key]
                else:
                    best_time_lap_num = session_history[best_time_lap_num_key]
                    best_time_lap_index = best_time_lap_num - 1
                    if 0 <= best_time_lap_index < len(session_history["lap-history-data"]):
                        best_lap_time = session_history["lap-history-data"][best_time_lap_index][best_time_key]
                        if best_lap_time < fastest_dict['time']:
                            fastest_dict['driver-index'] = driver_index
                            fastest_dict['lap-number'] = best_time_lap_num
                            fastest_dict['time'] = best_lap_time
                            fastest_dict['driver-name'] = driver_data["driver-name"]
                            fastest_dict['team-id'] = driver_data["participant-data"]["team-id"]
        return fastest_dict if any(value is not None for value in fastest_dict.values()) else None

    def getFastestTimeStr(value : Optional[int]) -> Optional[str]:
        """
        Converts the given value to a string in minutes:seconds.milliseconds format.

        Arguments:
            - value: The value to convert

        Returns:
            A string in minutes:seconds.milliseconds format
        """

        return None if value is None else F1Utils.getLapTimeStr(value)

    fastest_dict = {
        'lap' : getFastestTimesDict(json_data=json_data,
                                    best_time_lap_num_key="best-lap-time-lap-num",
                                    best_time_key="lap-time-in-ms"),
        's1' : getFastestTimesDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-1-lap-num",
                                    best_time_key="sector-1-time-in-ms"),
        's2' : getFastestTimesDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-2-lap-num",
                                    best_time_key="sector-2-time-in-ms"),
        's3' : getFastestTimesDict(json_data=json_data,
                                    best_time_lap_num_key="best-sector-3-lap-num",
                                    best_time_key="sector-3-time-in-ms"),
    }
    if fastest_dict['lap'] is not None:
        fastest_dict['lap']['time-str'] = getFastestTimeStr(fastest_dict['lap']['time'])
    if fastest_dict['s1'] is not None:
        fastest_dict['s1']['time-str'] = getFastestTimeStr(fastest_dict['s1']['time'])
    if fastest_dict['s2'] is not None:
        fastest_dict['s2']['time-str'] = getFastestTimeStr(fastest_dict['s2']['time'])
    if fastest_dict['s3'] is not None:
        fastest_dict['s3']['time-str'] = getFastestTimeStr(fastest_dict['s3']['time'])

    return fastest_dict

def getTyreStintRecordsDict(json_data: Dict[str, Any]):
    """
    Generate the tyre stint records based on the input JSON data.

    Parameters:
        - json_data: The JSON data containing classification and tyre set history for drivers.

    Returns:
        - final_json: A JSON object containing the longest tyre stint and lowest tyre wear per lap for each compound.
    """



    class TyreStintRecords:
        """Class that computes and stores tyre stint records
        """

        def __init__(self, json_data: Dict[str, Any]):
            """Analyse the input JSON data and populate the internal records

            Args:
                json_data (JSON): The input JSON dict
            """

            self.m_records = {}
            self.__analyse(json_data)

        def __analyse(self, json_data: Dict[str, Any]):
            """
            Analyzes the given json data to extract and record the following for each tyre compound:
                longest stint
                    driver name
                    length,
                lowest wear per lap
                    driver name
                    wear percentage.

            Arguments:
                - json_data: The JSON data containing classification data and tyre set history for each driver.
            """

            for driver_data in json_data["classification-data"]:
                if _isATwat(driver_data):
                    continue
                for tyre_set_history_item in driver_data["tyre-set-history"]:
                    if (tyre_set_history_item.get("tyre-set-data") is None):
                        continue
                    tyre_set_data = tyre_set_history_item["tyre-set-data"]
                    stint_length = tyre_set_history_item["stint-length"]
                    compound = tyre_set_data["actual-tyre-compound"]
                    if isinstance(compound, int):
                        # cunts who have telemetry disabled can fuck themselves
                        continue
                    compound = tyre_set_data["actual-tyre-compound"] + ' - ' + tyre_set_data["visual-tyre-compound"]
                    if not stint_length:
                        # Skip if either 0 or None
                        continue
                    if compound not in self.m_records:
                        self.m_records[compound] = {
                            "longest-stint-driver-name" : driver_data["driver-name"],
                            "longest-stint-length" : stint_length,
                            "highest-wear-value" : tyre_set_data["wear"] ,
                            "highest-wear-driver-name" : driver_data["driver-name"],
                            "lowest-wear-per-lap-driver-name" : driver_data["driver-name"],
                            "lowest-wear-per-lap-value" : \
                                    float(tyre_set_data["wear"])/stint_length
                        }
                    else:
                        if stint_length > self.m_records[compound]["longest-stint-length"]:
                            # New longest stint
                            self.m_records[compound]["longest-stint-length"] = stint_length
                            self.m_records[compound]["longest-stint-driver-name"] = driver_data["driver-name"]
                        # If the driver DNF's right after fitting new tyre set, wear will be 0. Ignore this
                        if tyre_set_data["wear"] > 0:
                            tyre_wear_per_lap = float(tyre_set_data["wear"]) / stint_length
                            if tyre_wear_per_lap < self.m_records[compound]["lowest-wear-per-lap-value"]:
                                self.m_records[compound]["lowest-wear-per-lap-value"] = tyre_wear_per_lap
                                self.m_records[compound]["lowest-wear-per-lap-driver-name"] = driver_data["driver-name"]
                            if tyre_set_data["wear"] > self.m_records[compound]["highest-wear-value"]:
                                self.m_records[compound]["highest-wear-value"] = tyre_set_data["wear"]
                                self.m_records[compound]["highest-wear-driver-name"] = driver_data["driver-name"]


    # Populate the final JSON and return
    tyre_stint_records = TyreStintRecords(json_data)
    return {
        compound: {
            'longest-tyre-stint': {
                'value': records["longest-stint-length"],
                'driver-name': records["longest-stint-driver-name"],
            },
            'lowest-tyre-wear-per-lap': {
                'value': records["lowest-wear-per-lap-value"],
                'driver-name': records["lowest-wear-per-lap-driver-name"],
            },
            'highest-tyre-wear': {
                'value': records["highest-wear-value"],
                'driver-name': records["highest-wear-driver-name"],
            },
        }
        for compound, records in tyre_stint_records.m_records.items()
    }
