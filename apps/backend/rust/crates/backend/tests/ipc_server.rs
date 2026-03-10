use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};

use backend::{
    BackendIpcServer, SharedBackendControlState, SharedSessionState, SharedShutdownState,
};
use f1_types::{
    DriverStatus, F1Packet, F1PacketType, LapData, PacketHeader, PacketLapData,
    PacketParticipantsData, PacketSessionData, ParticipantData, PitStatus, Sector, SessionType24,
    WeatherForecastSample,
};
use serde_json::{Value, json};
use tempfile::tempdir;

fn header(packet_type: F1PacketType, frame: u32) -> PacketHeader {
    PacketHeader::from_values(2025, 25, 1, 0, 1, packet_type, 7, 0.0, frame, frame, 1, 255)
}

fn session_packet() -> PacketSessionData {
    PacketSessionData {
        header: header(F1PacketType::Session, 1),
        weather_raw: 0,
        track_temperature: 30,
        air_temperature: 22,
        total_laps: 58,
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
        num_weather_forecast_samples: 1,
        weather_forecast_samples: vec![WeatherForecastSample {
            packet_format: 2025,
            session_type_raw: SessionType24::RACE as u8,
            time_offset: 0,
            weather_raw: 0,
            track_temperature: 30,
            track_temperature_change_raw: 2,
            air_temperature: 22,
            air_temperature_change_raw: 2,
            rain_percentage: 0,
        }],
        forecast_accuracy: 0,
        ai_difficulty: 100,
        season_link_identifier: 1,
        weekend_link_identifier: 2,
        session_link_identifier: 3,
        pit_stop_window_ideal_lap: 10,
        pit_stop_window_latest_lap: 20,
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

fn lap_packet() -> PacketLapData {
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
            2,
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
            DriverStatus::OnTrack,
            f1_types::ResultStatus::ACTIVE,
            false,
            0,
            0,
            0,
            325.0,
            4,
        ));
    }
    PacketLapData::from_values(header(F1PacketType::LapData, 3), laps, -1, -1)
}

fn cwd_lock() -> &'static Mutex<()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
}

fn saved_json_files(root: &Path) -> Vec<PathBuf> {
    let data_dir = root.join("data");
    if !data_dir.exists() {
        return Vec::new();
    }

    let mut files = Vec::new();
    for dated_entry in std::fs::read_dir(data_dir).expect("read data dir") {
        let dated_entry = dated_entry.expect("dated entry");
        let race_info_dir = dated_entry.path().join("race-info");
        if !race_info_dir.exists() {
            continue;
        }
        for file_entry in std::fs::read_dir(race_info_dir).expect("read race-info dir") {
            let file_entry = file_entry.expect("file entry");
            if file_entry.path().extension().and_then(|ext| ext.to_str()) == Some("json") {
                files.push(file_entry.path());
            }
        }
    }
    files
}

fn ipc_request(port: u16, command: &str, args: Value) -> Value {
    let context = zmq::Context::new();
    let socket = context.socket(zmq::REQ).expect("req socket");
    socket
        .connect(&format!("tcp://127.0.0.1:{port}"))
        .expect("connect req");
    socket.set_rcvtimeo(1000).expect("set timeout");
    socket
        .send(
            serde_json::to_vec(&json!({
                "cmd": command,
                "args": args,
            }))
            .expect("serialize request"),
            0,
        )
        .expect("send request");
    let bytes = socket.recv_bytes(0).expect("recv response");
    serde_json::from_slice(&bytes).expect("deserialize response")
}

#[tokio::test]
async fn ipc_server_handles_launcher_commands() {
    let _guard = cwd_lock().lock().expect("cwd lock");
    let temp_dir = tempdir().expect("tempdir");
    let original_cwd = std::env::current_dir().expect("cwd");
    std::env::set_current_dir(temp_dir.path()).expect("set cwd");

    let session_state = SharedSessionState::new();
    session_state.with_write(|state| {
        state.apply_packet(F1Packet::Session(session_packet()));
        state.apply_packet(F1Packet::Participants(participants_packet()));
        state.apply_packet(F1Packet::LapData(lap_packet()));
    });
    let control_state = SharedBackendControlState::new(
        Some(5),
        Some(6),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    );
    let shutdown_state = SharedShutdownState::new();
    let mut server = BackendIpcServer::start(
        session_state.clone(),
        control_state.clone(),
        shutdown_state.clone(),
    )
    .expect("start ipc server");

    let heartbeat = ipc_request(server.port(), "__heartbeat__", json!({}));
    assert_eq!(heartbeat["status"], "success");
    assert_eq!(heartbeat["reply"], "__heartbeat_ack__");

    let stats = ipc_request(server.port(), "get-stats", json!({}));
    assert_eq!(stats["status"], "success");
    assert_eq!(
        stats["stats"]["__CONTROL__"]["udp-action-codes"]["udp_custom_action_code"],
        json!(5)
    );

    let udp_change = ipc_request(
        server.port(),
        "udp-action-code-change",
        json!({
            "action_code_field": "udp_custom_action_code",
            "value": 9,
        }),
    );
    assert_eq!(udp_change["status"], "success");
    assert_eq!(control_state.udp_custom_action_code(), Some(9));

    let manual_save = ipc_request(server.port(), "manual-save", json!({}));
    assert_eq!(manual_save["status"], "success");
    assert_eq!(saved_json_files(temp_dir.path()).len(), 1);

    let shutdown = ipc_request(
        server.port(),
        "__shutdown__",
        json!({
            "reason": "ipc test",
        }),
    );
    assert_eq!(shutdown["status"], "success");

    server.close();
    std::env::set_current_dir(original_cwd).expect("restore cwd");
    assert_eq!(shutdown_state.reason().as_deref(), Some("ipc test"));
}
