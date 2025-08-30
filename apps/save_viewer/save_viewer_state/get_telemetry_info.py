# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List, Optional

from lib.f1_types import F1Utils, LapHistoryData, ResultStatus
from lib.tyre_wear_extrapolator import TyreWearPerLap

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------


def _getTelemetryInfo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to retrieve and format complete telemetry information.

    Args:
        json_data: Global telemetry data

    Returns:
        Complete telemetry data structure with session info and driver entries
    """
    # Check if global data exists
    if not json_data:
        return _get_empty_telemetry_info()

    session_type = json_data["session-info"]["session-type"]
    if session_type == "Time Trial":
        return _get_time_trial_telemetry_info(json_data)

    # Extract session-level information
    fastest_lap, fastest_lap_driver = _extract_fastest_lap_info(json_data)

    # Build base response structure
    json_response = _get_base_rsp_dict(json_data)
    json_response["fastest-lap-overall"] = fastest_lap
    json_response["fastest-lap-overall-driver"] = fastest_lap_driver

    # Prepare driver processing data
    result_str_map = {
        str(ResultStatus.DID_NOT_FINISH): "DNF",
        str(ResultStatus.DISQUALIFIED): "DSQ",
        str(ResultStatus.RETIRED): "DNF"
    }

    best_s1_time = json_data["records"]["fastest"]["s1"]["time"]
    best_s2_time = json_data["records"]["fastest"]["s2"]["time"]
    best_s3_time = json_data["records"]["fastest"]["s3"]["time"]
    fastest_lap_driver_index = json_data["records"]["fastest"]["lap"]["driver-index"]

    # Process each driver
    json_response["table-entries"] = []
    for data_per_driver in json_data["classification-data"]:
        # Skip dummy/blank entries
        if data_per_driver["driver-name"] is None or data_per_driver["team"] is None:
            continue

        driver_entry = _create_driver_entry(
            data_per_driver,
            best_s1_time,
            best_s2_time,
            best_s3_time,
            fastest_lap_driver_index,
            result_str_map
        )
        json_response["table-entries"].append(driver_entry)

    # Sort by track position
    json_response["table-entries"].sort(key=lambda x: x["driver-info"]["position"])

    return json_response

def _get_time_trial_telemetry_info(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the time trial telemetry response from raw JSON data."""

    player_data = json_data["classification-data"][0]
    session_history = player_data["session-history"]
    per_lap_info = player_data["per-lap-info"]

    json_response = _get_base_rsp_dict(json_data)
    json_response.update({
        "current-lap": player_data["current-lap"],
        "fastest-lap-overall-tyre": "Soft",  # TT tyres are always Soft
        "fastest-lap-driver": player_data["driver-name"],
        "fastest-lap-overall": 0,
    })

    # Add fastest lap info if available
    if best_lap_num := session_history.get("best-lap-time-lap-num"):
        best_lap_idx = best_lap_num - 1
        lap_history = session_history["lap-history-data"]
        if 0 <= best_lap_idx < len(lap_history):
            json_response["fastest-lap-overall"] = lap_history[best_lap_idx]["lap-time-in-ms"]

    # Insert top speed into session history
    lap_info_by_number = {info["lap-number"]: info for info in per_lap_info}
    for index, lap_data in enumerate(session_history["lap-history-data"]):
        if lap_info := lap_info_by_number.get(index + 1): # Lap numbers start at 1
            lap_data["top-speed-kmph"] = lap_info["top-speed-kmph"]

    # Wrap up time trial-specific data
    json_response["tt-data"] = {
        "session-history": session_history,
        "tt-data": None,
        "tt-setups": None,
    }

    return json_response

def _get_empty_telemetry_info() -> Dict[str, Any]:
    """
    Return a default telemetry information dictionary when no data is available.

    Returns:
        A dictionary with placeholder/default values representing telemetry data.
    """
    return {
        "live-data": False,
        "circuit": "---",
        "current-lap": "---",
        "event-type": "---", # for backward compatibility
        "session-type": "---",
        "session-uid": None,
        "fastest-lap-overall": 0,
        "fastest-lap-overall-driver": "---",
        "pit-speed-limit": 0,
        "race-ended": True,
        "safety-car-status": "",
        "table-entries": [],
        "total-laps": "---",
        "track-temperature": 0,
        "air-temperature": 0,
        "weather-forecast-samples": [],
        "f1-game-year": None,
        "f1-packet-format": None,
        "is-spectating": False,
        "spectator-car-index": None,
        "wdt-status": False,
    }

def _get_base_rsp_dict(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get the base response dictionary from the JSON data."""

    return {
        "live-data": False,
        "circuit": json_data["session-info"]["track-id"],
        "track-temperature": json_data["session-info"]["track-temperature"],
        "air-temperature": json_data["session-info"]["air-temperature"],
        "event-type": json_data["session-info"]["session-type"],
        "session-type": json_data["session-info"]["session-type"],
        "session-uid": 0, # not important
        "session-time-left": 0,
        "total-laps": json_data["session-info"]["total-laps"],
        "current-lap": json_data["classification-data"][0]["lap-data"]["current-lap-num"],
        "safety-car-status": json_data["session-info"]["safety-car-status"],
        "fastest-lap-overall-tyre": None,
        "pit-speed-limit": json_data["session-info"]["pit-speed-limit"],
        "weather-forecast-samples": _create_weather_forecast_data(json_data["session-info"]),
        "race-ended": True,
        "f1-game-year": json_data["game-year"],
        "f1-packet-format": json_data.get("packet-format"),
        "packet-format": json_data.get("packet-format"),
        "is-spectating": False,
        "spectator-car-index": None,
        "wdt-status": False,
    }


def _get_tyre_wear_json(data_per_driver: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract tyre wear data for a driver and return as JSON format.

    Args:
        data_per_driver: Driver's telemetry data containing car damage info

    Returns:
        TyreWearPerLap JSON representation with wear data for all four tyres
    """
    if "car-damage" not in data_per_driver:
        return TyreWearPerLap(
            fl_tyre_wear=None,
            fr_tyre_wear=None,
            rl_tyre_wear=None,
            rr_tyre_wear=None,
            desc="curr tyre wear"
        ).toJSON()

    tyres_wear = data_per_driver["car-damage"]["tyres-wear"]
    return TyreWearPerLap(
        fl_tyre_wear=tyres_wear[F1Utils.INDEX_FRONT_LEFT],
        fr_tyre_wear=tyres_wear[F1Utils.INDEX_FRONT_RIGHT],
        rl_tyre_wear=tyres_wear[F1Utils.INDEX_REAR_LEFT],
        rr_tyre_wear=tyres_wear[F1Utils.INDEX_REAR_RIGHT],
        desc="curr tyre wear"
    ).toJSON()


def _get_fastest_lap_time_ms(session_history: Dict[str, Any]) -> int:
    """
    Extract fastest lap time in milliseconds from session history.

    Args:
        session_history: Session history data containing lap times

    Returns:
        Fastest lap time in milliseconds, or 0 if no valid lap found
    """
    fastest_lap_num = session_history["best-lap-time-lap-num"]
    if fastest_lap_num == 0:
        return 0

    fastest_lap_index = fastest_lap_num - 1
    assert 0 <= fastest_lap_index < len(session_history["lap-history-data"])

    return session_history["lap-history-data"][fastest_lap_index]["lap-time-in-ms"]


def _get_last_lap_time_ms(session_history: Dict[str, Any]) -> int:
    """
    Extract the most recent completed lap time in milliseconds.

    Args:
        session_history: Session history data containing lap times

    Returns:
        Last completed lap time in milliseconds, or 0 if no valid lap found
    """
    if last_lap := next(
        (entry for entry in reversed(session_history["lap-history-data"])
         if entry.get("lap-time-in-ms", 0) > 0),
        None
    ):
        return last_lap["lap-time-in-ms"]
    return 0


def _get_sector_status_for_lap(
    lap_obj: Dict[str, Any],
    sector_1_best_ms: int,
    sector_2_best_ms: int,
    sector_3_best_ms: int,
    best_sector_1_lap: int,
    best_sector_2_lap: int,
    best_sector_3_lap: int,
    lap_num: int
) -> List[int]:
    """
    Determine sector status (purple/green/yellow/invalid) for a specific lap.

    Args:
        lap_obj: Lap data object containing sector times and validity flags
        sector_1_best_ms: Global best sector 1 time in milliseconds
        sector_2_best_ms: Global best sector 2 time in milliseconds
        sector_3_best_ms: Global best sector 3 time in milliseconds
        best_sector_1_lap: Lap number with driver's best sector 1 time
        best_sector_2_lap: Lap number with driver's best sector 2 time
        best_sector_3_lap: Lap number with driver's best sector 3 time
        lap_num: Current lap number being analyzed

    Returns:
        List of three sector statuses [s1_status, s2_status, s3_status]
    """
    lap_valid_flags = lap_obj["lap-valid-bit-flags"]

    s1_status = _get_single_sector_status(
        lap_obj["sector-1-time-in-ms"],
        sector_1_best_ms,
        lap_num == best_sector_1_lap,
        lap_valid_flags & LapHistoryData.SECTOR_1_VALID_BIT_MASK
    )

    s2_status = _get_single_sector_status(
        lap_obj["sector-2-time-in-ms"],
        sector_2_best_ms,
        lap_num == best_sector_2_lap,
        lap_valid_flags & LapHistoryData.SECTOR_2_VALID_BIT_MASK
    )

    s3_status = _get_single_sector_status(
        lap_obj["sector-3-time-in-ms"],
        sector_3_best_ms,
        lap_num == best_sector_3_lap,
        lap_valid_flags & LapHistoryData.SECTOR_3_VALID_BIT_MASK
    )

    return [s1_status, s2_status, s3_status]

def _get_single_sector_status(
    sector_time: int,
    sector_best_ms: int,
    is_best_sector_lap: bool,
    sector_valid_flag: bool
) -> int:
    """
    Determine the status of a single sector.

    Args:
        sector_time: Time of the current sector in milliseconds
        sector_best_ms: Best time for the sector in milliseconds
        is_best_sector_lap: Whether this is the driver's best lap for this sector
        sector_valid_flag: Whether the sector is valid (not invalidated)

    Returns:
        Sector status: purple (session best), green (personal best),
        yellow (normal), or invalid
    """
    if sector_time == sector_best_ms:
        return F1Utils.SECTOR_STATUS_PURPLE
    if is_best_sector_lap:
        return F1Utils.SECTOR_STATUS_GREEN
    if not sector_valid_flag:
        return F1Utils.SECTOR_STATUS_INVALID
    return F1Utils.SECTOR_STATUS_YELLOW

def _get_sector_status(
    data_per_driver: Dict[str, Any],
    sector_1_best_ms_global: Optional[int],
    sector_2_best_ms_global: Optional[int],
    sector_3_best_ms_global: Optional[int],
    result_status: Optional[str],
    for_best_lap: bool
) -> List[Optional[int]]:
    """
    Determine sector status for either best or last lap of a driver.

    Args:
        data_per_driver: Driver's complete telemetry data
        sector_1_best_ms_global: Global best sector 1 time in milliseconds
        sector_2_best_ms_global: Global best sector 2 time in milliseconds
        sector_3_best_ms_global: Global best sector 3 time in milliseconds
        result_status: Driver's current result status (active, DNF, etc.)
        for_best_lap: Whether to analyze best lap (True) or last lap (False)

    Returns:
        List of sector statuses [s1, s2, s3] or default NA values if data unavailable
    """
    default_val = [
        F1Utils.SECTOR_STATUS_NA,
        F1Utils.SECTOR_STATUS_NA,
        F1Utils.SECTOR_STATUS_NA
    ]

    packet_session_history = data_per_driver.get("session-history")

    # Validate input data
    if (not packet_session_history or
        not sector_1_best_ms_global or
        not sector_2_best_ms_global or
        not sector_3_best_ms_global):
        return default_val

    # Get lap time data
    best_lap_ms = _get_fastest_lap_time_ms(packet_session_history)
    last_lap_ms = _get_last_lap_time_ms(packet_session_history)
    current_lap = data_per_driver["current-lap"]

    # Validate lap data exists
    if for_best_lap and not best_lap_ms:
        return default_val
    if (not for_best_lap) and not last_lap_ms:
        return default_val

    # Determine which lap to analyze
    if for_best_lap:
        lap_num = packet_session_history["best-lap-time-lap-num"]
    elif result_status != str(ResultStatus.ACTIVE):
        lap_num = current_lap
    else:
        lap_num = current_lap - 1

    # Validate lap number exists in history
    if not (0 <= lap_num <= len(packet_session_history["lap-history-data"])):
        return default_val

    # Get lap object and best sector lap numbers
    lap_obj = packet_session_history["lap-history-data"][lap_num - 1]
    best_sector_1_lap = packet_session_history["best-sector-1-lap-num"]
    best_sector_2_lap = packet_session_history["best-sector-2-lap-num"]
    best_sector_3_lap = packet_session_history["best-sector-3-lap-num"]

    return _get_sector_status_for_lap(
        lap_obj,
        sector_1_best_ms_global,
        sector_2_best_ms_global,
        sector_3_best_ms_global,
        best_sector_1_lap,
        best_sector_2_lap,
        best_sector_3_lap,
        lap_num
    )


def _extract_fastest_lap_info(g_json_data: Dict[str, Any]) -> tuple[Any, str]:
    """
    Extract fastest lap time and driver name from global data.

    Args:
        g_json_data: Global telemetry data

    Returns:
        Tuple of (fastest_lap_time, fastest_lap_driver_name)
    """
    if "records" in g_json_data and "fastest" in g_json_data["records"]:
        fastest_lap = g_json_data["records"]["fastest"]["lap"]["time"]
        fastest_lap_driver = g_json_data["records"]["fastest"]["lap"]["driver-name"]
    else:
        fastest_lap = "---"
        fastest_lap_driver = "---"

    return fastest_lap, fastest_lap_driver


def _create_weather_forecast_data(session_info: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert weather forecast samples to the expected JSON format.

    Args:
        session_info: Session information containing weather forecast samples

    Returns:
        List of weather forecast dictionaries
    """
    return [
        {
            "time-offset": str(sample["time-offset"]),
            "weather": str(sample["weather"]),
            "rain-probability": str(sample["rain-percentage"])
        }
        for sample in session_info["weather-forecast-samples"]
    ]


def _create_driver_entry(
    data_per_driver: Dict[str, Any],
    best_s1_time: int,
    best_s2_time: int,
    best_s3_time: int,
    fastest_lap_driver_index: int,
    result_str_map: Dict[str, str]
) -> Dict[str, Any]:
    """
    Create a complete table entry for a single driver.

    Args:
        data_per_driver: Individual driver's telemetry data
        best_s1_time: Global best sector 1 time
        best_s2_time: Global best sector 2 time
        best_s3_time: Global best sector 3 time
        fastest_lap_driver_index: Index of driver with fastest lap
        result_str_map: Mapping of result status codes to display strings

    Returns:
        Complete driver entry dictionary for the telemetry table
    """
    index = data_per_driver["index"]
    position = data_per_driver["track-position"]

    # Calculate delta times
    if position == 1:
        delta_relative = 0
    else:
        delta_relative = data_per_driver["lap-data"]["delta-to-race-leader-in-ms"]

    # Driver status and flags
    is_fastest = (index == fastest_lap_driver_index)
    dnf_status_code = result_str_map.get(data_per_driver["lap-data"]["result-status"], "")

    # ERS percentage calculation
    ers_perc = (data_per_driver["car-status"]["ers-store-energy"] /
                data_per_driver["car-status"]["ers-max-capacity"] * 100.0)

    # Penalties
    time_pens = data_per_driver["lap-data"]["penalties"]
    num_dt = data_per_driver["lap-data"]["num-unserved-drive-through-pens"]
    num_sg = data_per_driver["lap-data"]["num-unserved-stop-go-pens"]

    # Pit stops count
    num_pitstops = None
    if data_per_driver.get("final-classification") is not None:
        num_pitstops = data_per_driver["final-classification"]["num-pit-stops"]
    elif data_per_driver.get("lap-data", {}).get("num-pit-stops") is not None:
        num_pitstops = data_per_driver["lap-data"]["num-pit-stops"]

    return {
        "driver-info": {
            "position": position,
            "name": data_per_driver["driver-name"],
            "team": data_per_driver["participant-data"]["team-id"],
            "is-fastest": is_fastest,
            "is-player": data_per_driver["is-player"],
            "dnf-status": dnf_status_code,
            "index": index,
            "telemetry-setting": data_per_driver["participant-data"]["telemetry-setting"],
            "drs": False,
        },
        "delta-info": {
            "delta": delta_relative,
            "delta-to-leader": delta_relative,
        },
        "ers-info": {
            "ers-percent": f'{F1Utils.floatToStr(ers_perc)}%',
            "ers-percent-float": ers_perc,
            "ers-mode": data_per_driver["car-status"].get("ers-deploy-mode", "None"),
        },
        "lap-info": {
            "current-lap": None,
            "last-lap": {
                "lap-time-ms": _get_last_lap_time_ms(data_per_driver["session-history"]),
                "sector-status": _get_sector_status(
                    data_per_driver,
                    best_s1_time,
                    best_s2_time,
                    best_s3_time,
                    data_per_driver["lap-data"]["result-status"],
                    for_best_lap=False,
                ),
            },
            "best-lap": {
                "lap-time-ms": _get_fastest_lap_time_ms(data_per_driver["session-history"]),
                "sector-status": _get_sector_status(
                    data_per_driver,
                    best_s1_time,
                    best_s2_time,
                    best_s3_time,
                    data_per_driver["lap-data"]["result-status"],
                    for_best_lap=True,
                ),
            },
            "lap-progress": None,
            "speed-trap-record-kmph": data_per_driver["lap-data"].get("speed-trap-fastest-speed"),
            "top-speed-kmph": data_per_driver.get("top-speed-kmph", 0.0),
        },
        "warns-pens-info": {
            "corner-cutting-warnings": data_per_driver["lap-data"]["corner-cutting-warnings"],
            "time-penalties": time_pens,
            "num-dt": num_dt,
            "num-sg": num_sg,
        },
        "tyre-info": {
            "wear-prediction": {
                "status": False,
                "desc": "Insufficient data for extrapolation",
                "predictions": [],
                "selected-pit-stop-lap": None,
            },
            "current-wear": _get_tyre_wear_json(data_per_driver),
            "tyre-age": data_per_driver["car-status"]["tyres-age-laps"],
            "tyre-life-remaining": None,
            "actual-tyre-compound": data_per_driver["car-status"]["actual-tyre-compound"],
            "visual-tyre-compound": data_per_driver["car-status"]["visual-tyre-compound"],
            "num-pitstops": num_pitstops,
        },
        "damage-info": {
            "fl-wing-damage": data_per_driver["car-damage"]["front-left-wing-damage"],
            "fr-wing-damage": data_per_driver["car-damage"]["front-right-wing-damage"],
            "rear-wing-damage": data_per_driver["car-damage"]["rear-wing-damage"],
        },
        "fuel-info": {
            "fuel-capacity": data_per_driver["car-status"]["fuel-capacity"],
            "fuel-mix": data_per_driver["car-status"]["fuel-mix"],
            "fuel-remaining-laps": data_per_driver["car-status"]["fuel-remaining-laps"],
            "fuel-in-tank": data_per_driver["car-status"]["fuel-in-tank"],
            "curr-fuel-rate": 0.0,
            "last-lap-fuel-used": 0.0,
            "target-fuel-rate-average": 0.0,
            "target-fuel-rate-next-lap": 0.0,
            "surplus-laps-png": 0.0,
            "surplus-laps-game": 0.0,
        },
    }
