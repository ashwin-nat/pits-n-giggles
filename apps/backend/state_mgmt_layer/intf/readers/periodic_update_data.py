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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import logging
from typing import Any, Dict

from apps.backend.state_mgmt_layer.session_state import SessionState

from ..base import BaseAPI
from .helpers import DriversListRsp

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class PeriodicUpdateData(BaseAPI):
    """This class will prepare the live race telemetry info response. Use toJSON() method to get the JSON rsp
    """
    def __init__(self, session_state: SessionState) -> None:
        """Initialse the member variables by fetching necessary data from the data store

        Args:
            session_state (SessionState): Handle to the session state data structure
        """

        self.m_session_info = session_state.m_session_info
        self.m_wdt_status = session_state.m_connected_to_sim
        track_length = self.m_session_info.m_packet_session.m_trackLength if self.m_session_info.m_packet_session else None
        self.m_driver_list_rsp = DriversListRsp(
            session_state=session_state,
            is_spectator_mode=self.m_session_info.m_is_spectating,
            track_length=track_length,
            is_tt_mode=(str(self.m_session_info.m_session_type) == "Time Trial"))
        self.m_curr_lap = self.m_driver_list_rsp.getCurrentLap()
        if self.m_session_info.m_weather_forecast_samples is None:
            self.m_session_info.m_weather_forecast_samples = []

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON update for the current race

        Returns:
            Dict[str, Any]: JSON response.
        """

        final_json = {
            # First, global fields
            "live-data" : True,
            "f1-game-year" : self._getValueOrDefaultValue(self.m_session_info.m_game_year, None),
            "packet-format" : self._getValueOrDefaultValue(self.m_session_info.m_packet_format, None),
            "circuit": str(self.m_session_info.m_track) if self.m_session_info.m_track is not None else "---",
            "formula": str(self.m_session_info.m_formula) if self.m_session_info.m_formula is not None else None,
            "pit-time-loss": self.m_session_info.m_pit_time_loss,
            "track-temperature": self._getValueOrDefaultValue(self.m_session_info.m_track_temp, default_value=0),
            "air-temperature": self._getValueOrDefaultValue(self.m_session_info.m_air_temp, default_value=0),
            "event-type": self._getValueOrDefaultValue(str(self.m_session_info.m_session_type)),
            "session-uid" : self._getValueOrDefaultValue(self.m_session_info.m_session_uid, None),
            "session-time-left" : self._getValueOrDefaultValue(self.m_session_info.m_packet_session.m_sessionTimeLeft \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "total-laps": self._getValueOrDefaultValue(self.m_session_info.m_total_laps, default_value=None),
            "current-lap": self._getValueOrDefaultValue(self.m_curr_lap, default_value=None),
            "safety-car-status": str(self._getValueOrDefaultValue(self.m_session_info.m_safety_car_status, default_value="")),
            "pit-speed-limit": self._getValueOrDefaultValue(self.m_session_info.m_pit_speed_limit, default_value=0),
            "weather-forecast-samples": [
                {
                    "rain-probability": str(sample.m_rainPercentage), # backward compatibility
                    **sample.toJSON(),
                } for sample in self.m_session_info.m_weather_forecast_samples
            ],
            "race-ended" : self.m_session_info.session_ended,
            "is-spectating" : self._getValueOrDefaultValue(self.m_session_info.m_is_spectating, False),
            "session-type"  : str(self.m_session_info.m_session_type) \
                if self.m_session_info.m_session_type is not None else "---",
            "session-duration-so-far" : self._getValueOrDefaultValue(
                (self.m_session_info.m_packet_session.m_sessionDuration - self.m_session_info.m_packet_session.m_sessionTimeLeft) \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-sc" : self._getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numSafetyCarPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-vsc" : self._getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numVirtualSafetyCarPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-red-flags" : self._getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numRedFlagPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "player-pit-window" : self._getValueOrDefaultValue(self.m_driver_list_rsp.m_next_pit_stop_window, None),
            "spectator-car-index" : self._getValueOrDefaultValue(self.m_session_info.m_spectator_car_index, None),
            "wdt-status" : self.m_wdt_status,
        }

        if str(self.m_session_info.m_session_type) == "Time Trial":
            final_json["tt-data"] = self.m_driver_list_rsp.toJSON()
        else:
            final_json["table-entries"] = self.m_driver_list_rsp.toJSON()

        final_json["fastest-lap-overall"] = self._getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap, default_value=0)
        final_json["fastest-lap-overall-driver"] = self._getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap_driver)
        final_json["fastest-lap-overall-tyre"] = str(self.m_driver_list_rsp.m_fastest_lap_tyre) \
            if self.m_driver_list_rsp.m_fastest_lap_tyre else None
        return final_json
