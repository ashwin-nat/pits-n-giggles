use std::sync::{Mutex, OnceLock};

use axum::body::Body;
use axum::http::{Request, StatusCode, header};
use backend::{
    SharedBackendControlState, SharedDerivedState, SharedFrontendUpdateState, SharedSessionState,
    SharedShutdownState, WebServerConfig, build_router,
};
use f1_types::{
    DriverStatus, F1Packet, F1PacketType, LapData, PacketHeader, PacketLapData,
    PacketParticipantsData, PacketSessionData, ParticipantData, PitStatus, Sector, SessionType24,
    WeatherForecastSample,
};
use http_body_util::BodyExt;
use serde_json::Value;
use tempfile::tempdir;
use tower::ServiceExt;

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

fn control_state() -> SharedBackendControlState {
    SharedBackendControlState::default()
}

fn shutdown_state() -> SharedShutdownState {
    SharedShutdownState::new()
}

#[tokio::test]
async fn health_endpoint_reports_basic_runtime_state() {
    let state = SharedSessionState::new();
    state.with_write(|session_state| {
        session_state.set_connected_to_sim(true);
        session_state.packet_count = 42;
    });

    let app = build_router(
        state,
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/health")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn driver_info_endpoint_validates_index_parameter() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/driver-info?index=999")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn index_route_renders_frontend_template_without_jinja_tags() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(Request::builder().uri("/").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn sse_route_returns_event_stream_content_type() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/events/race-table")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(
        response
            .headers()
            .get(header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok()),
        Some("text/event-stream")
    );
}

#[tokio::test]
async fn frontend_updates_route_returns_event_stream_content_type() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/events/frontend-updates")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(
        response
            .headers()
            .get(header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok()),
        Some("text/event-stream")
    );
}

#[tokio::test]
async fn hud_updates_route_returns_event_stream_content_type() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/events/hud-updates")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(
        response
            .headers()
            .get(header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok()),
        Some("text/event-stream")
    );
}

#[tokio::test]
async fn frontend_updates_snapshot_route_returns_entries() {
    let frontend_updates = SharedFrontendUpdateState::new();
    frontend_updates.push_custom_marker(serde_json::json!({
        "track": "Silverstone",
    }));

    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        frontend_updates,
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/frontend-updates")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let body = response.into_body().collect().await.unwrap().to_bytes();
    let value: Value = serde_json::from_slice(&body).expect("json");
    assert_eq!(value["entries"].as_array().expect("entries").len(), 1);
    assert_eq!(
        value["entries"][0]["payload"]["message-type"],
        "custom-marker"
    );
}

#[tokio::test]
async fn hud_updates_snapshot_route_filters_hud_entries() {
    let frontend_updates = SharedFrontendUpdateState::new();
    frontend_updates.push_custom_marker(serde_json::json!({
        "track": "Silverstone",
    }));
    frontend_updates.push_hud_toggle_notification("mfd");

    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        frontend_updates,
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/hud-updates")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let body = response.into_body().collect().await.unwrap().to_bytes();
    let value: Value = serde_json::from_slice(&body).expect("json");
    assert_eq!(value["entries"].as_array().expect("entries").len(), 1);
    assert_eq!(
        value["entries"][0]["payload"]["message-type"],
        "hud-toggle-notification"
    );
}

#[tokio::test]
async fn save_data_route_rejects_empty_state() {
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/save-data")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::BAD_REQUEST);
}

#[tokio::test]
async fn save_data_route_writes_manual_save_json() {
    let _guard = cwd_lock().lock().expect("cwd lock");
    let temp_dir = tempdir().expect("tempdir");
    let original_cwd = std::env::current_dir().expect("cwd");
    std::env::set_current_dir(temp_dir.path()).expect("set cwd");

    let state = SharedSessionState::new();
    state.with_write(|session_state| {
        session_state.apply_packet(F1Packet::Session(session_packet()));
        session_state.apply_packet(F1Packet::Participants(participants_packet()));
        session_state.apply_packet(F1Packet::LapData(lap_packet()));
    });

    let app = build_router(
        state,
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/save-data")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    std::env::set_current_dir(original_cwd).expect("restore cwd");

    assert_eq!(response.status(), StatusCode::OK);
    let body = response.into_body().collect().await.unwrap().to_bytes();
    let value: Value = serde_json::from_slice(&body).expect("json");
    let message = value["message"].as_str().expect("message");
    assert!(message.contains("Data saved to"));

    let saved_file = temp_dir
        .path()
        .join(message.strip_prefix("Data saved to ").expect("save prefix"));
    let saved_json: Value = serde_json::from_slice(&std::fs::read(saved_file).expect("saved file"))
        .expect("saved json");
    assert_eq!(saved_json["packet-format"], 2025);
    assert_eq!(saved_json["version"], env!("CARGO_PKG_VERSION"));
    assert_eq!(
        saved_json["classification-data"][0]["driver-info"]["name"],
        "Driver 0"
    );
}

#[tokio::test]
async fn control_stats_route_reports_runtime_control_state() {
    let control = SharedBackendControlState::new(
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
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control,
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .uri("/control/stats")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let body = response.into_body().collect().await.unwrap().to_bytes();
    let value: Value = serde_json::from_slice(&body).expect("json");
    assert_eq!(value["status"], "success");
    assert_eq!(
        value["stats"]["udp-action-codes"]["udp_custom_action_code"],
        5
    );
    assert_eq!(
        value["stats"]["udp-action-codes"]["udp_tyre_delta_action_code"],
        6
    );
}

#[tokio::test]
async fn control_udp_action_code_route_updates_config() {
    let control = SharedBackendControlState::new(
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
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control.clone(),
        shutdown_state(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/control/udp-action-code")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(
                    serde_json::to_vec(&serde_json::json!({
                        "action_code_field": "udp_custom_action_code",
                        "value": 9
                    }))
                    .expect("json"),
                ))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(control.udp_custom_action_code(), Some(9));
}

#[tokio::test]
async fn control_shutdown_route_sets_shutdown_reason() {
    let shutdown = shutdown_state();
    let app = build_router(
        SharedSessionState::new(),
        SharedDerivedState::new(),
        SharedFrontendUpdateState::new(),
        control_state(),
        shutdown.clone(),
        WebServerConfig::default(),
    );
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/control/shutdown")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(
                    serde_json::to_vec(&serde_json::json!({
                        "reason": "test shutdown"
                    }))
                    .expect("json"),
                ))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(shutdown.reason().as_deref(), Some("test shutdown"));
}
