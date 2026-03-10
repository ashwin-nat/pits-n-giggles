use std::collections::BTreeMap;

use f1_types::{SessionType23, SessionType24, TeamID24, TeamID25};
use serde::Serialize;
use serde_json::{Map, Value, json};

use crate::{DriverState, SessionState};

fn session_type_label(packet_format: u16, value: u8) -> String {
    if packet_format == 2023 {
        SessionType23::try_from(value)
            .map(|session| session.to_string())
            .unwrap_or_else(|_| value.to_string())
    } else {
        SessionType24::try_from(value)
            .map(|session| session.to_string())
            .unwrap_or_else(|_| value.to_string())
    }
}

fn is_time_trial_session(packet_format: Option<u16>, session_type_raw: Option<u8>) -> bool {
    match (packet_format, session_type_raw) {
        (Some(2023), Some(value)) => SessionType23::try_from(value)
            .map(|session| session.is_time_trial_type_session())
            .unwrap_or(false),
        (Some(_), Some(value)) => SessionType24::try_from(value)
            .map(|session| session.is_time_trial_type_session())
            .unwrap_or(false),
        _ => false,
    }
}

pub(crate) fn track_label(value: i8) -> String {
    match value {
        0 => "Melbourne",
        1 => "Paul Ricard",
        2 => "Shanghai",
        3 => "Sakhir",
        4 => "Catalunya",
        5 => "Monaco",
        6 => "Montreal",
        7 => "Silverstone",
        8 => "Hockenheim",
        9 => "Hungaroring",
        10 => "Spa",
        11 => "Monza",
        12 => "Singapore",
        13 => "Suzuka",
        14 => "Abu Dhabi",
        15 => "Texas",
        16 => "Brazil",
        17 => "Austria",
        18 => "Sochi",
        19 => "Mexico",
        20 => "Baku",
        21 => "Sakhir Short",
        22 => "Silverstone Short",
        23 => "Texas Short",
        24 => "Suzuka Short",
        25 => "Hanoi",
        26 => "Zandvoort",
        27 => "Imola",
        28 => "Portimao",
        29 => "Jeddah",
        30 => "Miami",
        31 => "Las Vegas",
        32 => "Losail",
        39 => "Silverstone_Reverse",
        40 => "Austria_Reverse",
        41 => "Zandvoort_Reverse",
        _ => return value.to_string(),
    }
    .to_string()
}

fn formula_label(value: u8) -> String {
    match value {
        0 => "F1 Modern",
        1 => "F1 Classic",
        2 => "F2",
        3 => "F1 Generic",
        4 => "Beta",
        5 => "Supercars",
        6 => "Esports",
        7 => "F2 2021",
        8 => "F1 World",
        9 => "F1 Elimination",
        _ => return value.to_string(),
    }
    .to_string()
}

fn safety_car_status_label(value: u8) -> String {
    match value {
        0 => "NO_SAFETY_CAR",
        1 => "FULL_SAFETY_CAR",
        2 => "VIRTUAL_SAFETY_CAR",
        3 => "FORMATION_LAP",
        _ => return value.to_string(),
    }
    .to_string()
}

fn telemetry_setting_label(value: u8) -> &'static str {
    match value {
        1 => "Public",
        _ => "Restricted",
    }
}

const SECTOR_STATUS_NA: i32 = -2;
const SECTOR_STATUS_INVALID: i32 = -1;
const SECTOR_STATUS_YELLOW: i32 = 0;
const SECTOR_STATUS_GREEN: i32 = 1;
const SECTOR_STATUS_PURPLE: i32 = 2;
const SECTOR_1_VALID_MASK: u8 = 0x02;
const SECTOR_2_VALID_MASK: u8 = 0x04;
const SECTOR_3_VALID_MASK: u8 = 0x08;

pub(crate) fn team_label(packet_format: u16, value: u8) -> String {
    if packet_format == 2023 {
        match value {
            0 => "Mercedes",
            1 => "Ferrari",
            2 => "Red Bull Racing",
            3 => "Williams",
            4 => "Aston Martin",
            5 => "Alpine",
            6 => "Alpha Tauri",
            7 => "Haas",
            8 => "McLaren",
            9 => "Alfa Romeo",
            255 => "MY_TEAM",
            _ => return value.to_string(),
        }
        .to_string()
    } else if packet_format == 2024 {
        TeamID24::from_raw(value)
            .map(|team| team.to_string())
            .unwrap_or_else(|| value.to_string())
    } else {
        TeamID25::from_raw(value)
            .map(|team| team.to_string())
            .unwrap_or_else(|| value.to_string())
    }
}

fn is_finish_line_after_pit_garage(track_id_raw: i8) -> bool {
    matches!(
        track_id_raw,
        0 | 3 | 5 | 10 | 11 | 14 | 17 | 26 | 27 | 28 | 31 | 32 | 39 | 40 | 41
    )
}

fn pit_time_loss(track_id_raw: i8, formula_raw: u8) -> Option<f64> {
    let is_f2 = matches!(formula_raw, 2 | 7);
    if is_f2 {
        return None;
    }

    match track_id_raw {
        0 => Some(18.0),
        1 => None,
        2 => Some(22.0),
        3 => Some(23.0),
        4 => Some(21.0),
        5 => Some(19.0),
        6 => Some(16.0),
        7 => Some(28.0),
        9 => Some(20.0),
        10 => Some(18.0),
        11 => Some(24.0),
        12 => Some(26.0),
        13 => Some(22.0),
        14 => Some(19.0),
        15 => Some(20.0),
        16 => Some(20.0),
        17 => Some(19.0),
        19 => Some(22.0),
        20 => Some(18.0),
        26 => Some(18.0),
        27 => Some(27.0),
        28 => None,
        29 => Some(18.0),
        30 => Some(19.0),
        31 => Some(20.0),
        32 => Some(25.0),
        39 => None,
        40 => Some(19.0),
        41 => Some(18.0),
        _ => None,
    }
}

fn serializable_value<T: Serialize>(value: Option<&T>) -> Value {
    value
        .map(|value| serde_json::to_value(value).unwrap_or(Value::Null))
        .unwrap_or(Value::Null)
}

fn format_time_ms(ms: u32) -> String {
    if ms == 0 {
        return "---".to_string();
    }

    let minutes = ms / 60_000;
    let seconds = (ms % 60_000) / 1_000;
    let millis = ms % 1_000;
    if minutes > 0 {
        format!("{minutes}:{seconds:02}.{millis:03}")
    } else {
        format!("{seconds:02}.{millis:03}")
    }
}

fn format_sector_ms(ms: u16) -> String {
    if ms == 0 {
        return "---".to_string();
    }
    format_time_ms(u32::from(ms))
}

fn sector_status(
    sector_time: u16,
    session_best_ms: u16,
    personal_best_ms: u16,
    sector_valid: bool,
) -> i32 {
    if sector_time == session_best_ms {
        return SECTOR_STATUS_PURPLE;
    }
    if sector_time == personal_best_ms {
        return SECTOR_STATUS_GREEN;
    }
    if !sector_valid {
        return SECTOR_STATUS_INVALID;
    }
    SECTOR_STATUS_YELLOW
}

fn snapshot_tyre_set_info_value(driver: &DriverState, lap_number: u8) -> Value {
    let Some(snapshot) = driver.per_lap_snapshots.get(&lap_number) else {
        return Value::Null;
    };
    let tyre_set = snapshot
        .tyre_sets
        .as_ref()
        .and_then(|packet| packet.fitted_tyre_set());
    let wear = snapshot.car_damage.as_ref().map(|damage| damage.tyres_wear);
    let status = snapshot.car_status.as_ref();

    json!({
        "visual-tyre-compound": status.map(|status| status.visual_tyre_compound.to_string()),
        "actual-tyre-compound": status.map(|status| status.actual_tyre_compound.to_string()),
        "tyre-set": tyre_set,
        "tyre-wear": {
            "front-left": wear.map(|wear| wear[0]),
            "front-right": wear.map(|wear| wear[1]),
            "rear-left": wear.map(|wear| wear[2]),
            "rear-right": wear.map(|wear| wear[3]),
            "average": wear.map(|wear| wear.iter().sum::<f32>() / 4.0),
        }
    })
}

fn snapshot_tyre_wear_history_value(driver: &DriverState, start_lap: u8, end_lap: u8) -> Value {
    let mut history = Vec::new();

    if start_lap == 1 {
        if let Some(snapshot) = driver.per_lap_snapshots.get(&0) {
            if let Some(wear) = snapshot.car_damage.as_ref().map(|damage| damage.tyres_wear) {
                history.push(json!({
                    "lap-number": 0,
                    "front-left-wear": wear[0],
                    "front-right-wear": wear[1],
                    "rear-left-wear": wear[2],
                    "rear-right-wear": wear[3],
                    "average": wear.iter().sum::<f32>() / 4.0,
                }));
            }
        }
    }

    for lap_number in start_lap..=end_lap {
        let Some(snapshot) = driver.per_lap_snapshots.get(&lap_number) else {
            continue;
        };
        let Some(wear) = snapshot.car_damage.as_ref().map(|damage| damage.tyres_wear) else {
            continue;
        };
        history.push(json!({
            "lap-number": lap_number,
            "front-left-wear": wear[0],
            "front-right-wear": wear[1],
            "rear-left-wear": wear[2],
            "rear-right-wear": wear[3],
            "average": wear.iter().sum::<f32>() / 4.0,
        }));
    }

    Value::Array(history)
}

impl SessionState {
    pub fn periodic_update_json(&self) -> Value {
        let packet_format = self.session_info.packet_format;
        let session_type = match (packet_format, self.session_info.session_type_raw) {
            (Some(packet_format), Some(raw)) => Some(session_type_label(packet_format, raw)),
            _ => None,
        };
        let weather_forecast_samples = self
            .session_info
            .weather_forecast_samples
            .iter()
            .map(|sample| {
                let mut value = serde_json::to_value(sample).unwrap_or_else(|_| Value::Null);
                if let Some(object) = value.as_object_mut() {
                    object.insert(
                        "rain-probability".to_string(),
                        json!(sample.rain_percentage.to_string()),
                    );
                }
                value
            })
            .collect::<Vec<_>>();

        let current_lap = self.current_lap_for_periodic_update();
        let fastest_driver = self
            .fastest_index
            .and_then(|index| self.driver(index as usize))
            .and_then(|driver| driver.driver_info.name.clone());
        let fastest_tyre = self
            .fastest_index
            .and_then(|index| self.driver(index as usize))
            .and_then(|driver| driver.lap_info.best_lap_visual_tyre_compound)
            .map(|compound| compound.to_string());
        let fastest_lap = self
            .fastest_index
            .and_then(|index| self.driver(index as usize))
            .and_then(|driver| driver.lap_info.best_lap_time_in_ms);

        let mut response = Map::from_iter([
            ("live-data".to_string(), Value::Bool(true)),
            (
                "f1-game-year".to_string(),
                json!(self.session_info.game_year),
            ),
            (
                "packet-format".to_string(),
                json!(self.session_info.packet_format),
            ),
            (
                "circuit".to_string(),
                json!(
                    self.session_info
                        .track_id_raw
                        .map(track_label)
                        .unwrap_or_else(|| "---".to_string())
                ),
            ),
            (
                "formula".to_string(),
                json!(self.session_info.formula_raw.map(formula_label)),
            ),
            (
                "pit-time-loss".to_string(),
                json!(
                    self.session_info
                        .track_id_raw
                        .zip(self.session_info.formula_raw)
                        .and_then(|(track_id_raw, formula_raw)| pit_time_loss(
                            track_id_raw,
                            formula_raw
                        ))
                ),
            ),
            (
                "track-temperature".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.track_temperature)
                        .unwrap_or(0)
                ),
            ),
            (
                "air-temperature".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.air_temperature)
                        .unwrap_or(0)
                ),
            ),
            ("event-type".to_string(), json!(session_type.clone())),
            (
                "session-uid".to_string(),
                json!(self.session_info.session_uid),
            ),
            (
                "session-time-left".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.session_time_left)
                        .unwrap_or(0)
                ),
            ),
            (
                "total-laps".to_string(),
                json!(self.session_info.total_laps),
            ),
            ("current-lap".to_string(), json!(current_lap)),
            (
                "safety-car-status".to_string(),
                json!(
                    self.session_info
                        .safety_car_status_raw
                        .map(safety_car_status_label)
                        .unwrap_or_default()
                ),
            ),
            (
                "pit-speed-limit".to_string(),
                json!(self.session_info.pit_speed_limit.unwrap_or(0)),
            ),
            (
                "weather-forecast-samples".to_string(),
                Value::Array(weather_forecast_samples),
            ),
            ("race-ended".to_string(), Value::Bool(self.race_completed)),
            (
                "is-spectating".to_string(),
                json!(self.session_info.is_spectating.unwrap_or(false)),
            ),
            (
                "session-type".to_string(),
                json!(session_type.clone().unwrap_or_else(|| "---".to_string())),
            ),
            (
                "session-duration-so-far".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| {
                            packet
                                .session_duration
                                .saturating_sub(packet.session_time_left)
                        })
                        .unwrap_or(0)
                ),
            ),
            (
                "num-sc".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.num_safety_car_periods)
                        .unwrap_or(0)
                ),
            ),
            (
                "num-vsc".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.num_virtual_safety_car_periods)
                        .unwrap_or(0)
                ),
            ),
            (
                "num-red-flags".to_string(),
                json!(
                    self.session_info
                        .packet_session
                        .as_ref()
                        .map(|packet| packet.num_red_flag_periods)
                        .unwrap_or(0)
                ),
            ),
            (
                "player-pit-window".to_string(),
                json!(self.next_pit_stop_window_lap()),
            ),
            (
                "spectator-car-index".to_string(),
                json!(self.session_info.spectator_car_index),
            ),
            ("wdt-status".to_string(), Value::Bool(self.connected_to_sim)),
            (
                "fastest-lap-overall".to_string(),
                json!(fastest_lap.unwrap_or(0)),
            ),
            (
                "fastest-lap-overall-driver".to_string(),
                json!(fastest_driver),
            ),
            ("fastest-lap-overall-tyre".to_string(), json!(fastest_tyre)),
        ]);

        if is_time_trial_session(packet_format, self.session_info.session_type_raw) {
            response.insert("tt-data".to_string(), self.time_trial_json());
        } else {
            response.insert(
                "table-entries".to_string(),
                Value::Array(self.table_entries_json()),
            );
        }

        Value::Object(response)
    }

    pub fn race_info_json(&self) -> Value {
        let mut classification_data = self.table_entries_json();
        for entry in &mut classification_data {
            if let Some(object) = entry.as_object_mut() {
                object.remove("fuel-info");
            }
        }
        let overtake_records = self.overtake_records_json();
        let overtakes_summary = self.overtakes_summary_json(&overtake_records);

        json!({
            "classification-data": classification_data,
            "collisions": {
                "records": self.events.collisions.iter().map(|(driver_1, driver_2)| {
                    json!({
                        "driver-1-index": driver_1,
                        "driver-1-name": self.driver(*driver_1 as usize).and_then(|driver| driver.driver_info.name.clone()),
                        "driver-1-lap": self.driver(*driver_1 as usize).and_then(|driver| driver.lap_info.current_lap),
                        "driver-2-index": driver_2,
                        "driver-2-name": self.driver(*driver_2 as usize).and_then(|driver| driver.driver_info.name.clone()),
                        "driver-2-lap": self.driver(*driver_2 as usize).and_then(|driver| driver.lap_info.current_lap),
                    })
                }).collect::<Vec<_>>()
            },
            "session-info": serializable_value(self.session_info.packet_session.as_ref()),
            "race-control": Value::Array(self.events.race_control_messages.clone()),
            "records": {
                "fastest": self.fastest_records_json(),
                "tyre-stats": self.tyre_stats_json(),
            },
            "overtakes": overtakes_summary,
            "custom-markers": serde_json::to_value(&self.events.custom_markers).unwrap_or(Value::Array(Vec::new())),
            "position-history": self.position_history_json(),
            "tyre-stint-history-v2": self.tyre_stint_history_v2_json(),
            "speed-trap-records": self.speed_trap_records_json(),
        })
    }

    pub fn event_info_prefix(&self) -> Option<String> {
        let packet_format = self.session_info.packet_format?;
        let session_type_raw = self.session_info.session_type_raw?;
        let track_id_raw = self.session_info.track_id_raw?;
        let session_type = session_type_label(packet_format, session_type_raw);
        let track = track_label(track_id_raw);
        Some(format!(
            "{}_{}_",
            session_type.replace(' ', "_"),
            track.replace(' ', "_")
        ))
    }

    pub fn save_data_json(&self, version: &str) -> Option<Value> {
        if !self.is_data_available() {
            return None;
        }

        let mut value = self.race_info_json();
        let object = value.as_object_mut()?;
        object.insert("game-year".to_string(), json!(self.session_info.game_year));
        object.insert(
            "packet-format".to_string(),
            json!(self.session_info.packet_format),
        );
        object.insert("version".to_string(), json!(version));
        Some(value)
    }

    pub fn driver_info_json(&self, index: usize) -> Option<Value> {
        let driver = self.driver(index)?;
        let packet_format = self.session_info.packet_format.unwrap_or(2025);

        Some(json!({
            "index": index,
            "is-player": driver.driver_info.is_player,
            "driver-name": driver.driver_info.name,
            "track-position": driver.driver_info.position,
            "team": driver.driver_info.team_id_raw.map(|team_id| team_label(packet_format, team_id)),
            "telemetry-settings": driver.driver_info.telemetry_setting_raw.map(telemetry_setting_label).unwrap_or("Restricted"),
            "current-lap": driver.lap_info.current_lap,
            "top-speed-kmph": driver.lap_info.top_speed_kph_overall,
            "car-damage": serializable_value(driver.packet_copies.car_damage.as_ref()),
            "car-status": serializable_value(driver.packet_copies.car_status.as_ref()),
            "participant-data": serializable_value(driver.packet_copies.participant_data.as_ref()),
            "tyre-sets": serializable_value(driver.packet_copies.tyre_sets.as_ref()),
            "session-history": serializable_value(driver.packet_copies.session_history.as_ref()),
            "final-classification": serializable_value(driver.packet_copies.final_classification.as_ref()),
            "lap-data": serializable_value(driver.packet_copies.lap_data.as_ref()),
            "car-setup": serializable_value(driver.packet_copies.car_setup.as_ref()),
            "warning-penalty-history": Value::Array(driver.warning_penalty_history.clone()),
            "tyre-set-history": self.driver_tyre_set_history_json(driver),
            "per-lap-info": self.driver_per_lap_info_json(driver),
            "tyre-wear-predictions": {
                "status": false,
                "desc": "Analyzer not yet ported to Rust",
                "predictions": Value::Array(Vec::new()),
                "rate": {
                    "front-left": Value::Null,
                    "front-right": Value::Null,
                    "rear-left": Value::Null,
                    "rear-right": Value::Null,
                },
                "selected-pit-stop-lap": Value::Null,
            },
            "lap-time-history": self.driver_lap_time_history_json(driver),
            "collisions": {
                "records": self.events.collisions.iter().filter_map(|(driver_1, driver_2)| {
                    if usize::from(*driver_1) != index && usize::from(*driver_2) != index {
                        return None;
                    }
                    Some(json!({
                        "driver-1-index": driver_1,
                        "driver-1-name": self.driver(*driver_1 as usize).and_then(|driver| driver.driver_info.name.clone()),
                        "driver-1-lap": self.driver(*driver_1 as usize).and_then(|driver| driver.lap_info.current_lap),
                        "driver-2-index": driver_2,
                        "driver-2-name": self.driver(*driver_2 as usize).and_then(|driver| driver.driver_info.name.clone()),
                        "driver-2-lap": self.driver(*driver_2 as usize).and_then(|driver| driver.lap_info.current_lap),
                    }))
                }).collect::<Vec<_>>(),
            },
            "race-control": Value::Array(self.events.race_control_messages.clone()),
            "overtakes-status-code": if self.race_completed { "RACE_COMPLETED" } else if self.events.overtakes.is_empty() { "NO_DATA" } else { "RACE_ONGOING" },
            "overtakes": {
                "records": self.events.overtakes.iter().enumerate().filter_map(|(overtake_id, overtake)| {
                    let driver_name = driver.driver_info.name.as_deref();
                    let overtaking_name = self.driver(overtake.overtaking_vehicle_index as usize).and_then(|driver| driver.driver_info.name.as_deref());
                    let overtaken_name = self.driver(overtake.overtaken_vehicle_index as usize).and_then(|driver| driver.driver_info.name.as_deref());
                    if driver_name != overtaking_name && driver_name != overtaken_name {
                        return None;
                    }
                    Some(json!({
                        "overtaking-driver-index": overtake.overtaking_vehicle_index,
                        "overtaking-driver-name": overtaking_name,
                        "overtaking-driver-lap": overtake.overtaking_lap,
                        "overtaken-driver-index": overtake.overtaken_vehicle_index,
                        "overtaken-driver-name": overtaken_name,
                        "overtaken-driver-lap": overtake.overtaken_lap,
                        "overtake-id": overtake_id,
                    }))
                }).collect::<Vec<_>>(),
            },
            "circuit": self.session_info.track_id_raw.map(track_label),
            "session-type": match (self.session_info.packet_format, self.session_info.session_type_raw) {
                (Some(packet_format), Some(raw)) => Some(session_type_label(packet_format, raw)),
                _ => None,
            },
            "is-finish-line-after-pit-garage": self.session_info.track_id_raw.map(is_finish_line_after_pit_garage),
        }))
    }

    pub fn stream_overlay_json(&self, show_sample_data_at_start: bool) -> Value {
        let reference_index = if self.session_info.is_spectating.unwrap_or(false) {
            self.session_info
                .spectator_car_index
                .or(self.player_index)
                .map(usize::from)
        } else {
            self.player_index.map(usize::from)
        };
        let packet_format = self.session_info.packet_format;
        let event_type = match (packet_format, self.session_info.session_type_raw) {
            (Some(packet_format), Some(raw)) => Some(session_type_label(packet_format, raw)),
            _ => None,
        };
        let driver = reference_index.and_then(|index| self.driver(index));
        let player_position = driver.and_then(|driver| driver.driver_info.position);
        let prev_driver = player_position
            .and_then(|position| self.driver_by_position(position.saturating_sub(1)));
        let next_driver =
            player_position.and_then(|position| self.driver_by_position(position + 1));
        let telemetry = driver.and_then(|driver| driver.packet_copies.car_telemetry.as_ref());
        let motion = driver.and_then(|driver| driver.packet_copies.motion.as_ref());
        let weather_forecast_samples = self
            .session_info
            .weather_forecast_samples
            .iter()
            .map(|sample| {
                let mut value = serde_json::to_value(sample).unwrap_or_else(|_| Value::Null);
                if let Some(object) = value.as_object_mut() {
                    object.insert(
                        "rain-probability".to_string(),
                        json!(sample.rain_percentage.to_string()),
                    );
                }
                value
            })
            .collect::<Vec<_>>();

        json!({
            "show-sample-data-at-start": show_sample_data_at_start,
            "f1-game-year": self.session_info.game_year,
            "f1-packet-format": self.session_info.packet_format,
            "event-type": event_type,
            "circuit": self.session_info.track_id_raw.map(track_label),
            "total-laps": self.session_info.total_laps,
            "pit-speed-limit": self.session_info.pit_speed_limit,
            "weather-forecast-samples": weather_forecast_samples,
            "car-telemetry": {
                "throttle": telemetry.map(|value| value.throttle * 100.0).unwrap_or(0.0),
                "brake": telemetry.map(|value| value.brake * 100.0).unwrap_or(0.0),
                "steering": telemetry.map(|value| value.steer * 100.0).unwrap_or(0.0),
                "rev-lights-percent": telemetry.map(|value| value.rev_lights_percent).unwrap_or(0),
            },
            "penalties-and-stats": {
                "air-temperature": self.session_info.packet_session.as_ref().map(|packet| packet.air_temperature),
                "track-temperature": self.session_info.packet_session.as_ref().map(|packet| packet.track_temperature),
                "corner-cutting-warnings": driver.and_then(|driver| driver.lap_info.corner_cutting_warnings),
                "speed-trap-record": driver.and_then(|driver| driver.lap_info.speed_trap_fastest_speed),
                "pit-speed-limit": self.session_info.pit_speed_limit,
            },
            "lap-time-history": driver.map(|driver| self.driver_lap_time_history_json(driver)).unwrap_or(Value::Null),
            "g-force": {
                "lat": motion.map(|value| value.g_force_lateral).unwrap_or(0.0),
                "long": motion.map(|value| value.g_force_longitudinal).unwrap_or(0.0),
                "vert": motion.map(|value| value.g_force_vertical).unwrap_or(0.0),
            },
            "pace-comparison": {
                "player": self.pace_driver_json(driver),
                "prev": self.pace_driver_json(prev_driver),
                "next": self.pace_driver_json(next_driver),
            },
            "motion": self
                .drivers
                .iter()
                .filter(|driver| driver.is_valid())
                .map(|driver| {
                    json!({
                        "name": driver.driver_info.name,
                        "team": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                        "track-position": driver.driver_info.position,
                        "index": driver.index,
                        "motion": driver.packet_copies.motion.as_ref(),
                        "ers": {
                            "ers-percent": driver.car_info.ers_percent,
                            "ers-mode": driver.packet_copies.car_status.as_ref().map(|status| status.ers_deploy_mode.to_string()),
                            "ers-harvested-by-mguk-this-lap": driver.packet_copies.car_status.as_ref().map(|status| {
                                (status.ers_harvested_this_lap_mguk / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY) * 100.0
                            }),
                            "ers-deployed-this-lap": driver.packet_copies.car_status.as_ref().map(|status| {
                                (status.ers_deployed_this_lap / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY) * 100.0
                            }),
                        },
                    })
                })
                .collect::<Vec<_>>(),
        })
    }

    fn current_lap_for_periodic_update(&self) -> Option<u8> {
        let is_spectator = self.session_info.is_spectating.unwrap_or(false);
        if is_spectator {
            self.drivers
                .iter()
                .filter(|driver| driver.is_valid())
                .min_by_key(|driver| driver.driver_info.position.unwrap_or(u8::MAX))
                .and_then(|driver| driver.lap_info.current_lap)
        } else {
            self.player_index
                .and_then(|index| self.driver(index as usize))
                .and_then(|driver| driver.lap_info.current_lap)
        }
    }

    fn table_entries_json(&self) -> Vec<Value> {
        let packet_format = self.session_info.packet_format.unwrap_or(2025);
        let fastest_index = self.fastest_index;
        let mut drivers = self
            .drivers
            .iter()
            .filter(|driver| driver.is_valid())
            .collect::<Vec<_>>();
        drivers.sort_by_key(|driver| driver.driver_info.position.unwrap_or(u8::MAX));

        drivers
            .into_iter()
            .map(|driver| {
                let drs_activated = driver.car_info.drs_activated.unwrap_or(false);
                let drs_allowed = driver.car_info.drs_allowed.unwrap_or(false);
                let drs_distance = driver.car_info.drs_distance.unwrap_or(0);
                let drs = drs_activated || drs_allowed || drs_distance > 0;
                let ers_mode = driver
                    .packet_copies
                    .car_status
                    .as_ref()
                    .map(|status| status.ers_deploy_mode.to_string());
                let ers_harvested = driver
                    .packet_copies
                    .car_status
                    .as_ref()
                    .map(|status| {
                        (status.ers_harvested_this_lap_mguk
                            / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY)
                            * 100.0
                    })
                    .unwrap_or(0.0);
                let ers_deployed = driver
                    .packet_copies
                    .car_status
                    .as_ref()
                    .map(|status| {
                        (status.ers_deployed_this_lap
                            / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY)
                            * 100.0
                    })
                    .unwrap_or(0.0);
                let lap_progress = match (
                    driver.packet_copies.lap_data.as_ref(),
                    self.session_info.track_length,
                ) {
                    (Some(lap_data), Some(track_length)) if track_length > 0 => {
                        Some((lap_data.lap_distance / f32::from(track_length)) * 100.0)
                    }
                    _ => None,
                };
                let team = driver
                    .driver_info
                    .team_id_raw
                    .map(|team_id| team_label(packet_format, team_id));

                json!({
                    "driver-info": {
                        "position": driver.driver_info.position,
                        "grid-position": driver.driver_info.grid_position,
                        "name": driver.driver_info.name,
                        "team": team,
                        "is-fastest": fastest_index == Some(driver.index as u8),
                        "is-player": driver.driver_info.is_player,
                        "dnf-status": driver.driver_info.dnf_status_code,
                        "index": driver.index,
                        "telemetry-setting": driver.driver_info.telemetry_setting_raw.map(telemetry_setting_label).unwrap_or("N/A"),
                        "is-pitting": driver.lap_info.is_pitting.unwrap_or(false),
                        "drs": drs,
                        "drs-activated": drs_activated,
                        "drs-allowed": drs_allowed,
                        "drs-distance": drs_distance,
                    },
                    "delta-info": {
                        "delta": driver.lap_info.delta_to_car_in_front_ms,
                        "delta-to-car-in-front": driver.lap_info.delta_to_car_in_front_ms,
                        "delta-to-leader": driver.lap_info.delta_to_leader_ms,
                    },
                    "ers-info": {
                        "ers-percent": driver.car_info.ers_percent.map(|value| format!("{value:.2}%")).unwrap_or_else(|| "0.00%".to_string()),
                        "ers-percent-float": driver.car_info.ers_percent,
                        "ers-mode": ers_mode,
                        "ers-harvested-by-mguk-this-lap": ers_harvested,
                        "ers-deployed-this-lap": ers_deployed,
                    },
                    "lap-info": {
                        "current-lap": driver.lap_info.current_lap,
                        "last-lap": {
                            "lap-time-ms": driver.lap_info.last_lap_time_in_ms,
                            "sector-status": self.last_lap_sector_status_json(driver),
                            "s1-time-ms": driver.lap_info.last_lap_history_data.as_ref().map(|lap| lap.sector1_time_in_ms),
                            "s2-time-ms": driver.lap_info.last_lap_history_data.as_ref().map(|lap| lap.sector2_time_in_ms),
                            "s3-time-ms": driver.lap_info.last_lap_history_data.as_ref().map(|lap| lap.sector3_time_in_ms),
                        },
                        "best-lap": {
                            "lap-time-ms": driver.lap_info.best_lap_time_in_ms,
                            "sector-status": self.best_lap_sector_status_json(driver),
                            "s1-time-ms": driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector1_time_in_ms),
                            "s2-time-ms": driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector2_time_in_ms),
                            "s3-time-ms": driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector3_time_in_ms),
                        },
                        "curr-lap": {
                            "lap-time-ms": driver.lap_info.current_lap_time_in_ms,
                            "s1-time-ms": driver.lap_info.current_lap_sector1_time_in_ms,
                            "s2-time-ms": driver.lap_info.current_lap_sector2_time_in_ms,
                            "s3-time-ms": driver.lap_info.current_lap_sector3_time_in_ms,
                            "sector": driver.lap_info.current_sector,
                            "driver-status": driver.lap_info.current_driver_status,
                            "sector-status": self.current_lap_sector_status_json(driver),
                            "lap-num": driver.lap_info.current_lap,
                            "delta-ms": driver.lap_info.current_lap_delta_ms,
                            "delta-sc-sec": driver.lap_info.safety_car_delta,
                        },
                        "lap-progress": lap_progress,
                        "speed-trap-record-kmph": driver.lap_info.speed_trap_fastest_speed,
                        "top-speed-kmph": driver.lap_info.top_speed_kph_this_lap,
                    },
                    "warns-pens-info": {
                        "corner-cutting-warnings": driver.lap_info.corner_cutting_warnings,
                        "time-penalties": driver.lap_info.penalties,
                        "num-dt": driver.lap_info.num_unserved_drive_through_pens,
                        "num-sg": driver.lap_info.num_unserved_stop_go_pens,
                    },
                    "tyre-info": {
                        "wear-prediction": Value::Null,
                        "current-wear": driver.tyre_info.wear,
                        "tyre-age": driver.tyre_info.tyre_age_laps,
                        "tyre-life-remaining": Value::Null,
                        "visual-tyre-compound": driver.tyre_info.visual_compound.map(|compound| compound.to_string()).unwrap_or_default(),
                        "actual-tyre-compound": driver.tyre_info.actual_compound.map(|compound| compound.to_string()).unwrap_or_default(),
                        "num-pitstops": driver.pit_info.num_stops,
                    },
                    "damage-info": {
                        "fl-wing-damage": driver.car_info.front_left_wing_damage,
                        "fr-wing-damage": driver.car_info.front_right_wing_damage,
                        "rear-wing-damage": driver.car_info.rear_wing_damage,
                    },
                    "fuel-info": {
                        "fuel-load-kg": driver.packet_copies.car_status.as_ref().map(|status| status.fuel_in_tank),
                        "fuel-laps-remaining": driver.packet_copies.car_status.as_ref().map(|status| status.fuel_remaining_laps),
                    },
                    "pit-info": {
                        "pit-status": driver.pit_info.pit_status,
                        "num-stops": driver.pit_info.num_stops,
                        "pit-lane-timer-active": driver.pit_info.pit_lane_timer_active,
                        "pit-lane-timer-ms": driver.pit_info.pit_lane_time_in_lane_ms,
                        "pit-stop-timer-ms": driver.pit_info.pit_stop_timer_ms,
                        "pit-stop-should-serve-pen": driver.pit_info.pit_stop_should_serve_pen,
                    }
                })
            })
            .collect()
    }

    fn best_lap_sector_status_json(&self, driver: &DriverState) -> Value {
        self.completed_lap_sector_status_json(
            driver,
            driver.lap_info.best_lap_history_data.as_ref(),
        )
    }

    fn last_lap_sector_status_json(&self, driver: &DriverState) -> Value {
        self.completed_lap_sector_status_json(
            driver,
            driver.lap_info.last_lap_history_data.as_ref(),
        )
    }

    fn completed_lap_sector_status_json(
        &self,
        driver: &DriverState,
        lap: Option<&f1_types::LapHistoryData>,
    ) -> Value {
        let Some(lap) = lap else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(session_best_sector1_ms) =
            self.fastest_sector_ms(|driver| driver.lap_info.personal_best_sector1_time_in_ms)
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(session_best_sector2_ms) =
            self.fastest_sector_ms(|driver| driver.lap_info.personal_best_sector2_time_in_ms)
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(session_best_sector3_ms) =
            self.fastest_sector_ms(|driver| driver.lap_info.personal_best_sector3_time_in_ms)
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(personal_best_sector1_ms) = driver.lap_info.personal_best_sector1_time_in_ms
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(personal_best_sector2_ms) = driver.lap_info.personal_best_sector2_time_in_ms
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(personal_best_sector3_ms) = driver.lap_info.personal_best_sector3_time_in_ms
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };

        json!([
            sector_status(
                lap.sector1_time_in_ms,
                session_best_sector1_ms,
                personal_best_sector1_ms,
                lap.lap_valid_bit_flags & SECTOR_1_VALID_MASK != 0,
            ),
            sector_status(
                lap.sector2_time_in_ms,
                session_best_sector2_ms,
                personal_best_sector2_ms,
                lap.lap_valid_bit_flags & SECTOR_2_VALID_MASK != 0,
            ),
            sector_status(
                lap.sector3_time_in_ms,
                session_best_sector3_ms,
                personal_best_sector3_ms,
                lap.lap_valid_bit_flags & SECTOR_3_VALID_MASK != 0,
            ),
        ])
    }

    fn current_lap_sector_status_json(&self, driver: &DriverState) -> Value {
        let Some(current_lap_time_in_ms) = driver.lap_info.current_lap_time_in_ms else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(current_sector) = driver.lap_info.current_sector.as_deref() else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        if current_lap_time_in_ms == 0 || current_sector == "SECTOR1" {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        }

        let Some(session_best_sector1_ms) =
            self.fastest_sector_ms(|driver| driver.lap_info.personal_best_sector1_time_in_ms)
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(session_best_sector2_ms) =
            self.fastest_sector_ms(|driver| driver.lap_info.personal_best_sector2_time_in_ms)
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(personal_best_sector1_ms) = driver.lap_info.personal_best_sector1_time_in_ms
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };
        let Some(personal_best_sector2_ms) = driver.lap_info.personal_best_sector2_time_in_ms
        else {
            return json!([SECTOR_STATUS_NA, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        };

        let s1_status = driver
            .lap_info
            .current_lap_sector1_time_in_ms
            .map(|sector1_time_in_ms| {
                sector_status(
                    sector1_time_in_ms,
                    session_best_sector1_ms,
                    personal_best_sector1_ms,
                    !driver.lap_info.current_lap_invalid.unwrap_or(false),
                )
            })
            .unwrap_or(SECTOR_STATUS_NA);
        if current_sector == "SECTOR2" {
            return json!([s1_status, SECTOR_STATUS_NA, SECTOR_STATUS_NA]);
        }

        let s2_status = driver
            .lap_info
            .current_lap_sector2_time_in_ms
            .map(|sector2_time_in_ms| {
                sector_status(
                    sector2_time_in_ms,
                    session_best_sector2_ms,
                    personal_best_sector2_ms,
                    !driver.lap_info.current_lap_invalid.unwrap_or(false),
                )
            })
            .unwrap_or(SECTOR_STATUS_NA);
        json!([s1_status, s2_status, SECTOR_STATUS_NA])
    }

    fn time_trial_json(&self) -> Value {
        let tt_packet = self.time_trial.packet.as_ref();
        json!({
            "current-lap": self.player_index.and_then(|index| self.driver(index as usize)).and_then(|driver| driver.lap_info.current_lap),
            "session-history": self.player_index.and_then(|index| self.driver(index as usize)).and_then(|driver| driver.packet_copies.session_history.as_ref()),
            "tt-data": tt_packet,
            "tt-setups": self.time_trial_setups_json(tt_packet),
            "irl-pole-lap": self.session_info.most_recent_pole_lap
        })
    }

    fn time_trial_setups_json(&self, packet: Option<&f1_types::PacketTimeTrialData>) -> Value {
        let Some(packet) = packet else {
            return json!({
                "personal-best-setup": Value::Null,
                "player-session-best-setup": Value::Null,
                "rival-session-best-setup": Value::Null,
            });
        };

        let mut personal_best_index = packet.personal_best_data_set.car_index;
        let player_session_best_index = packet.player_session_best_data_set.car_index;
        let rival_index = packet.rival_session_best_data_set.car_index;

        // Match the Python behavior: if PB equals session best, use the session-best car index.
        if packet.player_session_best_data_set.lap_time_in_ms
            == packet.personal_best_data_set.lap_time_in_ms
        {
            personal_best_index = player_session_best_index;
        }

        json!({
            "personal-best-setup": self.driver_car_setup_json(personal_best_index),
            "player-session-best-setup": self.driver_car_setup_json(player_session_best_index),
            "rival-session-best-setup": self.driver_car_setup_json(rival_index),
        })
    }

    fn driver_car_setup_json(&self, index: u8) -> Value {
        self.driver(index as usize)
            .and_then(|driver| driver.packet_copies.car_setup.as_ref())
            .map(|setup| serde_json::to_value(setup).unwrap_or(Value::Null))
            .unwrap_or(Value::Null)
    }

    fn overtake_records_json(&self) -> Vec<Value> {
        self.events
            .overtakes
            .iter()
            .enumerate()
            .map(|(overtake_id, overtake)| {
                json!({
                    "overtaking-driver-index": overtake.overtaking_vehicle_index,
                    "overtaking-driver-name": self.driver(overtake.overtaking_vehicle_index as usize).and_then(|driver| driver.driver_info.name.clone()),
                    "overtaking-driver-lap": overtake.overtaking_lap,
                    "overtaken-driver-index": overtake.overtaken_vehicle_index,
                    "overtaken-driver-name": self.driver(overtake.overtaken_vehicle_index as usize).and_then(|driver| driver.driver_info.name.clone()),
                    "overtaken-driver-lap": overtake.overtaken_lap,
                    "overtake-id": overtake_id,
                })
            })
            .collect()
    }

    fn overtakes_summary_json(&self, overtake_records: &[Value]) -> Value {
        let mut overtaking_counts: BTreeMap<String, usize> = BTreeMap::new();
        let mut overtaken_counts: BTreeMap<String, usize> = BTreeMap::new();
        let mut rivalry_records: BTreeMap<(String, String), Vec<Value>> = BTreeMap::new();

        for record in overtake_records {
            let overtaking_name = record["overtaking-driver-name"].as_str();
            let overtaken_name = record["overtaken-driver-name"].as_str();
            let (Some(overtaking_name), Some(overtaken_name)) = (overtaking_name, overtaken_name)
            else {
                continue;
            };

            *overtaking_counts
                .entry(overtaking_name.to_string())
                .or_default() += 1;
            *overtaken_counts
                .entry(overtaken_name.to_string())
                .or_default() += 1;

            let mut rivalry_pair = [overtaking_name.to_string(), overtaken_name.to_string()];
            rivalry_pair.sort();
            rivalry_records
                .entry((rivalry_pair[0].clone(), rivalry_pair[1].clone()))
                .or_default()
                .push(json!({
                    "overtaking-driver-name": overtaking_name,
                    "overtaking-driver-lap": record["overtaking-driver-lap"],
                    "overtaken-driver-name": overtaken_name,
                    "overtaken-driver-lap": record["overtaken-driver-lap"],
                }));
        }

        let (most_overtakes_drivers, most_overtakes_count) =
            self.max_count_names_json(&overtaking_counts);
        let (most_overtaken_drivers, most_overtaken_count) =
            self.max_count_names_json(&overtaken_counts);
        let most_heated_rivalries = if rivalry_records.is_empty() {
            Vec::new()
        } else {
            let max_rivalry_count = rivalry_records.values().map(Vec::len).max().unwrap_or(0);
            rivalry_records
                .into_iter()
                .filter(|(_, records)| records.len() == max_rivalry_count)
                .map(|((driver1, driver2), overtakes)| {
                    json!({
                        "driver1": driver1,
                        "driver2": driver2,
                        "overtakes": overtakes,
                    })
                })
                .collect::<Vec<_>>()
        };

        json!({
            "records": overtake_records,
            "number-of-overtakes": overtake_records.len(),
            "number-of-times-overtaken": most_overtaken_count,
            "most-overtakes": {
                "drivers": most_overtakes_drivers,
                "count": most_overtakes_count,
            },
            "most-overtaken": {
                "drivers": most_overtaken_drivers,
                "count": most_overtaken_count,
            },
            "most-heated-rivalries": most_heated_rivalries,
        })
    }

    fn max_count_names_json(&self, counts: &BTreeMap<String, usize>) -> (Vec<String>, usize) {
        let max_count = counts.values().copied().max().unwrap_or(0);
        if max_count == 0 {
            return (Vec::new(), 0);
        }

        (
            counts
                .iter()
                .filter(|(_, count)| **count == max_count)
                .map(|(name, _)| name.clone())
                .collect(),
            max_count,
        )
    }

    fn tyre_stats_json(&self) -> Value {
        #[derive(Clone)]
        struct TyreRecord {
            driver_name: String,
            value: f64,
        }

        #[derive(Default)]
        struct CompoundTyreStats {
            longest_tyre_stint: Option<TyreRecord>,
            lowest_tyre_wear_per_lap: Option<TyreRecord>,
            highest_tyre_wear: Option<TyreRecord>,
        }

        let mut stats_by_compound: BTreeMap<String, CompoundTyreStats> = BTreeMap::new();

        for driver in self.drivers.iter().filter(|driver| driver.is_valid()) {
            if driver.driver_info.telemetry_setting_raw != Some(1) {
                continue;
            }
            let Some(driver_name) = driver.driver_info.name.as_ref() else {
                continue;
            };

            for tyre_set in &driver.tyre_info.tyre_sets {
                let stint_length = f64::from(tyre_set.life_span);
                if stint_length <= 0.0 {
                    continue;
                }

                let compound = format!(
                    "{} - {}",
                    tyre_set.actual_tyre_compound, tyre_set.visual_tyre_compound
                );
                let wear = f64::from(tyre_set.wear);
                let wear_per_lap = wear / stint_length;
                let entry = stats_by_compound.entry(compound).or_default();

                if entry
                    .longest_tyre_stint
                    .as_ref()
                    .is_none_or(|current| stint_length > current.value)
                {
                    entry.longest_tyre_stint = Some(TyreRecord {
                        driver_name: driver_name.clone(),
                        value: stint_length,
                    });
                }

                if wear > 0.0
                    && entry
                        .lowest_tyre_wear_per_lap
                        .as_ref()
                        .is_none_or(|current| wear_per_lap < current.value)
                {
                    entry.lowest_tyre_wear_per_lap = Some(TyreRecord {
                        driver_name: driver_name.clone(),
                        value: wear_per_lap,
                    });
                }

                if entry
                    .highest_tyre_wear
                    .as_ref()
                    .is_none_or(|current| wear > current.value)
                {
                    entry.highest_tyre_wear = Some(TyreRecord {
                        driver_name: driver_name.clone(),
                        value: wear,
                    });
                }
            }
        }

        Value::Object(
            stats_by_compound
                .into_iter()
                .map(|(compound, stats)| {
                    (
                        compound,
                        json!({
                            "longest-tyre-stint": stats.longest_tyre_stint.as_ref().map(|record| {
                                json!({
                                    "value": record.value,
                                    "driver-name": record.driver_name,
                                })
                            }),
                            "lowest-tyre-wear-per-lap": stats.lowest_tyre_wear_per_lap.as_ref().map(|record| {
                                json!({
                                    "value": record.value,
                                    "driver-name": record.driver_name,
                                })
                            }),
                            "highest-tyre-wear": stats.highest_tyre_wear.as_ref().map(|record| {
                                json!({
                                    "value": record.value,
                                    "driver-name": record.driver_name,
                                })
                            }),
                        }),
                    )
                })
                .collect(),
        )
    }

    fn driver_lap_time_history_json(&self, driver: &DriverState) -> Value {
        let Some(session_history) = driver.packet_copies.session_history.as_ref() else {
            return json!({
                "fastest-lap-number": Value::Null,
                "fastest-s1-lap-number": Value::Null,
                "fastest-s2-lap-number": Value::Null,
                "fastest-s3-lap-number": Value::Null,
                "global-fastest-lap-ms": self.fastest_index.and_then(|index| self.driver(index as usize)).and_then(|driver| driver.lap_info.best_lap_time_in_ms),
                "global-fastest-s1-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector1_time_in_ms)),
                "global-fastest-s2-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector2_time_in_ms)),
                "global-fastest-s3-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector3_time_in_ms)),
                "lap-history-data": Value::Array(Vec::new()),
            });
        };

        let lap_history_data = session_history
            .lap_history_data
            .iter()
            .take(session_history.num_laps as usize)
            .enumerate()
            .map(|(lap_index, lap)| {
                let lap_number = (lap_index + 1) as u8;
                let mut value = serde_json::to_value(lap).unwrap_or_else(|_| Value::Null);
                if let Some(object) = value.as_object_mut() {
                    object.insert(
                        "tyre-set-info".to_string(),
                        snapshot_tyre_set_info_value(driver, lap_number),
                    );
                    object.insert(
                        "top-speed-kmph".to_string(),
                        json!(
                            driver
                                .per_lap_snapshots
                                .get(&lap_number)
                                .and_then(|snapshot| snapshot.top_speed_kph)
                        ),
                    );
                    object.insert("lap-number".to_string(), json!(lap_number));
                }
                value
            })
            .collect::<Vec<_>>();

        json!({
            "fastest-lap-number": if session_history.best_lap_time_lap_num > 0 { Some(session_history.best_lap_time_lap_num) } else { None::<u8> },
            "fastest-s1-lap-number": if session_history.best_sector1_lap_num > 0 { Some(session_history.best_sector1_lap_num) } else { None::<u8> },
            "fastest-s2-lap-number": if session_history.best_sector2_lap_num > 0 { Some(session_history.best_sector2_lap_num) } else { None::<u8> },
            "fastest-s3-lap-number": if session_history.best_sector3_lap_num > 0 { Some(session_history.best_sector3_lap_num) } else { None::<u8> },
            "global-fastest-lap-ms": self.fastest_index.and_then(|index| self.driver(index as usize)).and_then(|driver| driver.lap_info.best_lap_time_in_ms),
            "global-fastest-s1-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector1_time_in_ms)),
            "global-fastest-s2-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector2_time_in_ms)),
            "global-fastest-s3-ms": self.fastest_sector_ms(|driver| driver.lap_info.best_lap_history_data.as_ref().map(|lap| lap.sector3_time_in_ms)),
            "lap-history-data": lap_history_data,
        })
    }

    fn driver_tyre_set_history_json(&self, driver: &DriverState) -> Value {
        let Some(session_history) = driver.packet_copies.session_history.as_ref() else {
            return Value::Array(Vec::new());
        };

        let mut start_lap = 1u8;
        Value::Array(
            session_history
                .tyre_stints_history_data
                .iter()
                .take(session_history.num_tyre_stints as usize)
                .enumerate()
                .map(|(index, stint)| {
                    let end_lap = stint.end_lap.max(start_lap);
                    let snapshot = driver.per_lap_snapshots.get(&end_lap);
                    let wear = snapshot
                        .and_then(|snapshot| snapshot.car_damage.as_ref())
                        .map(|damage| damage.tyres_wear);
                    let fitted_index = snapshot
                        .and_then(|snapshot| snapshot.tyre_sets.as_ref())
                        .and_then(|tyre_sets| {
                            (tyre_sets.fitted_index != u8::MAX).then_some(tyre_sets.fitted_index)
                        });
                    let tyre_set_data = snapshot
                        .and_then(|snapshot| snapshot.tyre_sets.as_ref())
                        .and_then(|tyre_sets| tyre_sets.fitted_tyre_set());
                    let tyre_wear_history =
                        snapshot_tyre_wear_history_value(driver, start_lap, end_lap);
                    let latest_average_wear = tyre_wear_history
                        .as_array()
                        .and_then(|history| history.last())
                        .and_then(|value| value.get("average"))
                        .and_then(Value::as_f64);
                    let value = json!({
                        "stint-number": index + 1,
                        "start-lap": start_lap,
                        "end-lap": end_lap,
                        "stint-length": end_lap.saturating_sub(start_lap).saturating_add(1),
                        "tyre-set-key": fitted_index.map(|fitted_index| {
                            format!("{}.{}", fitted_index, stint.tyre_actual_compound)
                        }),
                        "fitted-index": fitted_index,
                        "tyre-set-data": {
                            "actual-tyre-compound": tyre_set_data
                                .map(|tyre_set| tyre_set.actual_tyre_compound.to_string())
                                .unwrap_or_else(|| stint.tyre_actual_compound.to_string()),
                            "visual-tyre-compound": tyre_set_data
                                .map(|tyre_set| tyre_set.visual_tyre_compound.to_string())
                                .unwrap_or_else(|| stint.tyre_visual_compound.to_string()),
                            "wear": latest_average_wear,
                        },
                        "tyre-wear": {
                            "front-left": wear.map(|wear| wear[0]),
                            "front-right": wear.map(|wear| wear[1]),
                            "rear-left": wear.map(|wear| wear[2]),
                            "rear-right": wear.map(|wear| wear[3]),
                            "average": wear.map(|wear| wear.iter().sum::<f32>() / 4.0),
                        },
                        "tyre-wear-history": tyre_wear_history,
                    });
                    start_lap = end_lap.saturating_add(1);
                    value
                })
                .collect(),
        )
    }

    fn driver_per_lap_info_json(&self, driver: &DriverState) -> Value {
        if driver.per_lap_snapshots.is_empty() {
            return Value::Array(Vec::new());
        }

        Value::Array(
            driver
                .per_lap_snapshots
                .iter()
                .map(|(lap_number, snapshot)| {
                    json!({
                        "lap-number": lap_number,
                        "car-status-data": serializable_value(snapshot.car_status.as_ref()),
                        "car-damage-data": serializable_value(snapshot.car_damage.as_ref()),
                        "max-safety-car-status": snapshot.max_safety_car_status_raw.map(safety_car_status_label),
                        "tyre-sets-data": serializable_value(snapshot.tyre_sets.as_ref()),
                        "track-position": snapshot.track_position,
                        "top-speed-kmph": snapshot.top_speed_kph,
                        "ers-stats": {
                            "ers-harv-mguh-j": snapshot.ers_harvested_mguh_j,
                            "ers-harv-mguk-j": snapshot.ers_harvested_mguk_j,
                            "ers-deployed-j": snapshot.ers_deployed_j,
                        },
                        "lap-history-data": driver
                            .packet_copies
                            .session_history
                            .as_ref()
                            .and_then(|history| history.lap_history_data.get(usize::from(*lap_number).saturating_sub(1))),
                    })
                })
                .collect(),
        )
    }

    fn fastest_records_json(&self) -> Value {
        json!({
            "lap": self.fastest_lap_record_json(),
            "s1": self.fastest_sector_record_json(1),
            "s2": self.fastest_sector_record_json(2),
            "s3": self.fastest_sector_record_json(3),
        })
    }

    fn fastest_lap_record_json(&self) -> Value {
        self.fastest_index
            .and_then(|index| self.driver(index as usize))
            .and_then(|driver| {
                let lap_number = driver
                    .packet_copies
                    .session_history
                    .as_ref()
                    .and_then(|history| {
                        (history.best_lap_time_lap_num > 0).then_some(history.best_lap_time_lap_num)
                    });
                let time_ms = driver.lap_info.best_lap_time_in_ms?;
                Some(json!({
                    "driver-name": driver.driver_info.name,
                    "team-id": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                    "lap-number": lap_number,
                    "time-ms": time_ms,
                    "time-str": format_time_ms(time_ms),
                }))
            })
            .unwrap_or(Value::Null)
    }

    fn fastest_sector_record_json(&self, sector: u8) -> Value {
        self.drivers
            .iter()
            .filter(|driver| driver.is_valid())
            .filter_map(|driver| {
                let history = driver.packet_copies.session_history.as_ref()?;
                let best_lap_num = match sector {
                    1 if history.best_sector1_lap_num > 0 => Some(history.best_sector1_lap_num),
                    2 if history.best_sector2_lap_num > 0 => Some(history.best_sector2_lap_num),
                    3 if history.best_sector3_lap_num > 0 => Some(history.best_sector3_lap_num),
                    _ => None,
                }?;
                let lap = history.lap_history_data.get(best_lap_num.saturating_sub(1) as usize)?;
                let time_ms = match sector {
                    1 => lap.sector1_time_in_ms,
                    2 => lap.sector2_time_in_ms,
                    3 => lap.sector3_time_in_ms,
                    _ => 0,
                };
                (time_ms > 0).then_some((driver, best_lap_num, time_ms))
            })
            .min_by_key(|(_, _, time_ms)| *time_ms)
            .map(|(driver, lap_number, time_ms)| {
                json!({
                    "driver-name": driver.driver_info.name,
                    "team-id": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                    "lap-number": lap_number,
                    "time-ms": time_ms,
                    "time-str": format_sector_ms(time_ms),
                })
            })
            .unwrap_or(Value::Null)
    }

    fn fastest_sector_ms<F>(&self, selector: F) -> Option<u16>
    where
        F: Fn(&DriverState) -> Option<u16>,
    {
        self.drivers
            .iter()
            .filter(|driver| driver.is_valid())
            .filter_map(selector)
            .filter(|value| *value > 0)
            .min()
    }

    fn position_history_json(&self) -> Value {
        Value::Array(
            self.drivers
                .iter()
                .filter(|driver| {
                    driver.is_valid()
                        && (!driver.lap_positions.is_empty() || !driver.per_lap_snapshots.is_empty())
                })
                .map(|driver| {
                    let position_history = if !driver.lap_positions.is_empty() {
                        driver
                            .lap_positions
                            .iter()
                            .enumerate()
                            .map(|(lap_index, position)| {
                                json!({
                                    "lap-number": lap_index + 1,
                                    "position": position,
                                })
                            })
                            .collect::<Vec<_>>()
                    } else {
                        driver
                            .per_lap_snapshots
                            .iter()
                            .filter_map(|(lap_number, snapshot)| {
                                snapshot.track_position.map(|position| {
                                    json!({
                                        "lap-number": lap_number,
                                        "position": position,
                                    })
                                })
                            })
                            .collect::<Vec<_>>()
                    };
                    json!({
                        "name": driver.driver_info.name,
                        "team": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                        "driver-position-history": position_history,
                    })
                })
                .collect(),
        )
    }

    fn speed_trap_records_json(&self) -> Value {
        let mut records = self
            .drivers
            .iter()
            .filter(|driver| driver.is_valid())
            .filter_map(|driver| {
                driver.lap_info.speed_trap_fastest_speed.map(|speed| {
                    json!({
                        "name": driver.driver_info.name,
                        "team": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                        "speed-trap-record-kmph": speed,
                    })
                })
            })
            .collect::<Vec<_>>();

        records.sort_by(|left, right| {
            let left_value = left["speed-trap-record-kmph"].as_f64().unwrap_or(0.0);
            let right_value = right["speed-trap-record-kmph"].as_f64().unwrap_or(0.0);
            right_value
                .partial_cmp(&left_value)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        Value::Array(records)
    }

    fn tyre_stint_history_v2_json(&self) -> Value {
        let mut drivers = self
            .drivers
            .iter()
            .filter(|driver| driver.is_valid())
            .map(|driver| {
                json!({
                    "position": driver.driver_info.position,
                    "name": driver.driver_info.name,
                    "team": driver.driver_info.team_id_raw.map(|team_id| team_label(self.session_info.packet_format.unwrap_or(2025), team_id)),
                    "telemetry-setting": driver.driver_info.telemetry_setting_raw.map(telemetry_setting_label).unwrap_or("Restricted"),
                    "result-status": driver.driver_info.dnf_status_code.clone().unwrap_or_default(),
                    "tyre-stint-history": self.driver_tyre_set_history_json(driver),
                })
            })
            .collect::<Vec<_>>();

        drivers.sort_by_key(|driver| driver["position"].as_u64().unwrap_or(u64::MAX));
        Value::Array(drivers)
    }

    fn pace_driver_json(&self, driver: Option<&DriverState>) -> Value {
        let Some(driver) = driver else {
            return json!({
                "name": Value::Null,
                "lap-ms": Value::Null,
                "sector-1-ms": Value::Null,
                "sector-2-ms": Value::Null,
                "sector-3-ms": Value::Null,
                "ers": {
                    "ers-percent": Value::Null,
                    "ers-mode": Value::Null,
                    "ers-harvested-by-mguk-this-lap": Value::Null,
                    "ers-deployed-this-lap": Value::Null,
                },
            });
        };

        json!({
            "name": driver.driver_info.name,
            "lap-ms": driver.lap_info.last_lap_time_in_ms,
            "sector-1-ms": driver
                .packet_copies
                .session_history
                .as_ref()
                .and_then(|history| history.lap_history_data.last())
                .map(|lap| lap.sector1_time_in_ms),
            "sector-2-ms": driver
                .packet_copies
                .session_history
                .as_ref()
                .and_then(|history| history.lap_history_data.last())
                .map(|lap| lap.sector2_time_in_ms),
            "sector-3-ms": driver
                .packet_copies
                .session_history
                .as_ref()
                .and_then(|history| history.lap_history_data.last())
                .map(|lap| lap.sector3_time_in_ms),
            "ers": {
                "ers-percent": driver.car_info.ers_percent,
                "ers-mode": driver.packet_copies.car_status.as_ref().map(|status| status.ers_deploy_mode.to_string()),
                "ers-harvested-by-mguk-this-lap": driver.packet_copies.car_status.as_ref().map(|status| {
                    (status.ers_harvested_this_lap_mguk / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY) * 100.0
                }),
                "ers-deployed-this-lap": driver.packet_copies.car_status.as_ref().map(|status| {
                    (status.ers_deployed_this_lap / f1_types::packet_7_car_status_data::CarStatusData::MAX_ERS_STORE_ENERGY) * 100.0
                }),
            },
        })
    }
}
