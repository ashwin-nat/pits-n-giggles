
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

_globals_lock = threading.Lock()
_driver_data_lock = threading.Lock()


class GlobalData:

    def __init__(self):

        self.m_circuit = None
        self.m_event_type = None
        self.m_track_temp = None
        self.m_total_laps = None

        # print("created GlobalData object. " + str(id(self)) + " tid = " + str(threading.get_ident()))
    def __str__(self):
        return (
            f"GlobalData(m_circuit={self.m_circuit}, "
            f"m_event_type={self.m_event_type}, "
            f"m_track_temp={self.m_track_temp}, "
            f"m_total_laps={self.m_total_laps})"
        )

class DataPerDriver:

    def __init__(self):
        self.m_position = None
        self.m_name = None
        self.m_team = None
        self.m_delta = None
        self.m_ers_perc = None
        self.m_best_lap = None
        self.m_last_lap = None
        self.m_tyre_wear = None
        self.m_is_player = None
        self.m_current_lap = None
        self.m_penalties = None
        self.m_tyre_age = None
        self.m_tyre_compound_type = None
        self.m_is_pitting = None
        self.m_drs_activated = None
        self.m_drs_allowed = None
        self.m_drs_distance = None

class DriverData:

    def __init__(self):
        self.m_driver_data = {} # key = car index, value = DataPerDriver
        self.m_player_index = None
        self.m_fastest_index = None
        self.m_num_cars = None
        # print("created DriverData object. " + str(id(self)) + " tid = " + str(threading.get_ident()))

    def update_object(self, index, new_obj):
        if self.m_driver_data is None:
            self.m_driver_data = {}
        if index not in self.m_driver_data.keys():
            self.m_driver_data[index] = new_obj
        else:
            old_obj = self.m_driver_data[index]
            for attr_name in dir(old_obj):
                if not attr_name.startswith("__") and not callable(getattr(old_obj, attr_name)):

                    new_value = getattr(new_obj, attr_name, None)
                    if new_value is not None:
                        setattr(old_obj, attr_name, new_value)
            self.m_driver_data[index] = old_obj
            if new_obj.m_is_player:

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

    def get_index_driver_data_by_track_position(self, track_position):

        for index, driver_data in self.m_driver_data.items():
            if driver_data.m_position == track_position:
                return index, copy.deepcopy(driver_data)
        return None

_globals = GlobalData()
_driver_data = DriverData()

def set_globals(circuit, track_temp, event_type, total_laps):
    with _globals_lock:
        _globals.m_circuit = circuit
        _globals.m_track_temp = track_temp
        _globals.m_event_type = event_type
        _globals.m_total_laps = total_laps

def get_globals():
    with _globals_lock:
        with _driver_data_lock: # we need this for current lap
            player_index = _driver_data.m_player_index
            curr_lap = _driver_data.m_driver_data[player_index].m_current_lap if player_index is not None else None
            return (_globals.m_circuit, _globals.m_track_temp, _globals.m_event_type, _globals.m_total_laps, curr_lap)

def set_driver_data(index: int, driver_data: DataPerDriver, is_fastest=False):
    with _driver_data_lock:
        _driver_data.update_object(index, driver_data)
        if is_fastest:
            # First clear old fastest
            _driver_data.m_fastest_index = index
        # return whether fastest lap needs to be recomputed later (we missed the fastest lap event)
        if (_driver_data.m_fastest_index is None) and (_driver_data.m_num_cars is not None):
            count_null_best_times = 0
            for curr_index, driver_data in _driver_data.m_driver_data.items():
                if curr_index >= _driver_data.m_num_cars:
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

def _convert_to_milliseconds(time_str):
    minutes, seconds_with_milliseconds = map(str, time_str.split(':'))
    seconds, milliseconds = map(int, seconds_with_milliseconds.split('.'))
    total_milliseconds = int(minutes) * 60 * 1000 + seconds * 1000 + milliseconds
    return total_milliseconds

def recompute_fastest_lap():
    with _driver_data_lock:
        # TODO - handle case where multiple cars have same fastest time.
        _driver_data.m_fastest_index = None
        fastest_time_ms = 500000000000 # cant be slower than this, right?
        for index, driver_data in _driver_data.m_driver_data.items():
            if driver_data.m_best_lap is not None:
                temp_lap_ms = _convert_to_milliseconds(driver_data.m_best_lap)
                if temp_lap_ms > 0 and temp_lap_ms < fastest_time_ms:
                    fastest_time_ms = temp_lap_ms
                    _driver_data.m_fastest_index = index


def set_num_cars(num_cars: int) -> None:
    with _driver_data_lock:
        _driver_data.m_num_cars = num_cars

def clear_all_driver_data():
    with _driver_data_lock:
        _driver_data.set_members_to_none()

def _get_adjacent_positions(position, total_cars=20, num_adjacent_cars=3):
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

def _get_cars_in_front_and_behind(track_positions, player_position):
    # Ensure the track positions are sorted
    sorted_positions = sorted(track_positions)

    # Find the index of the player's car in the sorted positions
    player_index = sorted_positions.index(player_position)

    # Cars in front of the player
    cars_in_front = sorted_positions[:player_index]

    # Cars behind the player
    cars_behind = sorted_positions[player_index + 1:]

    return cars_in_front, cars_behind

def get_driver_data(short=True) -> list[DataPerDriver]:

    with _driver_data_lock:
        final_list = []
        if (_driver_data.m_player_index) is None or (_driver_data.m_num_cars is None):
            return final_list
        player_position = _driver_data.m_driver_data[_driver_data.m_player_index].m_position
        positions = _get_adjacent_positions(player_position, total_cars=_driver_data.m_num_cars)
        for position in positions:
            index, temp_data = _driver_data.get_index_driver_data_by_track_position(position)
            temp_data.m_is_fastest = True if (index == _driver_data.m_fastest_index) else False
            if temp_data.m_ers_perc is not None:
                temp_data.m_ers_perc = ("{:.2f}".format(temp_data.m_ers_perc)) + "%"
            if temp_data.m_tyre_wear is not None:
                temp_data.m_tyre_wear = ("{:.2f}".format(temp_data.m_tyre_wear)) + "%"
            final_list.append(temp_data)

        if len(final_list) > 0:
            # recompute the deltas

            condition = lambda x: x.m_is_player == True
            player_index = next((index for index, item in enumerate(final_list) if condition(item)), None)

            # case 1: player is in the absolute front of this pack
            milliseconds_to_seconds = lambda ms: ("+" if ms >= 0 else "") + "{:.3f}".format(ms / 1000)
            if player_index == 0:
                final_list[0].m_delta = "---"
                delta_so_far = 0
                for data in final_list[1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds(delta_so_far)

            # case 2: player is in the back of the pack
            # Iterate from back to front using reversed need to look at previous car's data for distance ahead
            elif player_index == len(final_list) - 1:
                delta_so_far = 0
                one_car_behind_index = len(final_list)-1
                one_car_behind_delta = final_list[one_car_behind_index].m_delta
                for data in reversed(final_list[:len(final_list)-1]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta
                    data.m_delta = milliseconds_to_seconds(delta_so_far)
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
                    data.m_delta = milliseconds_to_seconds(delta_so_far)

                # Finally, set the deltas for the cars ahead
                delta_so_far = 0
                for data in final_list[player_index+1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds(delta_so_far)

                # first set the delta for the player
                final_list[player_index].m_delta = "---"

        return final_list