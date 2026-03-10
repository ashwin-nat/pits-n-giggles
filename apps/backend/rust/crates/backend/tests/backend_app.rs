use std::net::SocketAddr;
use std::time::Duration;

use backend::{BackendApp, BackendConfig};
use f1_types::{
    ActualTyreCompound, EventDetails, EventPacketType, F1Packet, F1PacketType, PacketEventData,
    PacketHeader, PacketParticipantsData, PacketSessionData, PacketTyreSetsData, ParticipantData,
    SessionType24, TyreSetData, VisualTyreCompound, WeatherForecastSample,
};
use telemetry_core::PacketProcessingOutcome;
use tokio::net::UdpSocket;

fn header(packet_type: F1PacketType, frame: u32) -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        0,
        1,
        packet_type,
        42,
        0.0,
        frame,
        frame,
        1,
        255,
    )
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
    PacketParticipantsData::from_values(header(F1PacketType::Participants, 1), 22, participants)
}

fn session_packet() -> PacketSessionData {
    PacketSessionData {
        header: header(F1PacketType::Session, 2),
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

fn player_tyre_sets_packet() -> PacketTyreSetsData {
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

fn button_event_packet(action_code: u8) -> PacketEventData {
    let button_status = 1u32 << (u32::from(action_code) + 19);
    PacketEventData::from_values(
        header(F1PacketType::Event, 4),
        EventPacketType::ButtonStatus,
        Some(EventDetails::Buttons { button_status }),
    )
}

#[tokio::test]
async fn processing_raw_packet_updates_state_on_accept() {
    let receiver = telemetry_core::TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4096)
            .await
            .expect("bind receiver"),
    );
    let mut app = BackendApp::new(receiver, BackendConfig::default());
    let raw_packet = participants_packet().to_bytes();

    let outcome = app.process_raw_packet(&raw_packet);

    assert!(matches!(
        outcome,
        PacketProcessingOutcome::Accepted(F1Packet::Participants(_))
    ));
    assert_eq!(app.state().packet_count, 1);
    assert_eq!(app.state().player_index, Some(1));
    assert_eq!(
        app.state()
            .driver(1)
            .and_then(|driver| driver.driver_info.name.as_deref()),
        Some("Driver 1")
    );
    assert!(app.state().connected_to_sim);
}

#[tokio::test]
async fn dropped_packet_does_not_advance_state() {
    let receiver = telemetry_core::TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4096)
            .await
            .expect("bind receiver"),
    );
    let mut app = BackendApp::new(receiver, BackendConfig::default());

    let outcome = app.process_raw_packet(&[1, 2, 3]);

    assert!(matches!(outcome, PacketProcessingOutcome::Dropped(_)));
    assert_eq!(app.state().packet_count, 0);
    assert!(!app.state().connected_to_sim);
}

#[tokio::test]
async fn backend_reads_udp_packets_and_applies_state() {
    let mut app = BackendApp::bind_udp("127.0.0.1:0", BackendConfig::default())
        .await
        .expect("bind backend");
    let bind_addr = app
        .telemetry_manager()
        .receiver()
        .local_addr()
        .expect("receiver addr");
    let sender = UdpSocket::bind("127.0.0.1:0").await.expect("bind sender");

    sender
        .send_to(&participants_packet().to_bytes(), bind_addr)
        .await
        .expect("send");

    let outcome = tokio::time::timeout(Duration::from_secs(1), app.next())
        .await
        .expect("recv timeout")
        .expect("backend next");

    assert!(matches!(
        outcome,
        PacketProcessingOutcome::Accepted(F1Packet::Participants(_))
    ));
    assert_eq!(app.state().packet_count, 1);
    assert_eq!(
        app.state()
            .driver(0)
            .and_then(|driver| driver.driver_info.name.as_deref()),
        Some("Driver 0")
    );
}

#[tokio::test]
async fn backend_app_accepts_tyre_delta_action_config_without_state_regression() {
    let receiver = telemetry_core::TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4096)
            .await
            .expect("bind receiver"),
    );
    let mut app = BackendApp::new(
        receiver,
        BackendConfig {
            udp_tyre_delta_action_code: Some(5),
            ..BackendConfig::default()
        },
    );

    app.process_raw_packet(&session_packet().to_bytes());
    app.process_raw_packet(&participants_packet().to_bytes());
    app.process_raw_packet(&player_tyre_sets_packet().to_bytes());
    let outcome = app.process_raw_packet(&button_event_packet(5).to_bytes());

    assert!(matches!(
        outcome,
        PacketProcessingOutcome::Accepted(F1Packet::Event(_))
    ));
    assert_eq!(app.state().packet_count, 4);
}

#[tokio::test]
async fn backend_app_forwards_raw_packets_to_configured_udp_target() {
    let receiver = telemetry_core::TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4096)
            .await
            .expect("bind receiver"),
    );
    let forward_listener = UdpSocket::bind("127.0.0.1:0")
        .await
        .expect("bind forward listener");
    let forward_target: SocketAddr = forward_listener.local_addr().expect("forward addr");
    let mut app = BackendApp::new(
        receiver,
        BackendConfig {
            forward_targets: vec![forward_target],
            ..BackendConfig::default()
        },
    );
    let raw_packet = participants_packet().to_bytes();

    let outcome = app.process_raw_packet(&raw_packet);
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
        PacketProcessingOutcome::Accepted(F1Packet::Participants(_))
    ));
    assert_eq!(&buffer[..received], raw_packet.as_slice());
}
