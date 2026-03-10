use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use std::time::Duration;

use backend::{BackendConfig, BackendRuntime, CaptureConfig};
use f1_types::{
    ActualTyreCompound, DriverStatus, EventDetails, EventPacketType, F1PacketType,
    FinalClassificationData, LapData, PacketEventData, PacketFinalClassificationData, PacketHeader,
    PacketLapData, PacketParticipantsData, PacketSessionData, PacketTyreSetsData, ParticipantData,
    PitStatus, ResultReason, ResultStatus, Sector, SessionType24, TyreSetData, VisualTyreCompound,
    WeatherForecastSample,
};
use tempfile::tempdir;
use tokio::net::UdpSocket;

fn header(packet_type: F1PacketType, frame: u32) -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        0,
        1,
        packet_type,
        99,
        0.0,
        frame,
        frame,
        1,
        255,
    )
}

fn session_packet() -> PacketSessionData {
    session_packet_with_type(SessionType24::RACE as u8)
}

fn session_packet_with_type(session_type_raw: u8) -> PacketSessionData {
    PacketSessionData {
        header: header(F1PacketType::Session, 1),
        weather_raw: 0,
        track_temperature: 30,
        air_temperature: 22,
        total_laps: 58,
        track_length: 5400,
        session_type_raw,
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
            session_type_raw,
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

fn final_classification_packet() -> PacketFinalClassificationData {
    PacketFinalClassificationData::from_values(
        header(F1PacketType::FinalClassification, 10),
        1,
        vec![FinalClassificationData::from_values(
            2025,
            1,
            4,
            1,
            58,
            0,
            ResultStatus::FINISHED,
            ResultReason::FINISHED,
            91_234,
            5_123.4,
            0,
            0,
            1,
            vec![ActualTyreCompound::C3],
            vec![VisualTyreCompound::Soft],
            vec![12],
        )],
    )
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
    for dated_entry in fs::read_dir(data_dir).expect("read data dir") {
        let dated_entry = dated_entry.expect("dated entry");
        let race_info_dir = dated_entry.path().join("race-info");
        if !race_info_dir.exists() {
            continue;
        }
        for file_entry in fs::read_dir(race_info_dir).expect("read race-info dir") {
            let file_entry = file_entry.expect("file entry");
            if file_entry.path().extension().and_then(|ext| ext.to_str()) == Some("json") {
                files.push(file_entry.path());
            }
        }
    }
    files
}

async fn wait_for_file_count(root: &Path, expected: usize) -> Vec<PathBuf> {
    for _ in 0..20 {
        let files = saved_json_files(root);
        if files.len() >= expected {
            return files;
        }
        tokio::time::sleep(Duration::from_millis(50)).await;
    }
    saved_json_files(root)
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

fn tyre_sets_packet() -> PacketTyreSetsData {
    let mut tyre_sets = vec![
        TyreSetData::from_values(
            2025,
            ActualTyreCompound::C3,
            VisualTyreCompound::Soft,
            5,
            true,
            SessionType24::RACE as u8,
            20,
            18,
            0,
            true,
        );
        20
    ];
    tyre_sets[18] = TyreSetData::from_values(
        2025,
        ActualTyreCompound::Inter,
        VisualTyreCompound::Inter,
        10,
        true,
        SessionType24::RACE as u8,
        12,
        10,
        1350,
        false,
    );
    tyre_sets[19] = TyreSetData::from_values(
        2025,
        ActualTyreCompound::Wet,
        VisualTyreCompound::Wet,
        12,
        true,
        SessionType24::RACE as u8,
        10,
        8,
        2750,
        false,
    );
    PacketTyreSetsData::from_values(header(F1PacketType::TyreSets, 3), 1, tyre_sets, 0)
}

fn button_packet(action_code: u8, frame: u32) -> PacketEventData {
    let button_status = 1u32 << (u32::from(action_code) + 19);
    PacketEventData::from_values(
        header(F1PacketType::Event, frame),
        EventPacketType::ButtonStatus,
        Some(EventDetails::Buttons { button_status }),
    )
}

fn session_started_packet(frame: u32) -> PacketEventData {
    PacketEventData::from_values(
        header(F1PacketType::Event, frame),
        EventPacketType::SessionStarted,
        None,
    )
}

fn start_lights_packet(frame: u32, num_lights: u8) -> PacketEventData {
    PacketEventData::from_values(
        header(F1PacketType::Event, frame),
        EventPacketType::StartLights,
        Some(EventDetails::StartLights { num_lights }),
    )
}

fn lap_packet(frame: u32) -> PacketLapData {
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
    PacketLapData::from_values(header(F1PacketType::LapData, frame), laps, -1, -1)
}

#[tokio::test]
async fn runtime_publishes_tyre_delta_frontend_update_once_per_press() {
    let mut runtime = BackendRuntime::bind_udp(
        "127.0.0.1:0",
        BackendConfig {
            udp_tyre_delta_action_code: Some(5),
            ..BackendConfig::default()
        },
    )
    .await
    .expect("bind runtime");

    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&tyre_sets_packet().to_bytes());
    runtime.process_raw_packet(&button_packet(5, 4).to_bytes());
    runtime.process_raw_packet(&button_packet(5, 5).to_bytes());

    let updates = runtime.frontend_update_state().entries_after(None);
    assert_eq!(updates.len(), 1);
    assert_eq!(updates[0].payload["message-type"], "tyre-delta-v2");
    assert_eq!(
        updates[0].payload["message"]["tyre-delta-messages"][0]["other-tyre-type"],
        "Wet"
    );
    assert_eq!(
        updates[0].payload["message"]["tyre-delta-messages"][1]["other-tyre-type"],
        "Intermediate"
    );
}

#[tokio::test]
async fn runtime_forwards_raw_packets_received_over_udp() {
    let forward_listener = UdpSocket::bind("127.0.0.1:0")
        .await
        .expect("bind forward listener");
    let forward_target = forward_listener.local_addr().expect("forward addr");
    let mut runtime = BackendRuntime::bind_udp(
        "127.0.0.1:0",
        BackendConfig {
            forward_targets: vec![forward_target],
            ..BackendConfig::default()
        },
    )
    .await
    .expect("bind runtime");
    let bind_addr = runtime
        .telemetry_manager()
        .receiver()
        .local_addr()
        .expect("runtime addr");
    let sender = UdpSocket::bind("127.0.0.1:0").await.expect("bind sender");
    let raw_packet = participants_packet().to_bytes();

    sender
        .send_to(&raw_packet, bind_addr)
        .await
        .expect("send packet");
    let outcome = tokio::time::timeout(Duration::from_secs(1), runtime.next())
        .await
        .expect("runtime timeout")
        .expect("runtime next");

    let mut buffer = [0u8; 4096];
    let (received, _) = tokio::time::timeout(
        Duration::from_secs(1),
        forward_listener.recv_from(&mut buffer),
    )
    .await
    .expect("forward timeout")
    .expect("recv forward");

    assert!(matches!(
        outcome,
        telemetry_core::PacketProcessingOutcome::Accepted(_)
    ));
    assert_eq!(&buffer[..received], raw_packet.as_slice());
}

#[tokio::test]
async fn runtime_uses_updated_control_action_code() {
    let mut runtime = BackendRuntime::bind_udp(
        "127.0.0.1:0",
        BackendConfig {
            udp_custom_action_code: Some(5),
            ..BackendConfig::default()
        },
    )
    .await
    .expect("bind runtime");

    runtime
        .control_state()
        .update_action_code("udp_custom_action_code", Some(6))
        .expect("update");
    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&lap_packet(3).to_bytes());
    runtime.process_raw_packet(&button_packet(5, 4).to_bytes());
    runtime.process_raw_packet(&button_packet(6, 5).to_bytes());

    let updates = runtime.frontend_update_state().entries_after(None);
    assert_eq!(updates.len(), 1);
    assert_eq!(updates[0].payload["message-type"], "custom-marker");
    assert_eq!(
        runtime.control_state().stats_json()["custom-marker-triggers"],
        serde_json::json!(1)
    );
}

#[tokio::test]
async fn runtime_autosaves_final_classification_once_for_race_sessions() {
    let _guard = cwd_lock().lock().expect("cwd lock");
    let temp_dir = tempdir().expect("tempdir");
    let original_cwd = std::env::current_dir().expect("cwd");
    std::env::set_current_dir(temp_dir.path()).expect("set cwd");

    let mut runtime = BackendRuntime::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind runtime");
    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&lap_packet(3).to_bytes());
    runtime.process_raw_packet(&final_classification_packet().to_bytes());
    runtime.process_raw_packet(&final_classification_packet().to_bytes());

    let files = wait_for_file_count(temp_dir.path(), 1).await;
    std::env::set_current_dir(original_cwd).expect("restore cwd");

    assert_eq!(files.len(), 1);
    let saved_json: serde_json::Value =
        serde_json::from_slice(&fs::read(&files[0]).expect("saved file")).expect("saved json");
    assert_eq!(
        saved_json["debug"]["reason"],
        serde_json::json!("Auto-save after final classification")
    );
    let file_name = files[0]
        .file_name()
        .and_then(|name| name.to_str())
        .expect("file name");
    assert!(!file_name.contains("Manual_"));
}

#[tokio::test]
async fn runtime_does_not_autosave_time_trial_when_disabled() {
    let _guard = cwd_lock().lock().expect("cwd lock");
    let temp_dir = tempdir().expect("tempdir");
    let original_cwd = std::env::current_dir().expect("cwd");
    std::env::set_current_dir(temp_dir.path()).expect("set cwd");

    let mut runtime = BackendRuntime::bind_udp(
        "127.0.0.1:0",
        BackendConfig {
            capture: CaptureConfig {
                post_race_data_autosave: true,
                post_quali_data_autosave: true,
                post_fp_data_autosave: false,
                post_tt_data_autosave: false,
            },
            ..BackendConfig::default()
        },
    )
    .await
    .expect("bind runtime");
    runtime
        .process_raw_packet(&session_packet_with_type(SessionType24::TIME_TRIAL as u8).to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&lap_packet(3).to_bytes());
    runtime.process_raw_packet(&final_classification_packet().to_bytes());
    tokio::time::sleep(Duration::from_millis(200)).await;

    let files = saved_json_files(temp_dir.path());
    std::env::set_current_dir(original_cwd).expect("restore cwd");

    assert!(files.is_empty());
}

#[tokio::test]
async fn runtime_clears_state_on_session_started_event() {
    let mut runtime = BackendRuntime::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind runtime");

    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&lap_packet(3).to_bytes());
    runtime.process_raw_packet(&session_started_packet(4).to_bytes());

    let snapshot = runtime.state().snapshot();
    assert_eq!(snapshot.packet_count, 1);
    assert!(snapshot.session_info.packet_session.is_none());
    assert_eq!(snapshot.events.race_control_messages.len(), 1);
    assert_eq!(
        snapshot.events.race_control_messages[0]["message-type"],
        serde_json::json!("SESSION_START")
    );
}

#[tokio::test]
async fn runtime_clears_state_on_missed_start_lights_only_once() {
    let mut runtime = BackendRuntime::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind runtime");

    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());
    runtime.process_raw_packet(&lap_packet(3).to_bytes());
    runtime.process_raw_packet(&start_lights_packet(4, 1).to_bytes());
    runtime.process_raw_packet(&start_lights_packet(5, 1).to_bytes());

    let snapshot = runtime.state().snapshot();
    assert_eq!(snapshot.packet_count, 2);
    assert!(snapshot.session_info.packet_session.is_none());
    assert_eq!(snapshot.events.race_control_messages.len(), 2);
    assert_eq!(
        snapshot.events.race_control_messages[0]["message-type"],
        serde_json::json!("START_LIGHTS")
    );
    assert_eq!(
        snapshot.events.race_control_messages[1]["message-type"],
        serde_json::json!("START_LIGHTS")
    );
}

#[tokio::test]
async fn runtime_ignores_zero_duration_session_packets_after_clear() {
    let mut runtime = BackendRuntime::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind runtime");

    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());

    let mut zero_duration_packet = session_packet();
    zero_duration_packet.header.overall_frame_identifier = 9;
    zero_duration_packet.header.frame_identifier = 9;
    zero_duration_packet.session_duration = 0;
    runtime.process_raw_packet(&zero_duration_packet.to_bytes());

    let snapshot = runtime.state().snapshot();
    assert_eq!(snapshot.packet_count, 0);
    assert!(snapshot.session_info.packet_session.is_none());
    assert!(snapshot.connected_to_sim);
}

#[tokio::test]
async fn runtime_ignores_first_session_packet_after_session_uid_change() {
    let mut runtime = BackendRuntime::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind runtime");

    runtime.process_raw_packet(&session_packet().to_bytes());
    runtime.process_raw_packet(&participants_packet().to_bytes());

    let mut changed_uid_packet = session_packet();
    changed_uid_packet.header.session_uid = 1234;
    changed_uid_packet.header.overall_frame_identifier = 10;
    changed_uid_packet.header.frame_identifier = 10;
    runtime.process_raw_packet(&changed_uid_packet.to_bytes());

    let cleared_snapshot = runtime.state().snapshot();
    assert_eq!(cleared_snapshot.packet_count, 0);
    assert!(cleared_snapshot.session_info.packet_session.is_none());

    runtime.process_raw_packet(&changed_uid_packet.to_bytes());
    let rebuilt_snapshot = runtime.state().snapshot();
    assert_eq!(rebuilt_snapshot.packet_count, 1);
    assert_eq!(rebuilt_snapshot.session_info.session_uid, Some(1234));
}

#[tokio::test]
async fn runtime_publishes_hud_notifications_for_udp_actions() {
    let mut runtime = BackendRuntime::bind_udp(
        "127.0.0.1:0",
        BackendConfig {
            toggle_overlays_udp_action_code: Some(5),
            cycle_mfd_udp_action_code: Some(6),
            lap_timer_toggle_udp_action_code: Some(7),
            mfd_interaction_udp_action_code: Some(8),
            ..BackendConfig::default()
        },
    )
    .await
    .expect("bind runtime");

    runtime.process_raw_packet(&button_packet(5, 4).to_bytes());
    runtime.process_raw_packet(&button_packet(6, 5).to_bytes());
    runtime.process_raw_packet(&button_packet(7, 6).to_bytes());
    runtime.process_raw_packet(&button_packet(8, 7).to_bytes());
    runtime.process_raw_packet(&button_packet(8, 8).to_bytes());

    let updates = runtime.frontend_update_state().hud_entries_after(None);
    assert_eq!(updates.len(), 4);
    assert_eq!(
        updates[0].payload["message-type"],
        "hud-toggle-notification"
    );
    assert_eq!(updates[0].payload["message"]["oid"], "");
    assert_eq!(
        updates[1].payload["message-type"],
        "hud-cycle-mfd-notification"
    );
    assert_eq!(updates[2].payload["message"]["oid"], "lap_timer");
    assert_eq!(
        updates[3].payload["message-type"],
        "hud-mfd-interaction-notification"
    );
}
