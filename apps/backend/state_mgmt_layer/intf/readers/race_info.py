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

import lib.race_analyzer as RaceAnalyzer
from apps.backend.state_mgmt_layer.session_state import SessionState

from ..base import BaseAPI
from .helpers import DriversListRsp

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class RaceInfoData(BaseAPI):
    """
    Overall race stats response class.
    """

    def __init__(self, session_state: SessionState):
        """Get the overall race stats and prepare the rsp fields

        Args:
            session_state (SessionState): Handle to the session state data structure
        """

        self.m_session_state: SessionState = session_state
        self.m_rsp = self.m_session_state.getRaceInfo()
        self._checkUpdateRecords()
        # Remove the classification-data key as it is not used by the frontend
        self.m_rsp.pop('classification-data', None)

    def _checkUpdateRecords(self):
        """
        Checks the given JSON data for the presence of certain keys and updates the data if necessary.
        """
        if "records" not in self.m_rsp:
            self.m_rsp["records"] = {}

        if "fastest" not in self.m_rsp["records"]:
            try:
                self.m_rsp["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(self.m_rsp)
            except ValueError:
                self.m_rsp["records"]["fastest"] = None

        if "tyre-stats" not in self.m_rsp["records"]:
            self.m_rsp["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(self.m_rsp)

        should_recompute_overtakes = False
        if "overtakes" not in self.m_rsp:
            self.m_rsp["overtakes"] = {
                "records" : []
            }
            should_recompute_overtakes = True

        expected_keys = [
            "number-of-overtakes",
            "number-of-times-overtaken",
            "most-heated-rivalries"
        ]
        for key in expected_keys:
            if key not in self.m_rsp["overtakes"]:
                should_recompute_overtakes = True

        if should_recompute_overtakes:
            _, overtake_records = self.m_session_state.getOvertakeJSON()
            self.m_rsp["overtakes"] = self.m_rsp["overtakes"] | overtake_records

        self.m_rsp["custom-markers"] = self.m_session_state.m_custom_markers_history.getJSONList()
        if self.m_session_state.m_session_info.is_valid:
            drivers_list_rsp = DriversListRsp(
                session_state=self.m_session_state,
                is_spectator_mode=True,
                is_tt_mode=self.m_session_state.m_session_info.m_session_type.isTimeTrialTypeSession())
            if self.m_session_state.isPositionHistorySupported():
                self.m_rsp["position-history"] = drivers_list_rsp.getPositionHistoryJSON()
                if self.m_session_state.m_session_info.m_packet_format == 2023:
                    self.m_rsp["tyre-stint-history"] = drivers_list_rsp.getTyreStintHistoryJSON()
                else:
                    self.m_rsp["tyre-stint-history-v2"] = drivers_list_rsp.getTyreStintHistoryJSONv2()
            self.m_rsp["speed-trap-records"] = drivers_list_rsp.getSpeedTrapRecordsJSON()

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return self.m_rsp
