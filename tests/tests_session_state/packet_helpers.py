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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Dict, List, Optional

from lib.f1_types import (F1PacketType, FinalClassificationData,
                          LapHistoryData, LiveryColour, Nationality,
                          PacketFinalClassificationData, PacketHeader,
                          PacketLapData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          ParticipantData, Platform, ResultStatus,
                          SessionType23, SessionType24, TelemetrySetting,
                          TrackID, WeatherForecastSample, get_team_id_class)
from lib.f1_types.common import get_num_cars
from lib.f1_types.packet_2_lap_data import LapData

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

# Sweep with @pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
ALL_FORMATS = [2023, 2024, 2025, 2026]

# ------------------------- SPECS --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class CarSpec:
    """One car's LAP_DATA entry. Build with car()."""
    index: int
    lap: int
    lap_distance: float
    position: int
    status: LapData.DriverStatus
    lap_time_ms: int


def car(index: int, lap: int, lap_distance: float, *,
        position: Optional[int] = None,
        status: LapData.DriverStatus = LapData.DriverStatus.ON_TRACK,
        lap_time_ms: int = 0) -> CarSpec:
    """A car on track. Position defaults to index + 1."""
    return CarSpec(index=index, lap=lap, lap_distance=lap_distance,
                   position=index + 1 if position is None else position,
                   status=status, lap_time_ms=lap_time_ms)


@dataclass(frozen=True)
class DriverSpec:
    """One PARTICIPANTS entry. Build with player() or ai()."""
    name: str
    ai_controlled: bool
    telemetry: TelemetrySetting


def player(name: str, telemetry: TelemetrySetting = TelemetrySetting.PUBLIC) -> DriverSpec:
    """A human driver."""
    return DriverSpec(name=name, ai_controlled=False, telemetry=telemetry)


def ai(name: str, telemetry: TelemetrySetting = TelemetrySetting.PUBLIC) -> DriverSpec:
    """An AI driver."""
    return DriverSpec(name=name, ai_controlled=True, telemetry=telemetry)


@dataclass(frozen=True)
class ClassifiedSpec:
    """One FINAL_CLASSIFICATION entry. Build with classified()."""
    position: int
    num_laps: int


def classified(position: int, num_laps: int) -> ClassifiedSpec:
    """A car that finished in position after num_laps."""
    return ClassifiedSpec(position=position, num_laps=num_laps)


def lap_time(lap_time_ms: int, valid: bool) -> LapHistoryData:
    """One SESSION_HISTORY lap."""
    return LapHistoryData.from_values(lap_time_ms, valid=valid)

# ------------------------- PACKETS ------------------------------------------------------------------------------------

class Packets:
    """Builds packets for one packet format. Every header gets the next frame number (frame and overall
    frame both count up from 1) unless the call overrides them."""

    def __init__(self, packet_format: int, player_index: int = 0) -> None:
        self.packet_format = packet_format
        self.player_index = player_index
        self._next_frame = 1

    def header(self, packet_type: F1PacketType, session_uid: int,
               frame: Optional[int] = None, overall_frame: Optional[int] = None) -> PacketHeader:
        """A header for packet_type. Frame and overall frame default to the next frame number."""
        if frame is None:
            frame = self._next_frame
            self._next_frame += 1
        return PacketHeader.from_values(
            packet_format=self.packet_format,
            game_year=self.packet_format % 100,
            game_major_version=1,
            game_minor_version=0,
            packet_version=1,
            packet_type=packet_type,
            session_uid=session_uid,
            session_time=frame / 60.0,
            frame_identifier=frame,
            overall_frame_identifier=frame if overall_frame is None else overall_frame,
            player_car_index=self.player_index,
            secondary_player_car_index=255,
        )

    def session(self, *, session_uid: int, session_type: str, track: TrackID, total_laps: int,
                track_length: int,
                weather: WeatherForecastSample.WeatherCondition = WeatherForecastSample.WeatherCondition.CLEAR,
                **header_kwargs: Optional[int]) -> PacketSessionData:
        """A SESSION packet. session_type is the enum member name (e.g. "RACE"), resolved per format,
        since the numeric values differ between SessionType23 and SessionType24. weather is the single
        forecast sample's weather, which the state layer reads as the current weather."""
        session_type_enum = (SessionType23 if self.packet_format == 2023 else SessionType24)[session_type]
        forecast = WeatherForecastSample.from_values(
            self.packet_format, session_type_enum, time_offset=0, weather=weather,
            track_temp=0, track_temp_change=WeatherForecastSample.TrackTemperatureChange.NO_CHANGE,
            air_temp=0, air_temp_change=WeatherForecastSample.AirTemperatureChange.NO_CHANGE, rain_percentage=0)
        return PacketSessionData.from_values(
            self.header(F1PacketType.SESSION, session_uid, **header_kwargs),
            session_type_enum, track, total_laps=total_laps, track_length=track_length,
            weather_forecast_samples=[forecast])

    def participants(self, *drivers: DriverSpec, session_uid: int, **header_kwargs: Optional[int]) -> PacketParticipantsData:
        """A PARTICIPANTS packet. drivers fill car indices 0.. in order. The rest of the grid is
        all-zero entries, as the game sends for empty slots."""
        header = self.header(F1PacketType.PARTICIPANTS, session_uid, **header_kwargs)
        entries = [self._participant(header, index, driver) for index, driver in enumerate(drivers)]
        entries += [self._empty_participant(header)] * (get_num_cars(self.packet_format) - len(entries))
        return PacketParticipantsData.from_values(header, num_active_cars=len(drivers), participants=entries)

    def lap(self, *cars: CarSpec, session_uid: int, **header_kwargs: Optional[int]) -> PacketLapData:
        """A LAP_DATA packet. Every car index not in cars is an all-zero (INVALID result status) entry,
        as the game sends for empty slots."""
        by_index: Dict[int, CarSpec] = {spec.index: spec for spec in cars}
        return PacketLapData.from_values(
            self.header(F1PacketType.LAP_DATA, session_uid, **header_kwargs),
            [self._lap_data(by_index.get(index)) for index in range(get_num_cars(self.packet_format))])

    def session_history(self, *, car_idx: int, laps: List[LapHistoryData], session_uid: int,
                        **header_kwargs: Optional[int]) -> PacketSessionHistoryData:
        """A SESSION_HISTORY packet for one car."""
        return PacketSessionHistoryData.from_values(
            self.header(F1PacketType.SESSION_HISTORY, session_uid, **header_kwargs), car_idx, laps)

    def final_classification(self, *entries: ClassifiedSpec, session_uid: int,
                             **header_kwargs: Optional[int]) -> PacketFinalClassificationData:
        """A FINAL_CLASSIFICATION packet. entries fill car indices 0.. in order, all FINISHED."""
        data = [FinalClassificationData.from_values(self.packet_format, position=entry.position,
                                                    num_laps=entry.num_laps, result_status=ResultStatus.FINISHED)
                for entry in entries]
        return PacketFinalClassificationData.from_values(
            self.header(F1PacketType.FINAL_CLASSIFICATION, session_uid, **header_kwargs), len(data), data)

    def _lap_data(self, spec: Optional[CarSpec]) -> LapData:
        active = spec is not None
        return LapData.from_values(
            last_lap_time_ms=0,
            current_lap_time_ms=spec.lap_time_ms if active else 0,
            sector1_time_ms=0, sector1_time_minutes=0,
            sector2_time_ms=0, sector2_time_minutes=0,
            delta_to_front_ms=0, delta_to_front_minutes=0,
            delta_to_leader_ms=0, delta_to_leader_minutes=0,
            lap_distance=spec.lap_distance if active else 0.0,
            total_distance=spec.lap_distance if active else 0.0,
            safety_car_delta=0.0,
            car_position=spec.position if active else 0,
            current_lap_num=spec.lap if active else 0,
            pit_status=0, num_pit_stops=0, sector=0, current_lap_invalid=0, penalties=0,
            total_warnings=0, corner_cutting_warnings=0,
            num_unserved_drive_through_pens=0, num_unserved_stop_go_pens=0,
            grid_position=spec.position if active else 0,
            driver_status=spec.status.value if active else 0,
            result_status=ResultStatus.ACTIVE.value if active else ResultStatus.INVALID.value,
            pit_lane_timer_active=0, pit_lane_time_ms=0, pit_stop_timer_ms=0, pit_stop_should_serve_pen=0,
            speed_trap_fastest_speed=0.0, speed_trap_fastest_lap=0,
            packet_format=self.packet_format,
        )

    def _participant(self, header: PacketHeader, index: int, driver: DriverSpec) -> ParticipantData:
        return ParticipantData.from_values(
            header, ai_controlled=driver.ai_controlled, driver_id=index, network_id=0,
            team_id=get_team_id_class(self.packet_format).MERCEDES, my_team=False, race_number=index + 1,
            nationality=Nationality.Unspecified, name=driver.name, your_telemetry=driver.telemetry,
            show_online_names=False, platform=Platform.NONE, liveries=_black_liveries())

    def _empty_participant(self, header: PacketHeader) -> ParticipantData:
        return ParticipantData.from_values(
            header, ai_controlled=False, driver_id=0, network_id=0,
            team_id=get_team_id_class(self.packet_format).MERCEDES, my_team=False, race_number=0,
            nationality=Nationality.Unspecified, name="", your_telemetry=TelemetrySetting.RESTRICTED,
            show_online_names=False, platform=Platform.NONE, liveries=_black_liveries())


def _black_liveries() -> List[LiveryColour]:
    # 2025+ always carries four livery colours on the wire
    return [LiveryColour.from_values(0, 0, 0) for _ in range(4)]
