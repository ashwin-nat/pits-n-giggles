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
from typing import Dict, List, Optional, Union

from lib.f1_types import (ActualTyreCompound, CarDamageData, CarMotionData, CarStatusData,
                          CarTelemetry2Data, CarTelemetryData, F1PacketType,
                          FinalClassificationData, LapHistoryData,
                          LiveryColour, Nationality, PacketCarDamageData,
                          PacketCarStatusData, PacketCarTelemetry2Data,
                          PacketCarTelemetryData, PacketEventData,
                          PacketFinalClassificationData, PacketHeader,
                          PacketLapData, PacketMotionData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          PacketTyreSetsData, ParticipantData, Platform,
                          ResultStatus, SessionType23, SessionType24,
                          TelemetrySetting, TrackID, TractionControlAssistMode,
                          TyreSetData, VisualTyreCompound,
                          WeatherForecastSample, get_team_id_class)
from lib.f1_types.common import get_num_cars
from lib.f1_types.packet_2_lap_data import LapData

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

# Sweep with @pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
ALL_FORMATS = [2023, 2024, 2025, 2026]

# The 20 TYRE_SETS entries, by index: the race weekend allocation of 8 soft, 3 medium, 2 hard, 4 inter, 3 wet.
# The C-numbers vary by track in the game; these are one plausible choice.
TYRE_SET_ALLOCATION = (
    [(ActualTyreCompound.C4, VisualTyreCompound.SOFT)] * 8 +
    [(ActualTyreCompound.C3, VisualTyreCompound.MEDIUM)] * 3 +
    [(ActualTyreCompound.C2, VisualTyreCompound.HARD)] * 2 +
    [(ActualTyreCompound.INTER, VisualTyreCompound.INTER)] * 4 +
    [(ActualTyreCompound.WET, VisualTyreCompound.WET)] * 3
)
FIRST_SOFT_IDX, FIRST_MEDIUM_IDX, FIRST_HARD_IDX = 0, 8, 11

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


@dataclass(frozen=True)
class DamageSpec:
    """One CAR_DAMAGE entry. Build with damage()."""
    index: int
    tyre_wear: float


def damage(index: int, tyre_wear: float) -> DamageSpec:
    """A car whose four tyres all carry tyre_wear percent."""
    return DamageSpec(index=index, tyre_wear=tyre_wear)


@dataclass(frozen=True)
class StatusSpec:
    """One CAR_STATUS entry. Build with fuel_and_ers()."""
    index: int
    fuel_in_tank: float
    ers_harvested_mguk: float
    ers_deployed: float


def fuel_and_ers(index: int, *, fuel_in_tank: float = 0.0, ers_harvested_mguk: float = 0.0,
                 ers_deployed: float = 0.0) -> StatusSpec:
    """A car's fuel in kg and its MGU-K harvest and ERS deployment this lap in joules. Unset values are 0."""
    return StatusSpec(index=index, fuel_in_tank=fuel_in_tank, ers_harvested_mguk=ers_harvested_mguk,
                      ers_deployed=ers_deployed)


@dataclass(frozen=True)
class SpeedSpec:
    """One CAR_TELEMETRY entry. Build with speed()."""
    index: int
    kmph: int


def speed(index: int, kmph: int) -> SpeedSpec:
    """A car travelling at kmph."""
    return SpeedSpec(index=index, kmph=kmph)


@dataclass(frozen=True)
class PositionSpec:
    """One MOTION entry. Build with world_position()."""
    index: int
    x: float
    y: float
    z: float
    yaw: float


def world_position(index: int, x: float, y: float, z: float, yaw: float) -> PositionSpec:
    """A car at world position (x, y, z), facing yaw radians."""
    return PositionSpec(index=index, x=x, y=y, z=z, yaw=yaw)

# ------------------------- PACKETS ------------------------------------------------------------------------------------

class Packets:
    """Builds packets for one packet format. Every header takes the next number from a counter starting at 1, as
    both its frame and overall frame, unless the call overrides one of them."""

    def __init__(self, packet_format: int, player_index: int = 0) -> None:
        self.packet_format = packet_format
        self.player_index = player_index
        self._next_frame = 1

    def header(self, packet_type: F1PacketType, session_uid: int,
               frame: Optional[int] = None, overall_frame: Optional[int] = None) -> PacketHeader:
        """A header for packet_type. Frame and overall frame default to the next frame number. Pass frame alone
        for a packet after a flashback: the sim's frame goes back, its overall frame keeps counting up."""
        next_frame = self._next_frame
        self._next_frame += 1
        frame = next_frame if frame is None else frame
        overall_frame = next_frame if overall_frame is None else overall_frame
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
            overall_frame_identifier=overall_frame,
            player_car_index=self.player_index,
            secondary_player_car_index=255,
        )

    def session(self, *, session_uid: int, session_type: str, track: TrackID, total_laps: int,
                track_length: int,
                weather: WeatherForecastSample.WeatherCondition = WeatherForecastSample.WeatherCondition.CLEAR,
                formula: PacketSessionData.FormulaType = PacketSessionData.FormulaType.F1_MODERN,
                is_spectating: bool = False,
                **header_kwargs: Optional[int]) -> PacketSessionData:
        """A SESSION packet. session_type is the enum member name (e.g. "RACE", "SHORT_QUALIFYING",
        "TIME_TRIAL"), resolved per format, since the numeric values differ between SessionType23 and
        SessionType24. weather is the single forecast sample's weather, which the state layer reads as the
        current weather."""
        session_type_enum = self._session_type(session_type)
        forecast = WeatherForecastSample.from_values(
            self.packet_format, session_type_enum, time_offset=0, weather=weather,
            track_temp=0, track_temp_change=WeatherForecastSample.TrackTemperatureChange.NO_CHANGE,
            air_temp=0, air_temp_change=WeatherForecastSample.AirTemperatureChange.NO_CHANGE, rain_percentage=0)
        return PacketSessionData.from_values(
            self.header(F1PacketType.SESSION, session_uid, **header_kwargs),
            session_type_enum, track, total_laps=total_laps, track_length=track_length,
            weather_forecast_samples=[forecast], formula=formula, is_spectating=is_spectating)

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

    def drive(self, index: int, *, lap: int, distances: List[float], session_uid: int,
              status: LapData.DriverStatus = LapData.DriverStatus.ON_TRACK) -> List[PacketLapData]:
        """One LAP_DATA per distance, for car index on lap, frames counting up. Inject them in order."""
        return [self.lap(car(index, lap=lap, lap_distance=distance, status=status), session_uid=session_uid)
                for distance in distances]

    def session_history(self, *, car_idx: int, laps: List[LapHistoryData], session_uid: int,
                        **header_kwargs: Optional[int]) -> PacketSessionHistoryData:
        """A SESSION_HISTORY packet for one car."""
        return PacketSessionHistoryData.from_values(
            self.header(F1PacketType.SESSION_HISTORY, session_uid, **header_kwargs), car_idx, laps)

    def session_history_burst(self, *, laps: List[LapHistoryData], session_uid: int,
                              overall_frame: int) -> List[PacketSessionHistoryData]:
        """One SESSION_HISTORY per car on the grid, all on overall_frame, each carrying laps."""
        return [self.session_history(car_idx=index, laps=laps, session_uid=session_uid, overall_frame=overall_frame)
                for index in range(get_num_cars(self.packet_format))]

    def final_classification(self, *entries: ClassifiedSpec, session_uid: int,
                             **header_kwargs: Optional[int]) -> PacketFinalClassificationData:
        """A FINAL_CLASSIFICATION packet. entries fill car indices 0.. in order, all FINISHED."""
        data = [FinalClassificationData.from_values(self.packet_format, position=entry.position,
                                                    num_laps=entry.num_laps, result_status=ResultStatus.FINISHED)
                for entry in entries]
        return PacketFinalClassificationData.from_values(
            self.header(F1PacketType.FINAL_CLASSIFICATION, session_uid, **header_kwargs), len(data), data)

    def car_damage(self, *cars: DamageSpec, session_uid: int, **header_kwargs: Optional[int]) -> PacketCarDamageData:
        """A CAR_DAMAGE packet. Every car index not in cars is an all-zero entry."""
        by_index: Dict[int, DamageSpec] = {spec.index: spec for spec in cars}
        entries = []
        for index in range(get_num_cars(self.packet_format)):
            wear = by_index[index].tyre_wear if index in by_index else 0.0
            entries.append(CarDamageData.from_values(
                self.packet_format, tyres_wear=[wear] * 4, tyres_damage=[0] * 4, brakes_damage=[0] * 4,
                tyre_blisters=[0] * 4, fl_wing_damage=0, fr_wing_damage=0, rear_wing_damage=0, floor_damage=0,
                diffuser_damage=0, sidepod_damage=0, drs_fault=False, ers_fault=False, gear_box_damage=0,
                engine_damage=0, engine_mguh_wear=0, engine_es_wear=0, engine_ce_wear=0, engine_ice_wear=0,
                engine_mguk_wear=0, engine_tc_wear=0, engine_blown=False, engine_seized=False))
        return PacketCarDamageData.from_values(
            self.header(F1PacketType.CAR_DAMAGE, session_uid, **header_kwargs), entries)

    def tyre_sets(self, *, car_idx: int, fitted_idx: int, session_uid: int,
                  **header_kwargs: Optional[int]) -> PacketTyreSetsData:
        """A TYRE_SETS packet for one car, with the TYRE_SET_ALLOCATION sets. Everything but the compounds and
        the fitted flag is zero."""
        sets = [TyreSetData.from_values(
            self.packet_format, actual_tyre_compound=actual, visual_tyre_compound=visual, wear=0, available=True,
            recommended_session=self._session_type("RACE"), life_span=0, usable_life=0, lap_delta_time=0,
            fitted=index == fitted_idx) for index, (actual, visual) in enumerate(TYRE_SET_ALLOCATION)]
        return PacketTyreSetsData.from_values(
            self.header(F1PacketType.TYRE_SETS, session_uid, **header_kwargs), car_idx, sets, fitted_idx)

    def car_status(self, *cars: StatusSpec, session_uid: int, **header_kwargs: Optional[int]) -> PacketCarStatusData:
        """A CAR_STATUS packet. Every car is on C3 / MEDIUM. Fuel and ERS come from cars, and are zero for any
        car index not in cars, as is everything else."""
        by_index: Dict[int, StatusSpec] = {spec.index: spec for spec in cars}
        entries = [self._car_status(by_index.get(index, fuel_and_ers(index)))
                   for index in range(get_num_cars(self.packet_format))]
        return PacketCarStatusData.from_values(
            self.header(F1PacketType.CAR_STATUS, session_uid, **header_kwargs), entries)

    def car_telemetry(self, *cars: SpeedSpec, session_uid: int,
                      **header_kwargs: Optional[int]) -> PacketCarTelemetryData:
        """A CAR_TELEMETRY packet. Speed comes from cars. Every other field, and every car index not in cars, is
        zero. MFD panels are closed (255)."""
        by_index: Dict[int, SpeedSpec] = {spec.index: spec for spec in cars}
        entries = [CarTelemetryData.from_values(by_index[index].kmph if index in by_index else 0, *([0] * 30),
                                                packet_format=self.packet_format)
                   for index in range(get_num_cars(self.packet_format))]
        return PacketCarTelemetryData.from_values(
            self.header(F1PacketType.CAR_TELEMETRY, session_uid, **header_kwargs),
            entries, mfd_panel_index=255, mfd_panel_index_secondary_player=255, suggested_gear=0)

    def motion(self, *cars: PositionSpec, session_uid: int, **header_kwargs: Optional[int]) -> PacketMotionData:
        """A MOTION packet. World position and yaw come from cars. Every other field, and every car index not in
        cars, is zero."""
        by_index: Dict[int, PositionSpec] = {spec.index: spec for spec in cars}
        entries = []
        for index in range(get_num_cars(self.packet_format)):
            spec = by_index.get(index, PositionSpec(index=index, x=0.0, y=0.0, z=0.0, yaw=0.0))
            entries.append(CarMotionData.from_values(
                spec.x, spec.y, spec.z, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, spec.yaw, 0.0, 0.0,
                packet_format=self.packet_format))
        return PacketMotionData.from_values(self.header(F1PacketType.MOTION, session_uid, **header_kwargs), entries)

    def car_telemetry_2(self, *, session_uid: int, **header_kwargs: Optional[int]) -> PacketCarTelemetry2Data:
        """A CAR_TELEMETRY_2 packet (2026 only) with an all-zero entry for every car."""
        entry = CarTelemetry2Data.from_values(
            active_aero_mode=CarTelemetry2Data.ActiveAeroMode.CORNER_MODE, active_aero_available=False,
            active_aero_activation_distance=0, overtake_available=False, overtake_active=False,
            overtake_activation_distance=0, regulations_2026=False, driving_wrong_way=False)
        return PacketCarTelemetry2Data.from_values(
            self.header(F1PacketType.CAR_TELEMETRY_2, session_uid, **header_kwargs),
            [entry] * get_num_cars(self.packet_format))

    def event(self, event_type: PacketEventData.EventPacketType, details: Optional[object], *,
              session_uid: int, **header_kwargs: Optional[int]) -> PacketEventData:
        """An EVENT packet. Build details with the event type's own from_values."""
        return PacketEventData.from_values(
            self.header(F1PacketType.EVENT, session_uid, **header_kwargs), event_type, details)

    def _car_status(self, spec: StatusSpec) -> CarStatusData:
        return CarStatusData.from_values(
            traction_control=TractionControlAssistMode.OFF, anti_lock_brakes=False,
            fuel_mix=CarStatusData.FuelMix.LEAN, front_brake_bias=0, pit_limiter_status=False,
            fuel_in_tank=spec.fuel_in_tank, fuel_capacity=0.0, fuel_remaining_laps=0.0, max_rpm=0, idle_rpm=0,
            max_gears=0, drs_allowed=0, drs_activation_distance=0, actual_tyre_compound=ActualTyreCompound.C3,
            visual_tyre_compound=VisualTyreCompound.MEDIUM, tyres_age_laps=0,
            m_vehicle_fia_flags=CarStatusData.VehicleFIAFlags.NONE, engine_power_ice=0.0, engine_power_mguk=0.0,
            ers_store_energy=0.0, ers_deploy_mode=CarStatusData.ERSDeployMode.NONE,
            ers_harvested_this_lap_mguk=spec.ers_harvested_mguk, ers_harvested_this_lap_mguh=0.0,
            ers_deployed_this_lap=spec.ers_deployed, network_paused=0, packet_format=self.packet_format)

    def _session_type(self, name: str) -> Union[SessionType23, SessionType24]:
        return (SessionType23 if self.packet_format == 2023 else SessionType24)[name]

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
            show_online_names=True, platform=Platform.NONE, liveries=_black_liveries())

    def _empty_participant(self, header: PacketHeader) -> ParticipantData:
        return ParticipantData.from_values(
            header, ai_controlled=False, driver_id=0, network_id=0,
            team_id=get_team_id_class(self.packet_format).MERCEDES, my_team=False, race_number=0,
            nationality=Nationality.Unspecified, name="", your_telemetry=TelemetrySetting.RESTRICTED,
            show_online_names=False, platform=Platform.NONE, liveries=_black_liveries())


def _black_liveries() -> List[LiveryColour]:
    # 2025+ always carries four livery colours on the wire
    return [LiveryColour.from_values(0, 0, 0) for _ in range(4)]
