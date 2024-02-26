
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

from collections import defaultdict
import threading
import copy
from f1_types import *
import csv
from io import StringIO

_globals_lock = threading.Lock()
_driver_data_lock = threading.Lock()


class GlobalData:

    def __init__(self):

        self.m_circuit = None
        self.m_event_type = None
        self.m_track_temp = None
        self.m_total_laps = None
        self.m_safety_car_status = None
        self.m_is_spectating = None
        self.m_spectator_car_index = None
        self.m_weather_forecast_samples = None
        self.m_pit_speed_limit = None
        self.m_final_classification_received = None

    def __str__(self):
        return (
            f"GlobalData(m_circuit={self.m_circuit}, "
            f"m_event_type={self.m_event_type}, "
            f"m_track_temp={self.m_track_temp}, "
            f"m_total_laps={self.m_total_laps}, "
            f"m_safety_car_status={str(self.m_safety_car_status)}, "
            f"m_is_spectating={str(self.m_is_spectating)}"
            f"m_spectator_car_index={str(self.m_spectator_car_index)}, "
            f"m_weather_forecast_samples={str(self.m_weather_forecast_samples)}, "
            f"m_pit_speed_limit={str(self.m_pit_speed_limit)}, "
            f"m_final_classification_received={str(self.m_final_classification_received)}")

class DataPerDriver:

    def __init__(self):
        self.m_position = None
        self.m_name = None
        self.m_team = None
        self.m_delta = None
        self.m_delta_to_leader = None
        self.m_ers_perc = None
        self.m_best_lap = None
        self.m_last_lap = None
        self.m_tyre_wear = None
        self.m_is_player = None
        self.m_current_lap = None
        self.m_penalties = None
        self.m_tyre_age = None
        self.m_tyre_compound_type = None
        self.m_tyre_surface_temp = None
        self.m_tyre_inner_temp = None
        self.m_is_pitting = None
        self.m_drs_activated = None
        self.m_drs_allowed = None
        self.m_drs_distance = None
        self.m_num_pitstops = None
        self.m_dnf_status_code = None
        self.m_tyre_life_remaining_laps = None
        self.m_telemetry_restrictions = None

class DriverData:

    def __init__(self):
        self.m_driver_data = {} # key = car index, value = DataPerDriver
        self.m_player_index = None
        self.m_fastest_index = None
        self.m_num_active_cars = None
        self.m_num_dnf_cars = None
        self.m_race_completed = None

    def update_object(self, index, new_obj):
        # For the first driver, the data structure will be None, create it
        if self.m_driver_data is None:
            self.m_driver_data = {}
        # The index may not be added into the data structure yet
        if index not in self.m_driver_data.keys():
            self.m_driver_data[index] = new_obj
        else:
            old_obj = self.m_driver_data[index]
            # Loop through every attribute in the object
            for attr_name in dir(old_obj):
                if not attr_name.startswith("__") and not callable(getattr(old_obj, attr_name)):
                    # For all non default/builtin attributes
                    new_value = getattr(new_obj, attr_name, None)
                    if new_value is not None:
                        setattr(old_obj, attr_name, new_value)
            self.m_driver_data[index] = old_obj
            if new_obj.m_is_player:
                # If we are updating the player's object
                if self.m_player_index is None:
                    self.m_player_index = index
                elif self.m_player_index != index:
                    # Clear the flag from the old driver entry and update the global index var
                    self.m_driver_data[self.m_player_index].m_is_player = False
                    self.m_player_index = index

    def set_members_to_none(self):
        # Get all class attributes (members)
        members = vars(self)

        # Iterate through the members and set them to None
        for member in members:
            setattr(self, member, None)

    def get_index_driver_data_by_track_position(self, track_position) -> Tuple[int, DataPerDriver]:

        for index, driver_data in self.m_driver_data.items():
            if driver_data.m_position == track_position:
                return index, copy.deepcopy(driver_data)
        return None, None

_globals = GlobalData()
_driver_data = DriverData()

def set_globals(circuit, track_temp, event_type, total_laps, safety_car_status, is_spectating,
                    spectator_car_index, weather_forecast_samples, pit_speed_limit):
    with _globals_lock:
        _globals.m_circuit = circuit
        _globals.m_track_temp = track_temp
        _globals.m_event_type = event_type
        _globals.m_total_laps = total_laps
        _globals.m_safety_car_status = safety_car_status
        _globals.m_is_spectating = is_spectating
        _globals.m_spectator_car_index = spectator_car_index
        _globals.m_weather_forecast_samples = weather_forecast_samples
        _globals.m_pit_speed_limit = pit_speed_limit

def getGlobals(num_weather_forecast_samples=4) -> Tuple[str, int, str, int, int, str, List[WeatherForecastSample], int, bool]:
    """
    Retrieves the global info regarding the current session

    Parameters:
    - num_weather_forecast_samples (int): Number of weather forecast samples to retrieve (default is 4).

    Returns:
        Tuple[str, int, str, int, int, str, List[WeatherForecastSample]]:
            1: Circuit name (str)
            2: Track temperature (int)
            3: Event type (str)
            4: Total number of laps in the race (int)
            5: Current lap of the player (int or None if player index is None)
            6: Safety car status (str)
            7: List of weather forecast samples (List[WeatherForecastSample])
            8: Pit speed limit (int)
            9: Final Classification Received (bool)
    """
    with _globals_lock:
        with _driver_data_lock: # we need this for current lap
            player_index = _driver_data.m_player_index
            curr_lap = _driver_data.m_driver_data[player_index].m_current_lap if player_index is not None else None
            if _globals.m_weather_forecast_samples is not None:
                weather_forecast_samples = _globals.m_weather_forecast_samples[:num_weather_forecast_samples]
            else:
                weather_forecast_samples = []
            return (_globals.m_circuit, _globals.m_track_temp, _globals.m_event_type,
                        _globals.m_total_laps, curr_lap, _globals.m_safety_car_status,
                            weather_forecast_samples, _globals.m_pit_speed_limit, _globals.m_final_classification_received)

def getEventInfoStr() -> str:
    with _globals_lock:
        if _globals.m_event_type and _globals.m_circuit:
            return (_globals.m_event_type + "_" + _globals.m_circuit).replace(' ', '_') + '_'
        else:
            return None

def getPlayerName() -> str:
    """Get the player's name.

    Returns:
        str: Player's name. None if not found (can be in spectator mode or before PNG has received sufficient data)
    """
    with _driver_data_lock:
        player_data = _driver_data.m_driver_data.get(_driver_data.m_player_index, None)
        return player_data.m_name if player_data else None

def set_driver_data(index: int, driver_data: DataPerDriver, is_fastest=False):
    with _driver_data_lock:
        _driver_data.m_race_completed = False
        _driver_data.update_object(index, driver_data)
        if is_fastest:
            # First clear old fastest
            _driver_data.m_fastest_index = index
        # return whether fastest lap needs to be recomputed later (we missed the fastest lap event)
        if (_driver_data.m_fastest_index is None) and (_driver_data.m_num_active_cars is not None):
            count_null_best_times = 0
            for curr_index, driver_data in _driver_data.m_driver_data.items():
                if curr_index >= _driver_data.m_num_active_cars:
                    continue
                if driver_data.m_best_lap is None:
                    count_null_best_times += 1
            if count_null_best_times == 0:
                # only recompute once all the best lap times are available
                return True
            else:
                return False
        else:
            return False

# def getOvertakeString(overtaking_car_index: int, being_overtaken_index: int) -> str:
#     """Returns a comma separating string containing overtake information

#     Args:
#         overtaking_car_index (int): The index of the overtaking car
#         being_overtaken_index (int): The index of the car being overtaken

#     Returns:
#         str: comma separated string containing 4 values
#             - Current Lap number of overtaking car
#             - Name of driver of overtaking car
#             - Current Lap number of car being overtaken
#             - Name of driver of car being overtaken
#     """
#     with _driver_data_lock:
#         if not _driver_data.m_driver_data:
#             return None
#         overtaking_car_obj      = _driver_data.m_driver_data.get(overtaking_car_index, None)
#         being_overtaken_car_obj = _driver_data.m_driver_data.get(being_overtaken_index, None)
#         if (overtaking_car_obj is None) or (being_overtaken_car_obj is None):
#             return None

#         # Format is Lap_Overtaking_car, Name_overtaking_car, Lap_overtaken_car, Name_overtaken_car
#         return (
#             str(overtaking_car_obj.m_current_lap) + ' ,' +
#             overtaking_car_obj.m_name + ',' +
#             str(being_overtaken_car_obj.m_current_lap) + ',' +
#             being_overtaken_car_obj.m_name
#         )

def getOvertakeString(overtaking_car_index: int, being_overtaken_index: int) -> str:
    """Returns a CSV-formatted string containing overtake information

    Args:
        overtaking_car_index (int): The index of the overtaking car
        being_overtaken_index (int): The index of the car being overtaken

    Returns:
        str: CSV-formatted string containing 4 values
            - Current Lap number of overtaking car
            - Name of driver of overtaking car
            - Current Lap number of car being overtaken
            - Name of driver of car being overtaken
    """
    with _driver_data_lock:
        if not _driver_data.m_driver_data:
            return None
        overtaking_car_obj = _driver_data.m_driver_data.get(overtaking_car_index, None)
        being_overtaken_car_obj = _driver_data.m_driver_data.get(being_overtaken_index, None)
        if overtaking_car_obj is None or being_overtaken_car_obj is None:
            return None

        # Prepare data for CSV writing
        data = [
            overtaking_car_obj.m_current_lap,
            overtaking_car_obj.m_name,
            being_overtaken_car_obj.m_current_lap,
            being_overtaken_car_obj.m_name
        ]

        # Use CSV writer to handle quoting and escaping
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(data)

        # Get the CSV-formatted string
        csv_string = csv_buffer.getvalue().strip()
        return csv_string

def set_final_classification(packet: PacketFinalClassificationData) -> None:
    with _driver_data_lock:
        _driver_data.m_race_completed = True
        for index, data in enumerate(packet.m_classificationData):
            if index in _driver_data.m_driver_data:
                _driver_data.m_driver_data[index].m_position = data.m_position
    with _globals_lock:
        _globals.m_final_classification_received = True

def millisecondsToMinutesSeconds(milliseconds):
    if not isinstance(milliseconds, int):
        raise ValueError("Input must be an integer representing milliseconds")

    if milliseconds < 0:
        raise ValueError("Input must be a non-negative integer")

    total_seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(total_seconds, 60)

    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

def set_all_driver_data(packet: PacketFinalClassificationData):

    with _driver_data_lock:
        for index, data in enumerate(packet.m_classificationData):
            driver_data = DataPerDriver()
            driver_data.m_best_lap = millisecondsToMinutesSeconds(data.m_bestLapTimeInMS)
            driver_data.m_position = data.m_position
            driver_data.m_penalties = "" if (data.m_penaltiesTime == 0) else ("(" + str(data.m_penaltiesTime) + " sec)")
            _driver_data.update_object(index, driver_data)

        if _driver_data.m_fastest_index is None:
            _recompute_fastest_lap_no_mutex()

def _convert_to_milliseconds(time_str):
    minutes, seconds_with_milliseconds = map(str, time_str.split(':'))
    seconds, milliseconds = map(int, seconds_with_milliseconds.split('.'))
    total_milliseconds = int(minutes) * 60 * 1000 + seconds * 1000 + milliseconds
    return total_milliseconds

def _recompute_fastest_lap_no_mutex():
    # TODO - handle case where multiple cars have same fastest time.
    _driver_data.m_fastest_index = None
    fastest_time_ms = 500000000000 # cant be slower than this, right?
    for index, driver_data in _driver_data.m_driver_data.items():
        if driver_data.m_best_lap is not None:
            temp_lap_ms = _convert_to_milliseconds(driver_data.m_best_lap)
            if temp_lap_ms > 0 and temp_lap_ms < fastest_time_ms:
                fastest_time_ms = temp_lap_ms
                _driver_data.m_fastest_index = index

def recompute_fastest_lap():
    with _driver_data_lock:
        _recompute_fastest_lap_no_mutex()

def set_num_cars(num_active_cars: int) -> None:
    with _driver_data_lock:
        _driver_data.m_num_active_cars = num_active_cars

def increment_dnf_counter() -> None:
    with _driver_data_lock:
        if _driver_data.m_num_dnf_cars is None:
            _driver_data.m_num_dnf_cars = 1
        else:
            _driver_data.m_num_dnf_cars += 1

def clear_all_driver_data():
    with _driver_data_lock:
        _driver_data.set_members_to_none()
    with _globals_lock:
        _globals.m_final_classification_received = False # Mark this as False because this is the start of the race

def _get_adjacent_positions(position:int, total_cars:int=20, num_adjacent_cars:int=2) -> List[int]:
    """Get the list of positions of the race that are to be returned to the UI.
        It will include the player's position plus/minus num_adjacent_cars

    Args:
        position (int): Track position of the player
        total_cars (int, optional): Total number of cars in the race. Defaults to 20.
        num_adjacent_cars (int, optional): Number of adjacent cars to be displayed. Defaults to 2.

    Returns:
        List[int]: The final list of track positions to be displayed
    """
    if not (1 <= position <= total_cars):
        return []

    min_valid_lower_bound = 1
    max_valid_upper_bound = total_cars

    # In time trial, total_cars will be lower than num_adjacent_cars
    if num_adjacent_cars >= total_cars:
        num_adjacent_cars = total_cars
        lower_bound = min_valid_lower_bound
        upper_bound = max_valid_upper_bound

    # GP scenario, lower bound and upper bound are off input position by num_adjacent_cars
    else:
        lower_bound = position - num_adjacent_cars
        upper_bound = position + num_adjacent_cars

    # now correct if lower and upper bounds have become invalid
    if lower_bound < min_valid_lower_bound:
        # lower bound is negative, need to shift the entire window right
        upper_bound += min_valid_lower_bound - lower_bound
        lower_bound = min_valid_lower_bound
    if upper_bound > total_cars:
        # upper bound is greater than limit, need to shift the entire window left
        lower_bound = lower_bound - (upper_bound - total_cars)
        upper_bound = max_valid_upper_bound

    return list(range(lower_bound, upper_bound + 1))

def getDriverData() -> Tuple[List[DataPerDriver], str]:

    # TODO: tidy up
    with _globals_lock:
        is_spectator_mode = _globals.m_is_spectating
    with _driver_data_lock:
        final_list = []
        fastest_lap_time = "---"
        if (_driver_data.m_player_index) is None or (_driver_data.m_num_active_cars is None):
            return final_list, fastest_lap_time
        player_position = _driver_data.m_driver_data[_driver_data.m_player_index].m_position
        total_cars = _driver_data.m_num_active_cars + \
                (0 if _driver_data.m_num_dnf_cars is None else _driver_data.m_num_dnf_cars)
        if _driver_data.m_race_completed or is_spectator_mode:
            positions = [i for i in range(1, _driver_data.m_num_active_cars+1)]
        else:
            positions = _get_adjacent_positions(player_position, total_cars)
        if _driver_data.m_fastest_index is not None:
            fastest_lap_time = _driver_data.m_driver_data[_driver_data.m_fastest_index].m_best_lap
        for position in positions:
            index, temp_data = _driver_data.get_index_driver_data_by_track_position(position)
            if (index, temp_data) == (None, None):
                return []
            temp_data.m_is_fastest = True if (index == _driver_data.m_fastest_index) else False
            if temp_data.m_ers_perc is not None:
                temp_data.m_ers_perc = ("{:.2f}".format(temp_data.m_ers_perc)) + "%"
            if temp_data.m_tyre_wear is not None:
                temp_data.m_tyre_wear = ("{:.2f}".format(temp_data.m_tyre_wear)) + "%"
            temp_data.m_index = index
            if temp_data.m_telemetry_restrictions is not None:
                temp_data.m_telemetry_restrictions = str(temp_data.m_telemetry_restrictions)
            else:
                temp_data.m_telemetry_restrictions = "N/A"
            final_list.append(temp_data)

        if len(final_list) == 0:
            return final_list, fastest_lap_time

        milliseconds_to_seconds_str = lambda ms: ("+" if ms >= 0 else "") + "{:.3f}".format(ms / 1000)
        if is_spectator_mode:
            # just convert the deltas to str
            for data in final_list:
                data.m_delta = milliseconds_to_seconds_str(data.m_delta)
        else:
            # recompute the deltas if not spectator mode
            condition = lambda x: x.m_is_player == True
            player_index = next((index for index, item in enumerate(final_list) if condition(item)), None)

            # case 1: player is in the absolute front of this pack
            if player_index == 0:
                final_list[0].m_delta = "---"
                delta_so_far = 0
                for data in final_list[1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

            # case 2: player is in the back of the pack
            # Iterate from back to front using reversed need to look at previous car's data for distance ahead
            elif player_index == len(final_list) - 1:
                delta_so_far = 0
                one_car_behind_index = len(final_list)-1
                one_car_behind_delta = final_list[one_car_behind_index].m_delta
                for data in reversed(final_list[:len(final_list)-1]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)
                final_list[len(final_list)-1].m_delta = "---"

            # case 3: player is somewhere in the middle of the pack
            else:

                # First, set the deltas for the cars ahead
                delta_so_far = 0
                one_car_behind_index = player_index
                one_car_behind_delta = final_list[one_car_behind_index].m_delta
                for data in reversed(final_list[:player_index]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

                # Finally, set the deltas for the cars ahead
                delta_so_far = 0
                for data in final_list[player_index+1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

                # finally set the delta for the player
                final_list[player_index].m_delta = "---"

        return final_list, fastest_lap_time
