# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from typing import TYPE_CHECKING, Optional

from lib.f1_types import (ActualTyreCompound, FinalClassificationData,
                          PacketFinalClassificationData, ResultReason,
                          ResultStatus, VisualTyreCompound)

if TYPE_CHECKING:
    from apps.backend.state_mgmt_layer.session_info import SessionInfo

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class DummyFinalClassificationMixin:
    """SessionState mixin: placeholder final-classification objects for a session that never
    received a real FINAL_CLASSIFICATION packet (e.g. a just-in-case save). Field values don't
    matter beyond count/format - buildFinalClassificationJSON only uses these to iterate; all
    real data comes from DataPerDriver."""

    __slots__ = ()

    # Provided by SessionState - declared here so a type checker resolves them on self
    # inside this mixin's own methods, without runtime cost or a circular import.
    if TYPE_CHECKING:
        m_num_active_cars: Optional[int]
        m_session_info: "SessionInfo"

    def _getDummyFinalClassificationPacket(self) -> PacketFinalClassificationData:
        """Returns a dummy final classification packet object

        Returns:
            PacketFinalClassificationData: A dummy final classification packet
        """
        packet = PacketFinalClassificationData.from_values(None, 0, [])
        packet.m_numCars = self.m_num_active_cars
        # Field values don't matter - buildFinalClassificationJSON only iterates over
        # m_classificationData for its length; all real data comes from DataPerDriver.
        packet.m_classificationData = [self._getDummyFinalClassificationData() for _ in range(self.m_num_active_cars)]
        return packet

    def _getDummyFinalClassificationData(self) -> FinalClassificationData:
        """Returns a dummy final classification data object

        Returns:
            FinalClassificationData: A dummy final classification data object
        """
        return FinalClassificationData.from_values(
            packet_format=self.m_session_info.m_packet_format,
            position=0,
            num_laps=0,
            grid_position=0,
            points=0,
            num_pit_stops=0,
            result_status=ResultStatus.INVALID,
            result_reason=ResultReason.INVALID,
            best_lap_time_in_ms=0,
            total_race_time=0,
            penalties_time=0,
            num_penalties=0,
            num_tyre_stints=0,
            # tyre_stints_actual,  # array of 8
            tyre_stints_actual_0=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_1=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_2=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_3=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_4=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_5=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_6=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_7=ActualTyreCompound.UNKNOWN,
            # tyre_stints_visual,  # array of 8
            tyre_stints_visual_0=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_1=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_2=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_3=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_4=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_5=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_6=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_7=VisualTyreCompound.UNKNOWN,
            # tyre_stints_end_laps,  # array of 8
            tyre_stints_end_laps_0=0,
            tyre_stints_end_laps_1=0,
            tyre_stints_end_laps_2=0,
            tyre_stints_end_laps_3=0,
            tyre_stints_end_laps_4=0,
            tyre_stints_end_laps_5=0,
            tyre_stints_end_laps_6=0,
            tyre_stints_end_laps_7=0
        )
