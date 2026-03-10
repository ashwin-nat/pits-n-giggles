use f1_types::{
    CarStatusData, EventDetails, EventPacketType, F1Packet, PacketCarDamageData,
    PacketCarSetupData, PacketCarStatusData, PacketCarTelemetryData, PacketEventData,
    PacketFinalClassificationData, PacketLapData, PacketLapPositionsData, PacketMotionData,
    PacketParticipantsData, PacketSessionData, PacketSessionHistoryData, PacketTimeTrialData,
    PacketTyreSetsData, PitStatus, ResultStatus,
};
use serde::Serialize;
use serde_json::{Map, Value, json};

use crate::api::team_label;
use crate::models::{
    CustomMarkerEntry, DriverState, FuelSample, LapTyreWearSample, OvertakeRecordState,
    PerLapSnapshotState, SessionEventsState, SessionInfoState, TimeTrialState,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum TyreDeltaType {
    Slick,
    Wet,
    Intermediate,
}

impl TyreDeltaType {
    fn label(self) -> &'static str {
        match self {
            Self::Slick => "Slick",
            Self::Wet => "Wet",
            Self::Intermediate => "Intermediate",
        }
    }
}

fn sector_label(sector: f1_types::Sector) -> String {
    match sector {
        f1_types::Sector::Sector1 => "SECTOR1".to_string(),
        f1_types::Sector::Sector2 => "SECTOR2".to_string(),
        f1_types::Sector::Sector3 => "SECTOR3".to_string(),
        f1_types::Sector::Unknown(value) => value.to_string(),
    }
}

fn format_marker_time_ms(ms: u32) -> String {
    let minutes = ms / 60_000;
    let seconds = (ms % 60_000) / 1_000;
    let millis = ms % 1_000;
    format!("{minutes}:{seconds:02}.{millis:03}")
}

fn format_percentage(value: f32) -> String {
    format!("{value:.2}")
}

fn tyre_delta_type(compound: f1_types::VisualTyreCompound) -> TyreDeltaType {
    match compound {
        f1_types::VisualTyreCompound::Wet | f1_types::VisualTyreCompound::WetF2 => {
            TyreDeltaType::Wet
        }
        f1_types::VisualTyreCompound::Inter => TyreDeltaType::Intermediate,
        _ => TyreDeltaType::Slick,
    }
}

fn find_tyre_delta_candidate(
    tyre_sets: &PacketTyreSetsData,
    reverse: bool,
    matcher: impl Fn(f1_types::VisualTyreCompound) -> bool,
) -> Option<(usize, &f1_types::TyreSetData)> {
    if reverse {
        tyre_sets
            .tyre_set_data
            .iter()
            .enumerate()
            .rev()
            .find(|(_, tyre_set)| matcher(tyre_set.visual_tyre_compound))
    } else {
        tyre_sets
            .tyre_set_data
            .iter()
            .enumerate()
            .find(|(_, tyre_set)| matcher(tyre_set.visual_tyre_compound))
    }
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct SessionState {
    pub packet_count: u64,
    pub player_index: Option<u8>,
    pub fastest_index: Option<u8>,
    pub num_active_cars: Option<u8>,
    pub num_dnf_cars: Option<u8>,
    pub race_completed: bool,
    pub is_player_dnf: bool,
    pub connected_to_sim: bool,
    pub flashback_occurred: bool,
    pub drivers: Vec<DriverState>,
    pub session_info: SessionInfoState,
    pub last_lap_positions: Option<PacketLapPositionsData>,
    pub time_trial: TimeTrialState,
    pub events: SessionEventsState,
}

impl Default for SessionState {
    fn default() -> Self {
        Self::new()
    }
}

impl SessionState {
    pub const MAX_DRIVERS: usize = 22;

    pub fn new() -> Self {
        Self {
            packet_count: 0,
            player_index: None,
            fastest_index: None,
            num_active_cars: None,
            num_dnf_cars: None,
            race_completed: false,
            is_player_dnf: false,
            connected_to_sim: false,
            flashback_occurred: false,
            drivers: (0..Self::MAX_DRIVERS).map(DriverState::new).collect(),
            session_info: SessionInfoState::default(),
            last_lap_positions: None,
            time_trial: TimeTrialState::default(),
            events: SessionEventsState::default(),
        }
    }

    pub fn clear(&mut self) {
        *self = Self::new();
    }

    pub fn set_connected_to_sim(&mut self, connected: bool) {
        self.connected_to_sim = connected;
    }

    pub fn is_data_available(&self) -> bool {
        self.session_info.packet_session.is_some()
            && self.num_active_cars.unwrap_or(0) > 0
            && self.drivers.iter().any(DriverState::is_valid)
    }

    pub fn driver(&self, index: usize) -> Option<&DriverState> {
        self.drivers.get(index)
    }

    pub fn driver_mut(&mut self, index: usize) -> Option<&mut DriverState> {
        self.drivers.get_mut(index)
    }

    pub fn apply_packet(&mut self, packet: F1Packet) {
        match packet {
            F1Packet::Session(packet) => self.apply_session(packet),
            F1Packet::Participants(packet) => self.apply_participants(packet),
            F1Packet::LapData(packet) => self.apply_lap_data(packet),
            F1Packet::Event(packet) => self.apply_event(packet),
            F1Packet::CarTelemetry(packet) => self.apply_car_telemetry(packet),
            F1Packet::CarStatus(packet) => self.apply_car_status(packet),
            F1Packet::CarDamage(packet) => self.apply_car_damage(packet),
            F1Packet::Motion(packet) => self.apply_motion(packet),
            F1Packet::CarSetups(packet) => self.apply_car_setups(packet),
            F1Packet::SessionHistory(packet) => self.apply_session_history(packet),
            F1Packet::TyreSets(packet) => self.apply_tyre_sets(packet),
            F1Packet::FinalClassification(packet) => self.apply_final_classification(packet),
            F1Packet::TimeTrial(packet) => self.apply_time_trial(packet),
            F1Packet::LapPositions(packet) => self.apply_lap_positions(packet),
            F1Packet::LobbyInfo(_) | F1Packet::MotionEx(_) => {}
        }
        self.packet_count += 1;
    }

    pub fn insert_custom_marker(&mut self) -> Option<CustomMarkerEntry> {
        let player_index = usize::from(self.player_index?);
        let driver = self.driver(player_index)?;
        let lap_data = driver.packet_copies.lap_data.as_ref()?;
        let track_id_raw = self.session_info.track_id_raw?;
        let packet_format = self.session_info.packet_format?;
        let session_type_raw = self.session_info.session_type_raw?;
        let track_length = f32::from(self.session_info.track_length?);
        if track_length <= 0.0 {
            return None;
        }

        let event_type = if packet_format == 2023 {
            f1_types::SessionType23::try_from(session_type_raw)
                .map(|value| value.to_string())
                .unwrap_or_else(|_| session_type_raw.to_string())
        } else {
            f1_types::SessionType24::try_from(session_type_raw)
                .map(|value| value.to_string())
                .unwrap_or_else(|_| session_type_raw.to_string())
        };
        let curr_lap_percentage = format!(
            "{}%",
            format_percentage((lap_data.lap_distance / track_length) * 100.0)
        );
        let marker = CustomMarkerEntry {
            track: crate::api::track_label(track_id_raw),
            event_type,
            lap: lap_data.current_lap_num.to_string(),
            sector: sector_label(lap_data.sector),
            curr_lap_time: format_marker_time_ms(lap_data.current_lap_time_in_ms),
            curr_lap_percentage,
        };
        self.events.custom_markers.push(marker.clone());
        Some(marker)
    }

    pub fn tyre_delta_notification_json(&self) -> Option<Value> {
        if self.session_info.is_spectating.unwrap_or(false)
            || self.session_info.packet_final_classification.is_some()
            || self.is_player_dnf
        {
            return None;
        }

        let packet_format = self.session_info.packet_format?;
        let session_type_raw = self.session_info.session_type_raw?;
        let is_time_trial = if packet_format == 2023 {
            matches!(
                f1_types::SessionType23::try_from(session_type_raw).ok(),
                Some(f1_types::SessionType23::TIME_TRIAL)
            )
        } else {
            matches!(
                f1_types::SessionType24::try_from(session_type_raw).ok(),
                Some(f1_types::SessionType24::TIME_TRIAL)
            )
        };
        if is_time_trial {
            return None;
        }

        let player_index = usize::from(self.player_index?);
        let tyre_sets = self
            .driver(player_index)?
            .packet_copies
            .tyre_sets
            .as_ref()?;
        let fitted_tyre = tyre_sets.fitted_tyre_set()?;
        let current_type = tyre_delta_type(fitted_tyre.visual_tyre_compound);

        let is_wet = |compound| tyre_delta_type(compound) == TyreDeltaType::Wet;
        let is_inter = |compound| tyre_delta_type(compound) == TyreDeltaType::Intermediate;
        let is_slick = |compound| tyre_delta_type(compound) == TyreDeltaType::Slick;

        let ((first_index, first_tyre, first_type), (second_index, second_tyre, second_type)) =
            match current_type {
                TyreDeltaType::Slick => (
                    (
                        find_tyre_delta_candidate(tyre_sets, true, is_wet)?.0,
                        find_tyre_delta_candidate(tyre_sets, true, is_wet)?.1,
                        TyreDeltaType::Wet,
                    ),
                    (
                        find_tyre_delta_candidate(tyre_sets, true, is_inter)?.0,
                        find_tyre_delta_candidate(tyre_sets, true, is_inter)?.1,
                        TyreDeltaType::Intermediate,
                    ),
                ),
                TyreDeltaType::Intermediate => (
                    (
                        find_tyre_delta_candidate(tyre_sets, true, is_wet)?.0,
                        find_tyre_delta_candidate(tyre_sets, true, is_wet)?.1,
                        TyreDeltaType::Wet,
                    ),
                    (
                        find_tyre_delta_candidate(tyre_sets, false, is_slick)?.0,
                        find_tyre_delta_candidate(tyre_sets, false, is_slick)?.1,
                        TyreDeltaType::Slick,
                    ),
                ),
                TyreDeltaType::Wet => (
                    (
                        find_tyre_delta_candidate(tyre_sets, false, is_slick)?.0,
                        find_tyre_delta_candidate(tyre_sets, false, is_slick)?.1,
                        TyreDeltaType::Slick,
                    ),
                    (
                        find_tyre_delta_candidate(tyre_sets, false, is_inter)?.0,
                        find_tyre_delta_candidate(tyre_sets, false, is_inter)?.1,
                        TyreDeltaType::Intermediate,
                    ),
                ),
            };

        if first_index == second_index || first_type == second_type {
            return None;
        }

        let current_label = current_type.label();
        Some(json!({
            "curr-tyre-type": current_label,
            "tyre-delta-messages": [
                {
                    "curr-tyre-type": current_label,
                    "other-tyre-type": first_type.label(),
                    "tyre-delta": f64::from(first_tyre.lap_delta_time) / 1000.0,
                },
                {
                    "curr-tyre-type": current_label,
                    "other-tyre-type": second_type.label(),
                    "tyre-delta": f64::from(second_tyre.lap_delta_time) / 1000.0,
                }
            ]
        }))
    }

    fn apply_session(&mut self, packet: PacketSessionData) {
        let is_new_session = self
            .session_info
            .session_uid
            .is_some_and(|session_uid| session_uid != packet.header.session_uid);
        if is_new_session {
            self.clear();
        }

        self.session_info.session_uid = Some(packet.header.session_uid);
        self.session_info.packet_format = Some(packet.header.packet_format);
        self.session_info.game_year = Some(packet.header.game_year);
        let safety_car_status_raw = packet.safety_car_status_raw;
        let should_clear_pole_lap = self.session_info.track_id_raw != Some(packet.track_id_raw)
            || self.session_info.formula_raw != Some(packet.formula_raw)
            || self.session_info.session_type_raw != Some(packet.session_type_raw);
        self.session_info.total_laps = Some(packet.total_laps);
        self.session_info.track_length = Some(packet.track_length);
        self.session_info.session_type_raw = Some(packet.session_type_raw);
        self.session_info.track_id_raw = Some(packet.track_id_raw);
        self.session_info.formula_raw = Some(packet.formula_raw);
        self.session_info.session_time_left = Some(packet.session_time_left);
        self.session_info.session_duration = Some(packet.session_duration);
        self.session_info.pit_speed_limit = Some(packet.pit_speed_limit);
        self.session_info.is_spectating = Some(packet.is_spectating);
        self.session_info.spectator_car_index = if packet.spectator_car_index == u8::MAX {
            None
        } else {
            Some(packet.spectator_car_index)
        };
        self.session_info.safety_car_status_raw = Some(packet.safety_car_status_raw);
        self.session_info.weather_forecast_samples = packet.weather_forecast_samples.clone();
        self.session_info.packet_session = Some(packet);
        if should_clear_pole_lap {
            self.session_info.most_recent_pole_lap = None;
        }
        for driver in &mut self.drivers {
            driver.current_lap_max_safety_car_status_raw = Some(
                driver
                    .current_lap_max_safety_car_status_raw
                    .map_or(safety_car_status_raw, |current| {
                        current.max(safety_car_status_raw)
                    }),
            );
        }
        self.race_completed = false;
    }

    fn apply_participants(&mut self, packet: PacketParticipantsData) {
        let player_index = if packet.header.player_car_index == u8::MAX {
            None
        } else {
            Some(packet.header.player_car_index)
        };
        self.player_index = player_index;
        self.num_active_cars = Some(packet.num_active_cars);

        for (index, participant) in packet.participants.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                driver.driver_info.name =
                    (!participant.name.is_empty()).then_some(participant.name.clone());
                driver.driver_info.team_id_raw = Some(participant.team_id_raw);
                driver.driver_info.driver_number = Some(participant.race_number);
                driver.driver_info.telemetry_setting_raw = Some(participant.your_telemetry_raw);
                driver.driver_info.is_player = player_index == Some(index as u8);
                driver.packet_copies.participant_data = Some(participant);
            }
        }
    }

    fn apply_lap_data(&mut self, packet: PacketLapData) {
        let mut active_cars = 0u8;
        let mut dnf_cars = 0u8;
        let player_index = self.player_index;
        let track_length = self.session_info.track_length;
        let safety_car_status_raw = self.session_info.safety_car_status_raw;
        let is_time_trial_session = self.is_time_trial_session();
        let flashback_occurred = self.flashback_occurred;

        for (index, lap_data) in packet.lap_data.iter().cloned().enumerate() {
            let previous_lap_data = self
                .driver(index)
                .and_then(|driver| driver.packet_copies.lap_data.clone());
            let lap_changed = previous_lap_data
                .as_ref()
                .is_some_and(|previous| previous.current_lap_num != lap_data.current_lap_num);
            if self.flashback_occurred {
                self.prune_driver_samples_from_lap(index, lap_data.current_lap_num);
            }
            if let Some(previous) = previous_lap_data.as_ref() {
                if lap_data.current_lap_num > previous.current_lap_num {
                    self.capture_completed_lap_samples(index, previous.current_lap_num);
                } else if lap_data.current_lap_num < previous.current_lap_num {
                    self.prune_driver_samples_from_lap(index, lap_data.current_lap_num);
                }
            }
            let driver_info_brief = self.driver_info_brief_json(index as u8);
            let mut warning_updates = Vec::new();
            let mut race_control_updates = Vec::new();

            if let Some(driver) = self.driver_mut(index) {
                driver.driver_info.position = Some(lap_data.car_position);
                driver.driver_info.grid_position = Some(lap_data.grid_position);

                driver.lap_info.last_lap_time_in_ms = Some(lap_data.last_lap_time_in_ms);
                driver.lap_info.current_lap_time_in_ms = Some(lap_data.current_lap_time_in_ms);
                driver.lap_info.current_lap_sector1_time_in_ms = Some(lap_data.sector1_time_in_ms);
                driver.lap_info.current_lap_sector2_time_in_ms = Some(lap_data.sector2_time_in_ms);
                driver.lap_info.current_lap_sector3_time_in_ms = None;
                driver.lap_info.current_lap = Some(lap_data.current_lap_num);
                driver.lap_info.delta_to_car_in_front_ms = Some(
                    u32::from(lap_data.delta_to_car_in_front_in_ms)
                        + (u32::from(lap_data.delta_to_car_in_front_minutes) * 60_000),
                );
                driver.lap_info.delta_to_leader_ms = Some(
                    u32::from(lap_data.delta_to_race_leader_in_ms)
                        + (u32::from(lap_data.delta_to_race_leader_minutes) * 60_000),
                );
                driver.lap_info.lap_distance = Some(lap_data.lap_distance);
                driver.lap_info.total_distance = Some(lap_data.total_distance);
                driver.lap_info.safety_car_delta = Some(lap_data.safety_car_delta);
                driver.lap_info.current_sector = Some(sector_label(lap_data.sector));
                driver.lap_info.current_lap_invalid = Some(lap_data.current_lap_invalid);
                driver.lap_info.current_driver_status = Some(lap_data.driver_status.to_string());
                driver.lap_info.result_status = Some(lap_data.result_status);
                driver.lap_info.speed_trap_fastest_speed = Some(lap_data.speed_trap_fastest_speed);
                driver.lap_info.penalties = Some(lap_data.penalties);
                driver.lap_info.total_warnings = Some(lap_data.total_warnings);
                driver.lap_info.corner_cutting_warnings = Some(lap_data.corner_cutting_warnings);
                driver.lap_info.num_unserved_drive_through_pens =
                    Some(lap_data.num_unserved_drive_through_pens);
                driver.lap_info.num_unserved_stop_go_pens =
                    Some(lap_data.num_unserved_stop_go_pens);
                driver.lap_info.is_pitting =
                    Some(!matches!(lap_data.pit_status, f1_types::PitStatus::None));

                driver.pit_info.pit_status = Some(lap_data.pit_status.to_string());
                driver.pit_info.num_stops = Some(lap_data.num_pit_stops);
                driver.pit_info.pit_lane_timer_active = Some(lap_data.pit_lane_timer_active);
                driver.pit_info.pit_lane_time_in_lane_ms =
                    Some(lap_data.pit_lane_time_in_lane_in_ms);
                driver.pit_info.pit_stop_timer_ms = Some(lap_data.pit_stop_timer_in_ms);
                driver.pit_info.pit_stop_should_serve_pen =
                    Some(lap_data.pit_stop_should_serve_pen);
                if lap_changed {
                    driver.current_lap_max_safety_car_status_raw = safety_car_status_raw;
                }
                if !is_time_trial_session {
                    if flashback_occurred {
                        driver
                            .delta_manager
                            .handle_flashback(lap_data.current_lap_num, lap_data.lap_distance);
                    }
                    driver.delta_manager.record_data_point(
                        lap_data.current_lap_num,
                        lap_data.lap_distance,
                        lap_data.current_lap_time_in_ms,
                    );
                    driver.lap_info.current_lap_delta_ms =
                        driver.delta_manager.get_delta().map(|delta| delta.delta_ms);
                }

                driver.packet_copies.lap_data = Some(lap_data.clone());

                if let Some(previous) = previous_lap_data.as_ref() {
                    let lap_progress_percent = track_length
                        .filter(|track_length| *track_length > 0)
                        .map(|track_length| {
                            (lap_data.lap_distance / f32::from(track_length)) * 100.0
                        });
                    let sector_number = Some(match lap_data.sector {
                        f1_types::Sector::Sector1 => 1,
                        f1_types::Sector::Sector2 => 2,
                        f1_types::Sector::Sector3 => 3,
                        f1_types::Sector::Unknown(value) => value.saturating_add(1),
                    });

                    let mut push_warning_update =
                        |entry_type: &str, old_value: u32, new_value: u32| {
                            if old_value != new_value {
                                warning_updates.push(json!({
                                    "lap-number": lap_data.current_lap_num,
                                    "sector-number": sector_number,
                                    "lap-progress-percent": lap_progress_percent,
                                    "entry-type": entry_type,
                                    "old-value": old_value,
                                    "new-value": new_value,
                                }));
                            }
                        };

                    push_warning_update(
                        "time-penalties",
                        u32::from(previous.penalties),
                        u32::from(lap_data.penalties),
                    );
                    push_warning_update(
                        "total-warnings",
                        u32::from(previous.total_warnings),
                        u32::from(lap_data.total_warnings),
                    );
                    push_warning_update(
                        "corner-cutting-warnings",
                        u32::from(previous.corner_cutting_warnings),
                        u32::from(lap_data.corner_cutting_warnings),
                    );
                    push_warning_update(
                        "num-dt",
                        u32::from(previous.num_unserved_drive_through_pens),
                        u32::from(lap_data.num_unserved_drive_through_pens),
                    );
                    push_warning_update(
                        "num-sg",
                        u32::from(previous.num_unserved_stop_go_pens),
                        u32::from(lap_data.num_unserved_stop_go_pens),
                    );

                    if matches!(previous.pit_status, PitStatus::None)
                        && !matches!(lap_data.pit_status, PitStatus::None)
                    {
                        race_control_updates.push(json!({
                            "message-type": "PITTING",
                            "lap-number": lap_data.current_lap_num,
                            "driver-info": driver_info_brief.clone(),
                        }));
                    }
                }

                if !matches!(
                    lap_data.result_status,
                    ResultStatus::INVALID | ResultStatus::INACTIVE
                ) {
                    active_cars += 1;
                }
                if matches!(
                    lap_data.result_status,
                    ResultStatus::DID_NOT_FINISH
                        | ResultStatus::DISQUALIFIED
                        | ResultStatus::RETIRED
                ) {
                    dnf_cars += 1;
                    driver.driver_info.dnf_status_code = Some(match lap_data.result_status {
                        ResultStatus::DISQUALIFIED => "DSQ".to_string(),
                        _ => "DNF".to_string(),
                    });
                }

                if player_index == Some(index as u8) && driver.driver_info.dnf_status_code.is_some()
                {
                    self.is_player_dnf = true;
                }
            }

            if let Some(driver) = self.driver_mut(index) {
                driver.warning_penalty_history.extend(warning_updates);
            }
            for message in race_control_updates {
                self.push_race_control_message_value(message);
            }
        }

        self.num_active_cars = Some(active_cars);
        self.num_dnf_cars = Some(dnf_cars);
        self.flashback_occurred = false;
    }

    fn apply_event(&mut self, packet: PacketEventData) {
        let event_code = packet.event_code;
        self.events.last_event = Some(packet.clone());

        if let Some(details) = packet.event_details {
            match details {
                EventDetails::FastestLap {
                    vehicle_idx,
                    lap_time,
                } => {
                    if let Some(driver) = self.driver_mut(vehicle_idx as usize) {
                        driver.lap_info.best_lap_time_in_ms = Some((lap_time * 1000.0) as u32);
                        driver.lap_info.best_lap_visual_tyre_compound =
                            driver.tyre_info.visual_compound;
                    }
                    self.fastest_index = Some(vehicle_idx);
                    self.push_race_control_message(
                        "FASTEST_LAP",
                        self.driver(vehicle_idx as usize)
                            .and_then(|driver| driver.lap_info.current_lap),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                            "lap-time-ms": (lap_time * 1000.0) as u32,
                        }),
                    );
                }
                EventDetails::Retirement { vehicle_idx, .. } => {
                    if let Some(driver) = self.driver_mut(vehicle_idx as usize) {
                        driver.driver_info.dnf_status_code = Some("DNF".to_string());
                        driver.lap_info.result_status = Some(ResultStatus::RETIRED);
                    }
                    if self.player_index == Some(vehicle_idx) {
                        self.is_player_dnf = true;
                    }
                    self.recompute_dnf_count();
                    self.push_race_control_message(
                        "RETIREMENT",
                        self.driver(vehicle_idx as usize)
                            .and_then(|driver| driver.lap_info.current_lap),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                        }),
                    );
                }
                EventDetails::RaceWinner { vehicle_idx } => {
                    self.events.race_winner_index = Some(vehicle_idx);
                    self.race_completed = true;
                    self.push_race_control_message(
                        "RACE_WINNER",
                        self.current_leader_lap_number(),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                        }),
                    );
                }
                EventDetails::Penalty {
                    penalty_type,
                    infringement_type,
                    vehicle_idx,
                    other_vehicle_idx,
                    lap_num,
                    ..
                } => {
                    self.push_race_control_message(
                        "PENALTY",
                        Some(lap_num),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                            "penalty-type": penalty_type.to_string(),
                            "infringement-type": infringement_type.to_string(),
                            "other-driver-info": self.driver_info_brief_json(other_vehicle_idx),
                        }),
                    );
                }
                EventDetails::SpeedTrap {
                    vehicle_idx, speed, ..
                } => {
                    self.push_race_control_message(
                        "SPEED_TRAP_RECORD",
                        self.driver(vehicle_idx as usize)
                            .and_then(|driver| driver.lap_info.current_lap),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                            "speed": speed,
                        }),
                    );
                }
                EventDetails::StartLights { num_lights } => {
                    self.push_race_control_message(
                        "START_LIGHTS",
                        self.current_leader_lap_number(),
                        json!({
                            "num-lights": num_lights,
                        }),
                    );
                }
                EventDetails::DriveThroughServed { vehicle_idx } => {
                    self.push_race_control_message(
                        "DRIVE_THROUGH_SERVED",
                        self.driver(vehicle_idx as usize)
                            .and_then(|driver| driver.lap_info.current_lap),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                        }),
                    );
                }
                EventDetails::StopGoServed {
                    vehicle_idx,
                    stop_time,
                } => {
                    self.push_race_control_message(
                        "STOP_GO_SERVED",
                        self.driver(vehicle_idx as usize)
                            .and_then(|driver| driver.lap_info.current_lap),
                        json!({
                            "driver-info": self.driver_info_brief_json(vehicle_idx),
                            "stop-time": stop_time,
                        }),
                    );
                }
                EventDetails::Flashback { .. } => {
                    self.flashback_occurred = true;
                    self.push_race_control_message(
                        "FLASHBACK",
                        self.current_leader_lap_number(),
                        json!({}),
                    );
                }
                EventDetails::Collision {
                    vehicle_1_index,
                    vehicle_2_index,
                } => {
                    self.events
                        .collisions
                        .push((vehicle_1_index, vehicle_2_index));
                    self.push_race_control_message(
                        "COLLISION",
                        self.current_leader_lap_number(),
                        json!({
                            "driver-1-info": self.driver_info_brief_json(vehicle_1_index),
                            "driver-2-info": self.driver_info_brief_json(vehicle_2_index),
                        }),
                    );
                }
                EventDetails::Overtake {
                    overtaking_vehicle_idx,
                    being_overtaken_vehicle_idx,
                } => {
                    let overtaking_lap = self
                        .driver(overtaking_vehicle_idx as usize)
                        .and_then(|driver| driver.lap_info.current_lap);
                    let overtaken_lap = self
                        .driver(being_overtaken_vehicle_idx as usize)
                        .and_then(|driver| driver.lap_info.current_lap);
                    self.events.overtakes.push(OvertakeRecordState {
                        overtaking_vehicle_index: overtaking_vehicle_idx,
                        overtaking_lap,
                        overtaken_vehicle_index: being_overtaken_vehicle_idx,
                        overtaken_lap,
                    });
                    self.push_race_control_message(
                        "OVERTAKE",
                        self.current_leader_lap_number(),
                        json!({
                            "overtaker-info": self.driver_info_brief_json(overtaking_vehicle_idx),
                            "overtaken-info": self.driver_info_brief_json(being_overtaken_vehicle_idx),
                        }),
                    );
                }
                EventDetails::SafetyCar {
                    safety_car_type,
                    event_type,
                } => {
                    self.push_race_control_message(
                        "SAFETY_CAR",
                        self.current_leader_lap_number(),
                        json!({
                            "sc-type": safety_car_type.to_string(),
                            "event-type": event_type.to_string(),
                        }),
                    );
                }
                _ => {}
            }
        }

        match event_code {
            EventPacketType::SessionStarted => {
                self.push_race_control_message(
                    "SESSION_START",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            EventPacketType::SessionEnded => {
                self.push_race_control_message(
                    "SESSION_END",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            EventPacketType::DrsEnabled => {
                self.push_race_control_message(
                    "DRS_ENABLED",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            EventPacketType::DrsDisabled => {
                self.push_race_control_message(
                    "DRS_DISABLED",
                    self.current_leader_lap_number(),
                    json!({"reason": "Unknown"}),
                );
            }
            EventPacketType::ChequeredFlag => {
                self.push_race_control_message(
                    "CHEQUERED_FLAG",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            EventPacketType::LightsOut => {
                self.push_race_control_message(
                    "LIGHTS_OUT",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            EventPacketType::RedFlag => {
                self.push_race_control_message(
                    "RED_FLAG",
                    self.current_leader_lap_number(),
                    json!({}),
                );
            }
            _ => {}
        }
    }

    fn apply_car_telemetry(&mut self, packet: PacketCarTelemetryData) {
        for (index, telemetry) in packet.car_telemetry_data.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                driver.car_info.drs_activated = Some(telemetry.drs);
                driver.tyre_info.average_inner_temperature = Some(
                    telemetry
                        .tyres_inner_temperature
                        .iter()
                        .map(|value| *value as f32)
                        .sum::<f32>()
                        / 4.0,
                );
                driver.tyre_info.average_surface_temperature = Some(
                    telemetry
                        .tyres_surface_temperature
                        .iter()
                        .map(|value| *value as f32)
                        .sum::<f32>()
                        / 4.0,
                );
                driver.lap_info.top_speed_kph_this_lap = Some(
                    driver
                        .lap_info
                        .top_speed_kph_this_lap
                        .map_or(telemetry.speed, |current| current.max(telemetry.speed)),
                );
                driver.lap_info.top_speed_kph_overall =
                    driver.lap_info.top_speed_kph_this_lap.map(|speed| {
                        driver
                            .lap_info
                            .top_speed_kph_overall
                            .map_or(speed, |current| current.max(speed))
                    });
                driver.packet_copies.car_telemetry = Some(telemetry);
            }
        }
    }

    fn apply_car_status(&mut self, packet: PacketCarStatusData) {
        for (index, status) in packet.car_status_data.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                driver.car_info.ers_percent =
                    Some((status.ers_store_energy / CarStatusData::MAX_ERS_STORE_ENERGY) * 100.0);
                driver.tyre_info.tyre_age_laps = Some(status.tyres_age_laps);
                driver.tyre_info.visual_compound = Some(status.visual_tyre_compound);
                driver.tyre_info.actual_compound = Some(status.actual_tyre_compound);
                driver.car_info.drs_allowed = Some(status.drs_allowed != 0);
                driver.car_info.drs_distance = Some(status.drs_activation_distance);
                driver.car_info.current_lap_ers_deployed_j = Some(
                    driver
                        .car_info
                        .current_lap_ers_deployed_j
                        .map_or(status.ers_deployed_this_lap, |current| {
                            current.max(status.ers_deployed_this_lap)
                        }),
                );
                driver.car_info.current_lap_ers_harvested_mguk_j = Some(
                    driver
                        .car_info
                        .current_lap_ers_harvested_mguk_j
                        .map_or(status.ers_harvested_this_lap_mguk, |current| {
                            current.max(status.ers_harvested_this_lap_mguk)
                        }),
                );
                driver.car_info.current_lap_ers_harvested_mguh_j = Some(
                    driver
                        .car_info
                        .current_lap_ers_harvested_mguh_j
                        .map_or(status.ers_harvested_this_lap_mguh, |current| {
                            current.max(status.ers_harvested_this_lap_mguh)
                        }),
                );
                driver.packet_copies.car_status = Some(status);
            }
        }
    }

    fn apply_car_damage(&mut self, packet: PacketCarDamageData) {
        for (index, damage) in packet.car_damage_data.iter().cloned().enumerate() {
            let previous_damage = self
                .driver(index)
                .and_then(|driver| driver.packet_copies.car_damage.clone());
            let driver_info_brief = self.driver_info_brief_json(index as u8);
            let mut race_control_updates = Vec::new();
            if let Some(driver) = self.driver_mut(index) {
                driver.tyre_info.wear = Some(damage.tyres_wear);
                driver.tyre_info.damage = Some(damage.tyres_damage);
                driver.car_info.front_left_wing_damage = Some(damage.front_left_wing_damage);
                driver.car_info.front_right_wing_damage = Some(damage.front_right_wing_damage);
                driver.car_info.rear_wing_damage = Some(damage.rear_wing_damage);
                driver.packet_copies.car_damage = Some(damage);

                if let Some(previous) = previous_damage {
                    for (part_name, old_value, new_value) in [
                        (
                            "m_frontLeftWingDamage",
                            previous.front_left_wing_damage,
                            driver.car_info.front_left_wing_damage.unwrap_or(0),
                        ),
                        (
                            "m_frontRightWingDamage",
                            previous.front_right_wing_damage,
                            driver.car_info.front_right_wing_damage.unwrap_or(0),
                        ),
                        (
                            "m_rearWingDamage",
                            previous.rear_wing_damage,
                            driver.car_info.rear_wing_damage.unwrap_or(0),
                        ),
                    ] {
                        if old_value != new_value {
                            race_control_updates.push(json!({
                                "message-type": "CAR_DAMAGE",
                                "lap-number": driver.lap_info.current_lap,
                                "driver-info": driver_info_brief.clone(),
                                "damaged-part": part_name,
                                "old-value": old_value,
                                "new-value": new_value,
                            }));
                            if new_value < old_value {
                                race_control_updates.push(json!({
                                    "message-type": "WING_CHANGE",
                                    "lap-number": driver.lap_info.current_lap,
                                    "driver-info": driver_info_brief.clone(),
                                }));
                            }
                        }
                    }
                }
            }
            for message in race_control_updates {
                self.push_race_control_message_value(message);
            }
        }
    }

    fn apply_motion(&mut self, packet: PacketMotionData) {
        for (index, motion) in packet.car_motion_data.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                driver.packet_copies.motion = Some(motion);
            }
        }
    }

    fn apply_car_setups(&mut self, packet: PacketCarSetupData) {
        for (index, setup) in packet.car_setups.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                driver.packet_copies.car_setup = Some(setup);
            }
        }
    }

    fn apply_session_history(&mut self, packet: PacketSessionHistoryData) {
        let car_index = usize::from(packet.car_index);
        let is_time_trial_session = self.is_time_trial_session();
        if let Some(driver) = self.driver_mut(car_index) {
            if packet.best_sector1_lap_num > 0 {
                let history_index = usize::from(packet.best_sector1_lap_num - 1);
                driver.lap_info.personal_best_sector1_time_in_ms = packet
                    .lap_history_data
                    .get(history_index)
                    .map(|lap| lap.sector1_time_in_ms);
            }
            if packet.best_sector2_lap_num > 0 {
                let history_index = usize::from(packet.best_sector2_lap_num - 1);
                driver.lap_info.personal_best_sector2_time_in_ms = packet
                    .lap_history_data
                    .get(history_index)
                    .map(|lap| lap.sector2_time_in_ms);
            }
            if packet.best_sector3_lap_num > 0 {
                let history_index = usize::from(packet.best_sector3_lap_num - 1);
                driver.lap_info.personal_best_sector3_time_in_ms = packet
                    .lap_history_data
                    .get(history_index)
                    .map(|lap| lap.sector3_time_in_ms);
            }
            if packet.best_lap_time_lap_num > 0 {
                let history_index = usize::from(packet.best_lap_time_lap_num - 1);
                if let Some(best_lap) = packet.lap_history_data.get(history_index).cloned() {
                    driver.lap_info.best_lap_time_in_ms = Some(best_lap.lap_time_in_ms);
                    driver.lap_info.best_lap_history_data = Some(best_lap);
                }
                if !is_time_trial_session {
                    driver
                        .delta_manager
                        .set_best_lap(packet.best_lap_time_lap_num);
                }
            }
            if packet.num_laps > 0 {
                let history_index = usize::from(packet.num_laps - 1);
                if let Some(last_lap) = packet.lap_history_data.get(history_index).cloned() {
                    driver.lap_info.last_lap_history_data = Some(last_lap.clone());
                    driver.lap_info.last_lap_time_in_ms = Some(last_lap.lap_time_in_ms);
                }
            }
            driver.packet_copies.session_history = Some(packet);
        }
    }

    fn apply_tyre_sets(&mut self, packet: PacketTyreSetsData) {
        let car_index = usize::from(packet.car_index);
        let previous_tyre_set = self
            .driver(car_index)
            .and_then(|driver| driver.packet_copies.tyre_sets.clone());
        if let Some(driver) = self.driver_mut(car_index) {
            driver.tyre_info.fitted_index = if packet.fitted_index == u8::MAX {
                None
            } else {
                Some(packet.fitted_index)
            };
            driver.tyre_info.fitted_tyre_set_key = packet.fitted_tyre_set_key();
            driver.tyre_info.tyre_sets = packet.tyre_set_data.clone();
            driver.packet_copies.tyre_sets = Some(packet);
        }
        if let Some(previous) = previous_tyre_set {
            let old_index = if previous.fitted_index == u8::MAX {
                None
            } else {
                Some(previous.fitted_index)
            };
            let new_index = self
                .driver(car_index)
                .and_then(|driver| driver.tyre_info.fitted_index);
            if old_index != new_index {
                let old_compound = previous
                    .fitted_tyre_set()
                    .map(|tyre_set| tyre_set.visual_tyre_compound.to_string());
                let new_compound = self
                    .driver(car_index)
                    .and_then(|driver| driver.packet_copies.tyre_sets.as_ref())
                    .and_then(|packet| packet.fitted_tyre_set())
                    .map(|tyre_set| tyre_set.visual_tyre_compound.to_string());
                self.push_race_control_message(
                    "TYRE_CHANGE",
                    self.driver(car_index)
                        .and_then(|driver| driver.lap_info.current_lap),
                    json!({
                        "driver-info": self.driver_info_brief_json(car_index as u8),
                        "old-tyre-compound": old_compound,
                        "old-tyre-index": old_index,
                        "new-tyre-compound": new_compound,
                        "new-tyre-index": new_index,
                    }),
                );
            }
        }
    }

    fn apply_final_classification(&mut self, packet: PacketFinalClassificationData) {
        self.session_info.packet_final_classification = Some(packet.clone());
        self.race_completed = true;

        for (index, classification) in packet.classification_data.iter().cloned().enumerate() {
            if let Some(driver) = self.driver_mut(index) {
                if classification.position != u8::MAX {
                    driver.driver_info.position = Some(classification.position);
                }
                driver.driver_info.grid_position = Some(classification.grid_position);
                driver.lap_info.total_race_time = Some(classification.total_race_time);
                driver.lap_info.best_lap_time_in_ms = Some(classification.best_lap_time_in_ms);
                driver.lap_info.result_status = Some(classification.result_status);
                driver.packet_copies.final_classification = Some(classification);
            }
        }
        self.recompute_dnf_count();
    }

    fn apply_time_trial(&mut self, packet: PacketTimeTrialData) {
        self.time_trial.player_session_best = Some(packet.player_session_best_data_set.clone());
        self.time_trial.personal_best = Some(packet.personal_best_data_set.clone());
        self.time_trial.rival_session_best = Some(packet.rival_session_best_data_set.clone());
        self.time_trial.packet = Some(packet);
    }

    fn apply_lap_positions(&mut self, packet: PacketLapPositionsData) {
        let mut per_driver = vec![Vec::new(); Self::MAX_DRIVERS];
        for row in &packet.lap_positions {
            for (driver_index, value) in row.iter().copied().enumerate().take(Self::MAX_DRIVERS) {
                per_driver[driver_index].push(value);
            }
        }

        for (driver_index, positions) in per_driver.into_iter().enumerate() {
            if let Some(driver) = self.driver_mut(driver_index) {
                driver.lap_positions = positions;
            }
        }

        self.last_lap_positions = Some(packet);
    }

    fn recompute_dnf_count(&mut self) {
        self.num_dnf_cars = Some(
            self.drivers
                .iter()
                .filter(|driver| driver.driver_info.dnf_status_code.is_some())
                .count() as u8,
        );
    }

    fn capture_completed_lap_samples(&mut self, driver_index: usize, completed_lap: u8) {
        let Some(driver) = self.driver_mut(driver_index) else {
            return;
        };
        let is_racing_lap = driver.current_lap_max_safety_car_status_raw.unwrap_or(0) == 0;
        let tyre_set_key = driver.tyre_info.fitted_tyre_set_key.clone();

        driver
            .per_lap_snapshots
            .entry(completed_lap)
            .or_insert_with(|| PerLapSnapshotState {
                car_status: driver.packet_copies.car_status.clone(),
                car_damage: driver.packet_copies.car_damage.clone(),
                tyre_sets: driver.packet_copies.tyre_sets.clone(),
                track_position: driver.driver_info.position,
                top_speed_kph: driver.lap_info.top_speed_kph_this_lap,
                max_safety_car_status_raw: driver.current_lap_max_safety_car_status_raw,
                ers_harvested_mguk_j: driver.car_info.current_lap_ers_harvested_mguk_j,
                ers_harvested_mguh_j: driver.car_info.current_lap_ers_harvested_mguh_j,
                ers_deployed_j: driver.car_info.current_lap_ers_deployed_j,
            });

        if driver
            .tyre_wear_samples
            .last()
            .is_none_or(|sample| sample.lap_number != completed_lap)
        {
            if let Some(damage) = driver.packet_copies.car_damage.as_ref() {
                driver.tyre_wear_samples.push(LapTyreWearSample {
                    lap_number: completed_lap,
                    wear: damage.tyres_wear,
                    is_racing_lap,
                    tyre_set_key: tyre_set_key.clone(),
                });
            }
        }

        if driver
            .fuel_samples
            .last()
            .is_none_or(|sample| sample.lap_number != completed_lap)
        {
            if let Some(status) = driver.packet_copies.car_status.as_ref() {
                driver.fuel_samples.push(FuelSample {
                    lap_number: completed_lap,
                    fuel_remaining_kg: status.fuel_in_tank,
                    is_racing_lap,
                    tyre_set_key,
                });
            }
        }
    }

    fn prune_driver_samples_from_lap(&mut self, driver_index: usize, lap_number: u8) {
        let Some(driver) = self.driver_mut(driver_index) else {
            return;
        };
        driver
            .tyre_wear_samples
            .retain(|sample| sample.lap_number < lap_number);
        driver
            .fuel_samples
            .retain(|sample| sample.lap_number < lap_number);
        driver
            .per_lap_snapshots
            .retain(|captured_lap, _| *captured_lap < lap_number);
    }

    fn current_leader_lap_number(&self) -> Option<u8> {
        self.driver_by_position(1)
            .and_then(|driver| driver.lap_info.current_lap)
    }

    pub fn next_pit_stop_window_lap(&self) -> Option<u8> {
        let ideal_lap = self
            .session_info
            .packet_session
            .as_ref()
            .map(|packet| packet.pit_stop_window_ideal_lap)
            .filter(|lap| *lap > 0)?;
        let player_lap = self
            .player_index
            .and_then(|index| self.driver(index as usize))
            .and_then(|driver| driver.lap_info.current_lap)?;
        (ideal_lap >= player_lap).then_some(ideal_lap)
    }

    fn is_time_trial_session(&self) -> bool {
        match (
            self.session_info.packet_format,
            self.session_info.session_type_raw,
        ) {
            (Some(2023), Some(value)) => f1_types::SessionType23::try_from(value)
                .map(|session| session.is_time_trial_type_session())
                .unwrap_or(false),
            (Some(_), Some(value)) => f1_types::SessionType24::try_from(value)
                .map(|session| session.is_time_trial_type_session())
                .unwrap_or(false),
            _ => false,
        }
    }

    pub(crate) fn driver_by_position(&self, position: u8) -> Option<&DriverState> {
        self.drivers
            .iter()
            .find(|driver| driver.is_valid() && driver.driver_info.position == Some(position))
    }

    fn driver_info_brief_json(&self, index: u8) -> Value {
        self.driver(index as usize)
            .map(|driver| {
                json!({
                    "name": driver.driver_info.name,
                    "team": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                    "driver-number": driver.driver_info.driver_number,
                })
            })
            .unwrap_or(Value::Null)
    }

    fn push_race_control_message(
        &mut self,
        message_type: &str,
        lap_number: Option<u8>,
        payload: Value,
    ) {
        let mut object = Map::new();
        object.insert("id".to_string(), json!(self.events.next_message_id + 1));
        object.insert("message-type".to_string(), json!(message_type));
        object.insert("lap-number".to_string(), json!(lap_number));
        if let Some(payload) = payload.as_object() {
            for (key, value) in payload {
                object.insert(key.clone(), value.clone());
            }
        }
        self.events.next_message_id += 1;
        self.events
            .race_control_messages
            .push(Value::Object(object));
    }

    fn push_race_control_message_value(&mut self, value: Value) {
        let lap_number = value
            .get("lap-number")
            .and_then(|value| value.as_u64())
            .map(|value| value as u8);
        let message_type = value
            .get("message-type")
            .and_then(|value| value.as_str())
            .unwrap_or("DEFAULT")
            .to_string();
        self.push_race_control_message(&message_type, lap_number, value);
    }
}
