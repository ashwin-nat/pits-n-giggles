use std::sync::mpsc::{Receiver, SyncSender, TryRecvError, TrySendError, sync_channel};
use std::thread::{self, JoinHandle};

use chrono::{Datelike, Utc};
use reqwest::blocking::Client;
use serde_json::Value;
use state::MostRecentPoleLap;

use crate::runtime::SharedSessionState;

#[derive(Clone, Debug, PartialEq)]
pub struct PoleLapRequest {
    pub session_uid: u64,
    pub packet_format: u16,
    pub track_id_raw: i8,
    pub formula_raw: u8,
    pub session_type_raw: u8,
}

pub struct ExternalMetadataWorker {
    sender: SyncSender<PoleLapRequest>,
    _thread: JoinHandle<()>,
}

impl ExternalMetadataWorker {
    pub fn start(shared_state: SharedSessionState) -> Self {
        let (sender, receiver) = sync_channel(1);
        let thread = thread::Builder::new()
            .name("png-openf1-metadata".to_string())
            .spawn(move || external_worker_loop(receiver, shared_state))
            .expect("spawn external metadata worker");
        Self {
            sender,
            _thread: thread,
        }
    }

    pub fn try_schedule(&self, request: PoleLapRequest) {
        match self.sender.try_send(request) {
            Ok(()) | Err(TrySendError::Full(_)) | Err(TrySendError::Disconnected(_)) => {}
        }
    }
}

fn external_worker_loop(receiver: Receiver<PoleLapRequest>, shared_state: SharedSessionState) {
    let client = Client::builder()
        .user_agent("pits-n-giggles-rust-backend")
        .timeout(std::time::Duration::from_secs(8))
        .build()
        .expect("build reqwest client");
    let mut last_request: Option<PoleLapRequest> = None;
    let mut last_result: Option<Option<MostRecentPoleLap>> = None;

    while let Ok(mut request) = receiver.recv() {
        loop {
            match receiver.try_recv() {
                Ok(next_request) => request = next_request,
                Err(TryRecvError::Empty) => break,
                Err(TryRecvError::Disconnected) => break,
            }
        }

        let result = if last_request.as_ref() == Some(&request) {
            last_result.clone().unwrap_or(None)
        } else {
            let fetched = fetch_most_recent_pole_lap(&client, &request);
            last_request = Some(request.clone());
            last_result = Some(fetched.clone());
            fetched
        };

        shared_state.with_write(|session_state| {
            if session_state.session_info.session_uid != Some(request.session_uid)
                || session_state.session_info.packet_format != Some(request.packet_format)
                || session_state.session_info.track_id_raw != Some(request.track_id_raw)
                || session_state.session_info.formula_raw != Some(request.formula_raw)
                || session_state.session_info.session_type_raw != Some(request.session_type_raw)
            {
                return;
            }
            session_state.session_info.most_recent_pole_lap = result;
        });
    }
}

fn fetch_most_recent_pole_lap(
    client: &Client,
    request: &PoleLapRequest,
) -> Option<MostRecentPoleLap> {
    if !should_fetch_pole_lap(
        request.packet_format,
        request.formula_raw,
        request.session_type_raw,
    ) {
        return None;
    }
    let circuit_key = openf1_circuit_key(request.track_id_raw)?;
    let circuit_label = track_label(request.track_id_raw).to_string();
    let current_year = Utc::now().year().clamp(0, i32::from(u16::MAX)) as u16;

    for year in (current_year.saturating_sub(2)..=current_year).rev() {
        let Some(quali_session_key) = fetch_qualifying_session_key(client, circuit_key, year)
        else {
            continue;
        };
        let Some(driver_number) = fetch_pole_driver_number(client, quali_session_key) else {
            continue;
        };
        let Some((driver_name, team_name)) =
            fetch_driver_details(client, quali_session_key, driver_number)
        else {
            continue;
        };
        let Some(fastest_lap) = fetch_fastest_lap(client, quali_session_key, driver_number) else {
            continue;
        };

        return Some(MostRecentPoleLap {
            circuit: circuit_label.clone(),
            year: Some(year),
            driver_name: Some(driver_name),
            driver_num: Some(driver_number),
            team_name: Some(team_name),
            lap_ms: seconds_field_ms(&fastest_lap, "lap_duration"),
            s1_ms: seconds_field_ms(&fastest_lap, "duration_sector_1"),
            s2_ms: seconds_field_ms(&fastest_lap, "duration_sector_2"),
            s3_ms: seconds_field_ms(&fastest_lap, "duration_sector_3"),
            speed_trap_kmph: fastest_lap
                .get("st_speed")
                .and_then(Value::as_u64)
                .and_then(|speed| u16::try_from(speed).ok()),
        });
    }

    None
}

fn should_fetch_pole_lap(packet_format: u16, formula_raw: u8, session_type_raw: u8) -> bool {
    let is_f1 = !matches!(formula_raw, 2 | 7);
    let is_time_trial = if packet_format == 2023 {
        session_type_raw == f1_types::SessionType23::TIME_TRIAL as u8
    } else {
        session_type_raw == f1_types::SessionType24::TIME_TRIAL as u8
    };
    is_f1 && is_time_trial
}

fn fetch_qualifying_session_key(client: &Client, circuit_key: u16, year: u16) -> Option<u64> {
    let sessions = openf1_request(
        client,
        "sessions",
        &[
            ("year", year.to_string()),
            ("circuit_key", circuit_key.to_string()),
        ],
    )?;
    sessions
        .as_array()?
        .iter()
        .find(|session| session.get("session_name").and_then(Value::as_str) == Some("Qualifying"))
        .and_then(|session| session.get("session_key").and_then(Value::as_u64))
}

fn fetch_pole_driver_number(client: &Client, session_key: u64) -> Option<u8> {
    let drivers = openf1_request(
        client,
        "starting_grid",
        &[
            ("session_key", session_key.to_string()),
            ("position", "1".to_string()),
        ],
    )?;
    drivers
        .as_array()?
        .first()?
        .get("driver_number")
        .and_then(Value::as_u64)
        .and_then(|number| u8::try_from(number).ok())
}

fn fetch_driver_details(
    client: &Client,
    session_key: u64,
    driver_number: u8,
) -> Option<(String, String)> {
    let drivers = openf1_request(
        client,
        "drivers",
        &[
            ("session_key", session_key.to_string()),
            ("driver_number", driver_number.to_string()),
        ],
    )?;
    let driver = drivers.as_array()?.iter().find(|driver| {
        driver.get("driver_number").and_then(Value::as_u64) == Some(u64::from(driver_number))
    })?;
    let driver_name = driver
        .get("broadcast_name")
        .and_then(Value::as_str)
        .map(|name| name.replacen(' ', ". ", 1))?;
    let team_name = driver.get("team_name").and_then(Value::as_str)?.to_string();
    Some((driver_name, team_name))
}

fn fetch_fastest_lap(client: &Client, session_key: u64, driver_number: u8) -> Option<Value> {
    let laps = openf1_request(
        client,
        "laps",
        &[
            ("session_key", session_key.to_string()),
            ("driver_number", driver_number.to_string()),
        ],
    )?;
    laps.as_array()?
        .iter()
        .filter(|lap| lap.get("lap_duration").and_then(Value::as_f64).is_some())
        .min_by(|left, right| {
            let left_duration = left
                .get("lap_duration")
                .and_then(Value::as_f64)
                .unwrap_or(f64::MAX);
            let right_duration = right
                .get("lap_duration")
                .and_then(Value::as_f64)
                .unwrap_or(f64::MAX);
            left_duration
                .partial_cmp(&right_duration)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .cloned()
}

fn openf1_request(client: &Client, endpoint: &str, params: &[(&str, String)]) -> Option<Value> {
    let url = format!("https://api.openf1.org/v1/{endpoint}");
    client
        .get(url)
        .query(params)
        .send()
        .ok()?
        .error_for_status()
        .ok()?
        .json::<Value>()
        .ok()
}

fn seconds_field_ms(value: &Value, key: &str) -> Option<u32> {
    value
        .get(key)
        .and_then(Value::as_f64)
        .map(|seconds| (seconds * 1000.0).round() as u32)
}

fn openf1_circuit_key(track_id_raw: i8) -> Option<u16> {
    match track_id_raw {
        3 => Some(63),
        29 => Some(149),
        0 => Some(10),
        13 => Some(46),
        2 => Some(49),
        30 => Some(151),
        27 => Some(6),
        5 => Some(22),
        6 => Some(23),
        4 => Some(15),
        17 => Some(19),
        7 => Some(2),
        9 => Some(4),
        10 => Some(7),
        26 => Some(55),
        11 => Some(39),
        20 => Some(144),
        12 => Some(61),
        15 => Some(9),
        19 => Some(65),
        16 => Some(14),
        31 => Some(152),
        32 => Some(150),
        14 => Some(70),
        _ => None,
    }
}

fn track_label(track_id_raw: i8) -> &'static str {
    match track_id_raw {
        0 => "Melbourne",
        2 => "Shanghai",
        3 => "Sakhir",
        4 => "Catalunya",
        5 => "Monaco",
        6 => "Montreal",
        7 => "Silverstone",
        9 => "Hungaroring",
        10 => "Spa",
        11 => "Monza",
        12 => "Singapore",
        13 => "Suzuka",
        14 => "Abu Dhabi",
        15 => "Texas",
        16 => "Brazil",
        17 => "Austria",
        19 => "Mexico",
        20 => "Baku",
        26 => "Zandvoort",
        27 => "Imola",
        29 => "Jeddah",
        30 => "Miami",
        31 => "Las Vegas",
        32 => "Losail",
        _ => "Unknown",
    }
}

#[cfg(test)]
mod tests {
    use super::{openf1_circuit_key, should_fetch_pole_lap};

    #[test]
    fn track_mapping_supports_known_openf1_circuits() {
        assert_eq!(openf1_circuit_key(7), Some(2));
        assert_eq!(openf1_circuit_key(31), Some(152));
        assert_eq!(openf1_circuit_key(1), None);
    }

    #[test]
    fn only_f1_time_trial_sessions_trigger_pole_lap_fetches() {
        assert!(should_fetch_pole_lap(
            2025,
            0,
            f1_types::SessionType24::TIME_TRIAL as u8
        ));
        assert!(!should_fetch_pole_lap(
            2025,
            2,
            f1_types::SessionType24::TIME_TRIAL as u8
        ));
        assert!(!should_fetch_pole_lap(
            2025,
            0,
            f1_types::SessionType24::RACE as u8
        ));
    }
}
