use std::sync::mpsc::{Receiver, SyncSender, TryRecvError, TrySendError, sync_channel};
use std::sync::{Arc, RwLock};
use std::thread::{self, JoinHandle};

use serde_json::{Value, json};
use state::{DriverState, LapTyreWearSample, SessionState};

#[derive(Clone, Debug, Default)]
pub struct DerivedDriverState {
    pub tyre_wear_predictions: Option<Value>,
    pub fuel_info: Option<Value>,
}

#[derive(Clone, Debug)]
pub struct DerivedState {
    pub source_packet_count: u64,
    pub drivers: Vec<DerivedDriverState>,
}

impl Default for DerivedState {
    fn default() -> Self {
        Self {
            source_packet_count: 0,
            drivers: vec![DerivedDriverState::default(); SessionState::MAX_DRIVERS],
        }
    }
}

impl DerivedState {
    pub fn driver(&self, index: usize) -> Option<&DerivedDriverState> {
        self.drivers.get(index)
    }
}

#[derive(Clone, Default)]
pub struct SharedDerivedState(Arc<RwLock<DerivedState>>);

impl SharedDerivedState {
    pub fn new() -> Self {
        Self(Arc::new(RwLock::new(DerivedState::default())))
    }

    pub fn snapshot(&self) -> DerivedState {
        self.0.read().expect("derived state poisoned").clone()
    }

    fn replace(&self, state: DerivedState) {
        let mut guard = self.0.write().expect("derived state poisoned");
        *guard = state;
    }

    pub fn clear(&self) {
        self.replace(DerivedState::default());
    }
}

pub struct DerivedStateWorker {
    sender: SyncSender<SessionState>,
    _thread: JoinHandle<()>,
}

impl DerivedStateWorker {
    pub fn start(shared_state: SharedDerivedState) -> Self {
        let (sender, receiver) = sync_channel(1);
        let thread = thread::Builder::new()
            .name("png-derived-state".to_string())
            .spawn(move || derived_worker_loop(receiver, shared_state))
            .expect("spawn derived state worker");
        Self {
            sender,
            _thread: thread,
        }
    }

    pub fn try_schedule(&self, snapshot: SessionState) {
        match self.sender.try_send(snapshot) {
            Ok(()) | Err(TrySendError::Full(_)) | Err(TrySendError::Disconnected(_)) => {}
        }
    }
}

pub fn should_refresh_derived_state(packet: &f1_types::F1Packet) -> bool {
    matches!(
        packet,
        f1_types::F1Packet::Session(_)
            | f1_types::F1Packet::LapData(_)
            | f1_types::F1Packet::CarStatus(_)
            | f1_types::F1Packet::CarDamage(_)
            | f1_types::F1Packet::TyreSets(_)
            | f1_types::F1Packet::FinalClassification(_)
            | f1_types::F1Packet::Event(_)
    )
}

fn derived_worker_loop(receiver: Receiver<SessionState>, shared_state: SharedDerivedState) {
    while let Ok(mut snapshot) = receiver.recv() {
        loop {
            match receiver.try_recv() {
                Ok(next_snapshot) => snapshot = next_snapshot,
                Err(TryRecvError::Empty) => break,
                Err(TryRecvError::Disconnected) => break,
            }
        }
        shared_state.replace(compute_derived_state(&snapshot));
    }
}

pub fn compute_derived_state(session_state: &SessionState) -> DerivedState {
    let mut derived_state = DerivedState {
        source_packet_count: session_state.packet_count,
        ..DerivedState::default()
    };

    for driver in &session_state.drivers {
        derived_state.drivers[driver.index] = DerivedDriverState {
            tyre_wear_predictions: Some(compute_tyre_wear_predictions(session_state, driver)),
            fuel_info: Some(compute_fuel_info(session_state, driver)),
        };
    }

    derived_state
}

pub fn merge_periodic_update_json(value: &mut Value, derived_state: &DerivedState) {
    let Some(table_entries) = value.get_mut("table-entries").and_then(Value::as_array_mut) else {
        return;
    };

    for table_entry in table_entries {
        let index = table_entry
            .get("driver-info")
            .and_then(Value::as_object)
            .and_then(|driver_info| driver_info.get("index"))
            .and_then(Value::as_u64)
            .map(|index| index as usize);
        let Some(driver_index) = index else {
            continue;
        };
        let Some(derived_driver) = derived_state.driver(driver_index) else {
            continue;
        };

        if let Some(predictions) = derived_driver.tyre_wear_predictions.as_ref() {
            set_nested_value(
                table_entry,
                &["tyre-info", "wear-prediction"],
                predictions.clone(),
            );
        }
        if let Some(fuel_info) = derived_driver.fuel_info.as_ref() {
            set_nested_value(table_entry, &["fuel-info"], fuel_info.clone());
        }
    }
}

pub fn merge_driver_info_json(value: &mut Value, index: usize, derived_state: &DerivedState) {
    let Some(derived_driver) = derived_state.driver(index) else {
        return;
    };

    if let Some(predictions) = derived_driver.tyre_wear_predictions.as_ref() {
        set_nested_value(value, &["tyre-wear-predictions"], predictions.clone());
    }
    if let Some(fuel_info) = derived_driver.fuel_info.as_ref() {
        set_nested_value(value, &["fuel-info"], fuel_info.clone());
    }
}

fn set_nested_value(root: &mut Value, path: &[&str], new_value: Value) {
    let mut current = root;
    for segment in &path[..path.len().saturating_sub(1)] {
        let Some(object) = current.as_object_mut() else {
            return;
        };
        let Some(next) = object.get_mut(*segment) else {
            return;
        };
        current = next;
    }

    if let Some(last) = path.last() {
        if let Some(object) = current.as_object_mut() {
            object.insert((*last).to_string(), new_value);
        }
    }
}

fn compute_tyre_wear_predictions(session_state: &SessionState, driver: &DriverState) -> Value {
    let total_laps = session_total_laps(session_state);
    let selected_pit_stop_lap = session_state.next_pit_stop_window_lap();
    let current_tyre_set_key = driver.tyre_info.fitted_tyre_set_key.as_deref();
    let current_stint = current_stint_samples(&driver.tyre_wear_samples, current_tyre_set_key);
    let racing_samples = current_stint
        .iter()
        .filter(|sample| sample.is_racing_lap)
        .copied()
        .collect::<Vec<_>>();

    let (fl_rate, fl_intercept) = linear_regression(
        &racing_samples
            .iter()
            .map(|sample| (sample.lap_number, sample.wear[0]))
            .collect::<Vec<_>>(),
    );
    let (fr_rate, fr_intercept) = linear_regression(
        &racing_samples
            .iter()
            .map(|sample| (sample.lap_number, sample.wear[1]))
            .collect::<Vec<_>>(),
    );
    let (rl_rate, rl_intercept) = linear_regression(
        &racing_samples
            .iter()
            .map(|sample| (sample.lap_number, sample.wear[2]))
            .collect::<Vec<_>>(),
    );
    let (rr_rate, rr_intercept) = linear_regression(
        &racing_samples
            .iter()
            .map(|sample| (sample.lap_number, sample.wear[3]))
            .collect::<Vec<_>>(),
    );

    let mut predictions = Vec::new();
    if let (Some(total_laps), Some(last_sample)) = (total_laps, current_stint.last().copied()) {
        if racing_samples.len() > 1 {
            if last_sample.lap_number >= total_laps {
                predictions.push(tyre_prediction_value(
                    last_sample.lap_number,
                    last_sample.wear,
                ));
            } else {
                let mut previous_wear = last_sample.wear;
                for lap_number in (last_sample.lap_number + 1)..=total_laps {
                    let predicted_wear = [
                        clamp_wear(
                            fl_rate * f32::from(lap_number) + fl_intercept,
                            previous_wear[0],
                        ),
                        clamp_wear(
                            fr_rate * f32::from(lap_number) + fr_intercept,
                            previous_wear[1],
                        ),
                        clamp_wear(
                            rl_rate * f32::from(lap_number) + rl_intercept,
                            previous_wear[2],
                        ),
                        clamp_wear(
                            rr_rate * f32::from(lap_number) + rr_intercept,
                            previous_wear[3],
                        ),
                    ];
                    previous_wear = predicted_wear;
                    predictions.push(tyre_prediction_value(lap_number, predicted_wear));
                }
            }
        }
    }

    json!({
        "status": !predictions.is_empty(),
        "desc": if predictions.is_empty() {
            "Insufficient data for extrapolation"
        } else {
            "Data is sufficient for extrapolation"
        },
        "predictions": predictions,
        "rate": {
            "front-left": fl_rate,
            "front-right": fr_rate,
            "rear-left": rl_rate,
            "rear-right": rr_rate,
        },
        "selected-pit-stop-lap": selected_pit_stop_lap,
    })
}

fn compute_fuel_info(session_state: &SessionState, driver: &DriverState) -> Value {
    let car_status = driver.packet_copies.car_status.as_ref();
    let total_laps = session_total_laps(session_state).map(f32::from);
    let racing_samples = driver
        .fuel_samples
        .iter()
        .filter(|sample| sample.is_racing_lap)
        .collect::<Vec<_>>();

    let curr_fuel_rate = compute_current_fuel_rate(&racing_samples);
    let last_lap_fuel_used = driver
        .fuel_samples
        .windows(2)
        .last()
        .map(|window| window[0].fuel_remaining_kg - window[1].fuel_remaining_kg);

    let current_fuel = car_status.map(|status| status.fuel_in_tank);
    let current_lap = driver.lap_info.current_lap.map(f32::from);
    let laps_left = match (total_laps, current_lap) {
        (Some(total_laps), Some(current_lap)) => Some((total_laps - current_lap).max(0.0)),
        _ => None,
    };

    let target_fuel_rate = match (current_fuel, laps_left) {
        (Some(current_fuel), Some(laps_left)) if laps_left > 0.0 => {
            Some((current_fuel - f1_types::CarStatusData::MIN_FUEL_KG) / laps_left)
        }
        _ => None,
    };
    let surplus_laps_png = match (current_fuel, laps_left, curr_fuel_rate) {
        (Some(current_fuel), Some(laps_left), Some(curr_fuel_rate)) if curr_fuel_rate > 0.0 => {
            Some(
                ((current_fuel - f1_types::CarStatusData::MIN_FUEL_KG) / curr_fuel_rate)
                    - laps_left,
            )
        }
        _ => None,
    };
    let target_fuel_rate_next_lap = match (target_fuel_rate, curr_fuel_rate) {
        (Some(target_fuel_rate), Some(curr_fuel_rate)) => {
            Some(target_fuel_rate - ((curr_fuel_rate - target_fuel_rate) * 0.5))
        }
        (Some(target_fuel_rate), None) => Some(target_fuel_rate),
        _ => None,
    };

    json!({
        "fuel-capacity": car_status.map(|status| status.fuel_capacity),
        "fuel-mix": car_status.map(|status| status.fuel_mix.to_string()),
        "fuel-remaining-laps": car_status.map(|status| status.fuel_remaining_laps),
        "fuel-in-tank": current_fuel,
        "remaining-fuel": current_fuel,
        "curr-fuel-rate": curr_fuel_rate,
        "last-lap-fuel-used": last_lap_fuel_used,
        "target-fuel-rate-average": target_fuel_rate,
        "target-fuel-rate-next-lap": target_fuel_rate_next_lap,
        "surplus-laps-png": surplus_laps_png,
        "surplus-laps-game": car_status.map(|status| status.fuel_remaining_laps),
    })
}

fn current_stint_samples<'a>(
    samples: &'a [LapTyreWearSample],
    current_tyre_set_key: Option<&str>,
) -> Vec<&'a LapTyreWearSample> {
    let Some(current_tyre_set_key) = current_tyre_set_key else {
        return samples.iter().collect();
    };

    let mut selected = Vec::new();
    for sample in samples.iter().rev() {
        if sample.tyre_set_key.as_deref() == Some(current_tyre_set_key) {
            selected.push(sample);
        } else if !selected.is_empty() {
            break;
        }
    }
    selected.reverse();
    selected
}

fn compute_current_fuel_rate(samples: &[&state::FuelSample]) -> Option<f32> {
    if samples.len() <= 1 {
        return None;
    }

    let mut total_fuel_used = 0.0;
    let mut valid_pair_count = 0usize;
    for window in samples.windows(2) {
        let previous = window[0];
        let current = window[1];
        if current.lap_number == previous.lap_number + 1 {
            total_fuel_used += previous.fuel_remaining_kg - current.fuel_remaining_kg;
            valid_pair_count += 1;
        }
    }

    if valid_pair_count == 0 {
        None
    } else {
        Some(total_fuel_used / valid_pair_count as f32)
    }
}

fn session_total_laps(session_state: &SessionState) -> Option<u8> {
    session_state
        .session_info
        .total_laps
        .filter(|total_laps| *total_laps > 0)
        .map(|total_laps| total_laps as u8)
}

fn tyre_prediction_value(lap_number: u8, wear: [f32; 4]) -> Value {
    json!({
        "lap-number": lap_number,
        "front-left-wear": wear[0],
        "front-right-wear": wear[1],
        "rear-left-wear": wear[2],
        "rear-right-wear": wear[3],
        "average": wear.iter().sum::<f32>() / 4.0,
        "desc": Value::Null,
    })
}

fn linear_regression(points: &[(u8, f32)]) -> (f32, f32) {
    if points.len() <= 1 {
        return (0.0, points.first().map(|(_, y)| *y).unwrap_or(0.0));
    }

    let count = points.len() as f32;
    let mean_x = points.iter().map(|(x, _)| f32::from(*x)).sum::<f32>() / count;
    let mean_y = points.iter().map(|(_, y)| *y).sum::<f32>() / count;
    let numerator = points
        .iter()
        .map(|(x, y)| (f32::from(*x) - mean_x) * (*y - mean_y))
        .sum::<f32>();
    let denominator = points
        .iter()
        .map(|(x, _)| (f32::from(*x) - mean_x).powi(2))
        .sum::<f32>();

    let slope = if denominator == 0.0 {
        0.0
    } else {
        numerator / denominator
    }
    .max(0.0);
    let intercept = mean_y - (slope * mean_x);
    (slope, intercept)
}

fn clamp_wear(predicted_wear: f32, current_wear: f32) -> f32 {
    predicted_wear.max(0.0).max(current_wear)
}

#[cfg(test)]
mod tests {
    use super::{compute_derived_state, merge_driver_info_json, merge_periodic_update_json};
    use f1_types::packet_7_car_status_data::{ErsDeployMode, FuelMix, VehicleFiaFlags};
    use f1_types::{
        ActualTyreCompound, CarDamageData, CarStatusData, F1Packet, F1PacketType, LapData,
        PacketCarDamageData, PacketCarStatusData, PacketHeader, PacketLapData,
        PacketParticipantsData, PacketSessionData, PacketTyreSetsData, ParticipantData, PitStatus,
        Sector, SessionType24, TractionControlAssistMode, TyreSetData, VisualTyreCompound,
    };
    use serde_json::Value;
    use state::SessionState;

    fn header(packet_type: F1PacketType, frame: u32) -> PacketHeader {
        PacketHeader::from_values(
            2025,
            25,
            1,
            0,
            1,
            packet_type,
            500,
            0.0,
            frame,
            frame,
            1,
            255,
        )
    }

    fn sample_session_packet() -> PacketSessionData {
        PacketSessionData {
            header: header(F1PacketType::Session, 1),
            weather_raw: 0,
            track_temperature: 30,
            air_temperature: 22,
            total_laps: 10,
            track_length: 5400,
            session_type_raw: SessionType24::RACE as u8,
            track_id_raw: 7,
            formula_raw: 0,
            session_time_left: 3600,
            session_duration: 7200,
            pit_speed_limit: 80,
            game_paused: 0,
            is_spectating: false,
            spectator_car_index: 255,
            sli_pro_native_support: 0,
            num_marshal_zones: 0,
            marshal_zones: vec![],
            safety_car_status_raw: 0,
            network_game: 1,
            num_weather_forecast_samples: 0,
            weather_forecast_samples: vec![],
            forecast_accuracy: 0,
            ai_difficulty: 100,
            season_link_identifier: 1,
            weekend_link_identifier: 2,
            session_link_identifier: 3,
            pit_stop_window_ideal_lap: 5,
            pit_stop_window_latest_lap: 8,
            pit_stop_rejoin_position: 5,
            steering_assist: 0,
            braking_assist: 0,
            gearbox_assist_raw: 0,
            pit_assist: 0,
            pit_release_assist: 0,
            ers_assist: 0,
            drs_assist: 0,
            dynamic_racing_line: 0,
            dynamic_racing_line_type: 0,
            game_mode_raw: 26,
            rule_set_raw: 1,
            time_of_day: 0,
            session_length_raw: 4,
            speed_units_lead_player: 0,
            temperature_units_lead_player: 0,
            speed_units_secondary_player: 0,
            temperature_units_secondary_player: 0,
            num_safety_car_periods: 0,
            num_virtual_safety_car_periods: 0,
            num_red_flag_periods: 0,
            equal_car_performance: 0,
            recovery_mode_raw: 0,
            flashback_limit_raw: 0,
            surface_type_raw: 0,
            low_fuel_mode_raw: 0,
            race_starts_raw: 0,
            tyre_temperature_mode_raw: 0,
            pit_lane_tyre_sim: 0,
            car_damage_raw: 0,
            car_damage_rate_raw: 0,
            collisions_raw: 0,
            collisions_off_for_first_lap_only: 0,
            mp_unsafe_pit_release: 0,
            mp_off_for_griefing: 0,
            corner_cutting_stringency_raw: 0,
            parc_ferme_rules: 0,
            pit_stop_experience_raw: 0,
            safety_car_setting_raw: 0,
            safety_car_experience_raw: 0,
            formation_lap: 0,
            formation_lap_experience_raw: 0,
            red_flags_setting_raw: 0,
            affects_license_level_solo: 0,
            affects_license_level_mp: 0,
            num_sessions_in_weekend: 0,
            weekend_structure: vec![],
            sector2_lap_distance_start: 1800.0,
            sector3_lap_distance_start: 3600.0,
            raw_section5_2025: Some([0; 45]),
        }
    }

    fn participants_packet() -> PacketParticipantsData {
        let mut participants = Vec::new();
        for index in 0..PacketParticipantsData::MAX_PARTICIPANTS {
            participants.push(ParticipantData::from_values(
                2025,
                false,
                index as u8,
                index as u8,
                (index % 10) as u8,
                false,
                (index + 1) as u8,
                10,
                format!("Driver {index}"),
                1,
                true,
                1,
                0,
                0,
                vec![],
            ));
        }
        PacketParticipantsData::from_values(header(F1PacketType::Participants, 2), 22, participants)
    }

    fn car_status_packet(frame: u32, fuel_in_tank: f32, tyre_age_laps: u8) -> PacketCarStatusData {
        PacketCarStatusData::from_values(
            header(F1PacketType::CarStatus, frame),
            vec![
                CarStatusData::from_values(
                    TractionControlAssistMode::Off,
                    false,
                    FuelMix::Lean,
                    50,
                    false,
                    fuel_in_tank,
                    100.0,
                    fuel_in_tank / 2.0,
                    12_000,
                    4_000,
                    tyre_age_laps,
                    1,
                    100,
                    ActualTyreCompound::C3,
                    VisualTyreCompound::Soft,
                    8,
                    VehicleFiaFlags::None,
                    0.0,
                    0.0,
                    2_000_000.0,
                    ErsDeployMode::Overtake,
                    100.0,
                    50.0,
                    80.0,
                    false,
                );
                22
            ],
        )
    }

    fn car_damage_packet(frame: u32, base_wear: f32) -> PacketCarDamageData {
        PacketCarDamageData::from_values(
            header(F1PacketType::CarDamage, frame),
            vec![
                CarDamageData::from_values(
                    2025,
                    [base_wear, base_wear + 1.0, base_wear + 2.0, base_wear + 3.0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    false,
                    false,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    false,
                    false,
                );
                22
            ],
        )
    }

    fn tyre_sets_packet(frame: u32) -> PacketTyreSetsData {
        PacketTyreSetsData::from_values(
            header(F1PacketType::TyreSets, frame),
            0,
            vec![
                TyreSetData::from_values(
                    2025,
                    ActualTyreCompound::C3,
                    VisualTyreCompound::Soft,
                    0,
                    true,
                    1,
                    0,
                    0,
                    0,
                    false,
                );
                20
            ],
            0,
        )
    }

    fn lap_packet(frame: u32, current_lap: u8) -> PacketLapData {
        let mut laps = Vec::new();
        for index in 0..PacketLapData::MAX_CARS {
            laps.push(LapData::from_values(
                2025,
                90_000 + index as u32,
                10_000 + index as u32,
                30_000,
                0,
                30_000,
                0,
                500,
                0,
                1_000,
                0,
                100.0 + index as f32,
                500.0 + index as f32,
                1.5,
                (index + 1) as u8,
                current_lap,
                PitStatus::None,
                1,
                Sector::Sector2,
                false,
                0,
                0,
                0,
                0,
                0,
                (index + 1) as u8,
                f1_types::DriverStatus::OnTrack,
                f1_types::ResultStatus::ACTIVE,
                false,
                0,
                0,
                0,
                325.0,
                4,
            ));
        }
        PacketLapData::from_values(header(F1PacketType::LapData, frame), laps, -1, -1)
    }

    #[test]
    fn derived_state_populates_tyre_and_fuel_outputs() {
        let mut state = SessionState::new();
        state.apply_packet(F1Packet::Session(sample_session_packet()));
        state.apply_packet(F1Packet::Participants(participants_packet()));
        state.apply_packet(F1Packet::TyreSets(tyre_sets_packet(3)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(4, 18.0, 1)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(5, 10.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(6, 2)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(7, 16.8, 2)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(8, 12.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(9, 3)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(10, 15.6, 3)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(11, 14.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(12, 4)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(13, 14.4, 4)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(14, 16.0)));

        let derived = compute_derived_state(&state);
        let driver = derived.driver(0).expect("driver 0 derived");
        let tyre_predictions = driver
            .tyre_wear_predictions
            .as_ref()
            .expect("tyre predictions");
        let fuel_info = driver.fuel_info.as_ref().expect("fuel info");

        assert_eq!(derived.source_packet_count, state.packet_count);
        assert_eq!(tyre_predictions["status"], Value::Bool(true));
        assert_eq!(tyre_predictions["selected-pit-stop-lap"], Value::from(5));
        assert!(
            tyre_predictions["predictions"]
                .as_array()
                .is_some_and(|predictions| !predictions.is_empty())
        );
        assert!(fuel_info["curr-fuel-rate"].as_f64().is_some());
        assert!(fuel_info["target-fuel-rate-average"].as_f64().is_some());
    }

    #[test]
    fn merge_helpers_replace_placeholder_frontend_fields() {
        let mut state = SessionState::new();
        state.apply_packet(F1Packet::Session(sample_session_packet()));
        state.apply_packet(F1Packet::Participants(participants_packet()));
        state.apply_packet(F1Packet::TyreSets(tyre_sets_packet(3)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(4, 18.0, 1)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(5, 10.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(6, 2)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(7, 16.8, 2)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(8, 12.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(9, 3)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(10, 15.6, 3)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(11, 14.0)));
        state.apply_packet(F1Packet::LapData(lap_packet(12, 4)));
        state.apply_packet(F1Packet::CarStatus(car_status_packet(13, 14.4, 4)));
        state.apply_packet(F1Packet::CarDamage(car_damage_packet(14, 16.0)));

        let derived = compute_derived_state(&state);
        let mut periodic_update = state.periodic_update_json();
        merge_periodic_update_json(&mut periodic_update, &derived);
        let mut driver_info = state.driver_info_json(0).expect("driver info");
        merge_driver_info_json(&mut driver_info, 0, &derived);

        assert_eq!(
            periodic_update["table-entries"][0]["tyre-info"]["wear-prediction"]["status"],
            Value::Bool(true)
        );
        assert_eq!(
            periodic_update["table-entries"][0]["tyre-info"]["wear-prediction"]["selected-pit-stop-lap"],
            Value::from(5)
        );
        assert!(
            periodic_update["table-entries"][0]["fuel-info"]["curr-fuel-rate"]
                .as_f64()
                .is_some()
        );
        assert_eq!(
            driver_info["tyre-wear-predictions"]["status"],
            Value::Bool(true)
        );
    }
}
