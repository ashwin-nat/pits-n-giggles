use std::collections::BTreeMap;

use f1_types::{
    ActualTyreCompound, CarDamageData, CarMotionData, CarSetupData, CarStatusData,
    CarTelemetryData, FinalClassificationData, LapData, LapHistoryData, PacketEventData,
    PacketFinalClassificationData, PacketSessionData, PacketSessionHistoryData,
    PacketTimeTrialData, PacketTyreSetsData, ParticipantData, ResultStatus, TimeTrialDataSet,
    TyreSetData, VisualTyreCompound, WeatherForecastSample,
};
use serde::Serialize;
use serde_json::Value;

use crate::delta::LapDeltaManager;

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct PacketCopies {
    pub lap_data: Option<LapData>,
    pub participant_data: Option<ParticipantData>,
    pub car_telemetry: Option<CarTelemetryData>,
    pub car_status: Option<CarStatusData>,
    pub car_damage: Option<CarDamageData>,
    pub session_history: Option<PacketSessionHistoryData>,
    pub tyre_sets: Option<PacketTyreSetsData>,
    pub final_classification: Option<FinalClassificationData>,
    pub motion: Option<CarMotionData>,
    pub car_setup: Option<CarSetupData>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct DriverInfoState {
    pub name: Option<String>,
    pub position: Option<u8>,
    pub grid_position: Option<u8>,
    pub team_id_raw: Option<u8>,
    pub is_player: bool,
    pub telemetry_setting_raw: Option<u8>,
    pub driver_number: Option<u8>,
    pub dnf_status_code: Option<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct LapInfoState {
    pub best_lap_time_in_ms: Option<u32>,
    pub best_lap_history_data: Option<LapHistoryData>,
    pub last_lap_history_data: Option<LapHistoryData>,
    pub best_lap_visual_tyre_compound: Option<VisualTyreCompound>,
    pub personal_best_sector1_time_in_ms: Option<u16>,
    pub personal_best_sector2_time_in_ms: Option<u16>,
    pub personal_best_sector3_time_in_ms: Option<u16>,
    pub last_lap_time_in_ms: Option<u32>,
    pub current_lap: Option<u8>,
    pub delta_to_car_in_front_ms: Option<u32>,
    pub delta_to_leader_ms: Option<u32>,
    pub top_speed_kph_this_lap: Option<u16>,
    pub top_speed_kph_overall: Option<u16>,
    pub speed_trap_fastest_speed: Option<f32>,
    pub current_lap_delta_ms: Option<i32>,
    pub is_pitting: Option<bool>,
    pub total_race_time: Option<f64>,
    pub result_status: Option<ResultStatus>,
    pub current_lap_sector1_time_in_ms: Option<u16>,
    pub current_lap_sector2_time_in_ms: Option<u16>,
    pub current_lap_sector3_time_in_ms: Option<u16>,
    pub current_lap_time_in_ms: Option<u32>,
    pub current_sector: Option<String>,
    pub current_lap_invalid: Option<bool>,
    pub current_driver_status: Option<String>,
    pub lap_distance: Option<f32>,
    pub total_distance: Option<f32>,
    pub safety_car_delta: Option<f32>,
    pub penalties: Option<u8>,
    pub total_warnings: Option<u8>,
    pub corner_cutting_warnings: Option<u8>,
    pub num_unserved_drive_through_pens: Option<u8>,
    pub num_unserved_stop_go_pens: Option<u8>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct TyreInfoState {
    pub tyre_age_laps: Option<u8>,
    pub visual_compound: Option<VisualTyreCompound>,
    pub actual_compound: Option<ActualTyreCompound>,
    pub average_inner_temperature: Option<f32>,
    pub average_surface_temperature: Option<f32>,
    pub wear: Option<[f32; 4]>,
    pub damage: Option<[u8; 4]>,
    pub fitted_index: Option<u8>,
    pub fitted_tyre_set_key: Option<String>,
    pub tyre_sets: Vec<TyreSetData>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct PitInfoState {
    pub pit_status: Option<String>,
    pub num_stops: Option<u8>,
    pub pit_lane_timer_active: Option<bool>,
    pub pit_lane_time_in_lane_ms: Option<u16>,
    pub pit_stop_timer_ms: Option<u16>,
    pub pit_stop_should_serve_pen: Option<u8>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct CarInfoState {
    pub ers_percent: Option<f32>,
    pub drs_activated: Option<bool>,
    pub drs_allowed: Option<bool>,
    pub drs_distance: Option<u16>,
    pub front_left_wing_damage: Option<u8>,
    pub front_right_wing_damage: Option<u8>,
    pub rear_wing_damage: Option<u8>,
    pub current_lap_ers_harvested_mguk_j: Option<f32>,
    pub current_lap_ers_harvested_mguh_j: Option<f32>,
    pub current_lap_ers_deployed_j: Option<f32>,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct LapTyreWearSample {
    pub lap_number: u8,
    pub wear: [f32; 4],
    pub is_racing_lap: bool,
    pub tyre_set_key: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct FuelSample {
    pub lap_number: u8,
    pub fuel_remaining_kg: f32,
    pub is_racing_lap: bool,
    pub tyre_set_key: Option<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct PerLapSnapshotState {
    pub car_status: Option<CarStatusData>,
    pub car_damage: Option<CarDamageData>,
    pub tyre_sets: Option<PacketTyreSetsData>,
    pub track_position: Option<u8>,
    pub top_speed_kph: Option<u16>,
    pub max_safety_car_status_raw: Option<u8>,
    pub ers_harvested_mguk_j: Option<f32>,
    pub ers_harvested_mguh_j: Option<f32>,
    pub ers_deployed_j: Option<f32>,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct DriverState {
    pub index: usize,
    pub driver_info: DriverInfoState,
    pub lap_info: LapInfoState,
    pub tyre_info: TyreInfoState,
    pub pit_info: PitInfoState,
    pub car_info: CarInfoState,
    pub packet_copies: PacketCopies,
    pub lap_positions: Vec<u8>,
    pub warning_penalty_history: Vec<Value>,
    pub tyre_wear_samples: Vec<LapTyreWearSample>,
    pub fuel_samples: Vec<FuelSample>,
    pub per_lap_snapshots: BTreeMap<u8, PerLapSnapshotState>,
    pub current_lap_max_safety_car_status_raw: Option<u8>,
    #[serde(skip_serializing)]
    pub delta_manager: LapDeltaManager,
}

impl DriverState {
    pub fn new(index: usize) -> Self {
        Self {
            index,
            driver_info: DriverInfoState::default(),
            lap_info: LapInfoState::default(),
            tyre_info: TyreInfoState::default(),
            pit_info: PitInfoState::default(),
            car_info: CarInfoState::default(),
            packet_copies: PacketCopies::default(),
            lap_positions: Vec::new(),
            warning_penalty_history: Vec::new(),
            tyre_wear_samples: Vec::new(),
            fuel_samples: Vec::new(),
            per_lap_snapshots: BTreeMap::new(),
            current_lap_max_safety_car_status_raw: None,
            delta_manager: LapDeltaManager::default(),
        }
    }

    pub fn is_valid(&self) -> bool {
        if matches!(
            self.lap_info.result_status,
            Some(ResultStatus::INVALID | ResultStatus::INACTIVE)
        ) {
            return false;
        }

        let has_valid_position = matches!(self.driver_info.position, Some(1..=22));
        let has_driver_info =
            self.driver_info.name.is_some() || self.driver_info.team_id_raw.is_some();
        has_valid_position && has_driver_info
    }
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct SessionInfoState {
    pub session_uid: Option<u64>,
    pub packet_format: Option<u16>,
    pub game_year: Option<u8>,
    pub total_laps: Option<i8>,
    pub track_length: Option<u16>,
    pub session_type_raw: Option<u8>,
    pub track_id_raw: Option<i8>,
    pub formula_raw: Option<u8>,
    pub session_time_left: Option<u16>,
    pub session_duration: Option<u16>,
    pub pit_speed_limit: Option<u8>,
    pub is_spectating: Option<bool>,
    pub spectator_car_index: Option<u8>,
    pub safety_car_status_raw: Option<u8>,
    pub weather_forecast_samples: Vec<WeatherForecastSample>,
    pub packet_session: Option<PacketSessionData>,
    pub packet_final_classification: Option<PacketFinalClassificationData>,
    pub most_recent_pole_lap: Option<MostRecentPoleLap>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct SessionEventsState {
    pub last_event: Option<PacketEventData>,
    pub collisions: Vec<(u8, u8)>,
    pub overtakes: Vec<OvertakeRecordState>,
    pub custom_markers: Vec<CustomMarkerEntry>,
    pub race_winner_index: Option<u8>,
    pub race_control_messages: Vec<Value>,
    pub next_message_id: u64,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct OvertakeRecordState {
    pub overtaking_vehicle_index: u8,
    pub overtaking_lap: Option<u8>,
    pub overtaken_vehicle_index: u8,
    pub overtaken_lap: Option<u8>,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct CustomMarkerEntry {
    pub track: String,
    #[serde(rename = "event-type")]
    pub event_type: String,
    pub lap: String,
    pub sector: String,
    #[serde(rename = "curr-lap-time")]
    pub curr_lap_time: String,
    #[serde(rename = "curr-lap-percentage")]
    pub curr_lap_percentage: String,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize)]
pub struct TimeTrialState {
    pub packet: Option<PacketTimeTrialData>,
    pub player_session_best: Option<TimeTrialDataSet>,
    pub personal_best: Option<TimeTrialDataSet>,
    pub rival_session_best: Option<TimeTrialDataSet>,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct MostRecentPoleLap {
    pub circuit: String,
    pub year: Option<u16>,
    #[serde(rename = "driver-name")]
    pub driver_name: Option<String>,
    #[serde(rename = "driver-num")]
    pub driver_num: Option<u8>,
    #[serde(rename = "team-name")]
    pub team_name: Option<String>,
    #[serde(rename = "lap-ms")]
    pub lap_ms: Option<u32>,
    #[serde(rename = "s1-ms")]
    pub s1_ms: Option<u32>,
    #[serde(rename = "s2-ms")]
    pub s2_ms: Option<u32>,
    #[serde(rename = "s3-ms")]
    pub s3_ms: Option<u32>,
    #[serde(rename = "speed-trap-kmph")]
    pub speed_trap_kmph: Option<u16>,
}
