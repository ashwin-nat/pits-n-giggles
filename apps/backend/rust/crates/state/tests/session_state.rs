use f1_types::CarSetupData;
use f1_types::packet_7_car_status_data::{ErsDeployMode, FuelMix, VehicleFiaFlags};
use f1_types::{
    ActualTyreCompound, CarDamageData, CarStatusData, CarTelemetryData, EventDetails,
    EventPacketType, F1Packet, F1PacketType, LapData, PacketCarDamageData, PacketCarSetupData,
    PacketCarStatusData, PacketCarTelemetryData, PacketEventData, PacketHeader, PacketLapData,
    PacketLapPositionsData, PacketParticipantsData, PacketSessionData, PacketSessionHistoryData,
    PacketTimeTrialData, PacketTyreSetsData, ParticipantData, PitStatus, ResultStatus, Sector,
    SessionType24, TimeTrialDataSet, TractionControlAssistMode, TyreSetData, VisualTyreCompound,
    WeatherForecastSample,
};
use state::{MostRecentPoleLap, SessionState};

fn header(packet_type: F1PacketType, frame: u32) -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        0,
        1,
        packet_type,
        100,
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

fn sample_time_trial_session_packet() -> PacketSessionData {
    let mut packet = sample_session_packet();
    packet.header = header(F1PacketType::Session, 1);
    packet.session_type_raw = SessionType24::TIME_TRIAL as u8;
    packet
}

fn sample_participants_packet() -> PacketParticipantsData {
    let mut participants = Vec::new();
    for index in 0..PacketParticipantsData::MAX_PARTICIPANTS {
        participants.push(ParticipantData::from_values(
            2025,
            index != 1,
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

fn sample_lap_packet() -> PacketLapData {
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
            5,
            if index == 1 {
                PitStatus::Pitting
            } else {
                PitStatus::None
            },
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
            if index == 2 {
                ResultStatus::RETIRED
            } else {
                ResultStatus::ACTIVE
            },
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

fn sample_car_setups_packet() -> PacketCarSetupData {
    let mut car_setups = Vec::new();
    for index in 0..22 {
        car_setups.push(CarSetupData::from_values(
            2025,
            10 + index as u8,
            20 + index as u8,
            50,
            40,
            -2.5,
            -1.5,
            0.05,
            0.2,
            30,
            25,
            10,
            12,
            20,
            22,
            95,
            60,
            21.5,
            21.5,
            23.0,
            23.0,
            7,
            30.0,
            80,
        ));
    }
    PacketCarSetupData::from_values(header(F1PacketType::CarSetups, 13), car_setups, 0.0)
}

fn sample_player_tyre_sets_packet() -> PacketTyreSetsData {
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
    PacketTyreSetsData::from_values(header(F1PacketType::TyreSets, 12), 1, tyre_sets, 0)
}

fn sample_time_trial_packet() -> PacketTimeTrialData {
    PacketTimeTrialData::from_values(
        header(F1PacketType::TimeTrial, 14),
        TimeTrialDataSet::from_values(
            2025, 0, 10, 90_000, 30_000, 29_000, 31_000, true, false, true, true, true, true,
        ),
        TimeTrialDataSet::from_values(
            2025, 2, 10, 90_000, 30_000, 29_500, 30_500, true, false, true, true, true, true,
        ),
        TimeTrialDataSet::from_values(
            2025, 3, 10, 91_000, 30_500, 30_000, 30_500, false, true, false, true, true, true,
        ),
    )
}

fn delta_test_lap_packet(
    frame: u32,
    lap_num: u8,
    distance: f32,
    current_lap_time_in_ms: u32,
) -> PacketLapData {
    let mut laps = Vec::new();
    for index in 0..PacketLapData::MAX_CARS {
        let (lap_num, distance, current_lap_time_in_ms) = if index == 0 {
            (lap_num, distance, current_lap_time_in_ms)
        } else {
            (5, 100.0 + index as f32, 10_000 + index as u32)
        };
        laps.push(LapData::from_values(
            2025,
            90_000 + index as u32,
            current_lap_time_in_ms,
            30_000,
            0,
            30_000,
            0,
            500,
            0,
            1_000,
            0,
            distance,
            500.0 + index as f32,
            1.5,
            (index + 1) as u8,
            lap_num,
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
            ResultStatus::ACTIVE,
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
fn session_state_applies_session_participants_and_lap_packets() {
    let mut state = SessionState::new();

    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));

    assert_eq!(state.packet_count, 3);
    assert_eq!(state.player_index, Some(1));
    assert_eq!(state.session_info.track_length, Some(5400));
    assert_eq!(state.num_active_cars, Some(22));

    let player = state.driver(1).expect("player");
    assert_eq!(player.driver_info.name.as_deref(), Some("Driver 1"));
    assert_eq!(player.driver_info.is_player, true);
    assert_eq!(player.lap_info.current_lap, Some(5));
    assert_eq!(player.pit_info.pit_status.as_deref(), Some("PITTING"));

    let retired = state.driver(2).expect("retired");
    assert_eq!(retired.driver_info.dnf_status_code.as_deref(), Some("DNF"));
    assert_eq!(state.num_dnf_cars, Some(1));
}

#[test]
fn session_state_applies_event_status_telemetry_damage_and_tyre_sets() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));

    let event = PacketEventData::from_values(
        header(F1PacketType::Event, 4),
        EventPacketType::FastestLap,
        Some(EventDetails::FastestLap {
            vehicle_idx: 1,
            lap_time: 80.123,
        }),
    );
    state.apply_packet(F1Packet::Event(event));

    let status_packet = PacketCarStatusData::from_values(
        header(F1PacketType::CarStatus, 5),
        vec![
            CarStatusData::from_values(
                TractionControlAssistMode::Off,
                false,
                FuelMix::Lean,
                50,
                false,
                20.0,
                100.0,
                20.0,
                12_000,
                4_000,
                8,
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
    );
    state.apply_packet(F1Packet::CarStatus(status_packet));

    let telemetry_packet = PacketCarTelemetryData::from_values(
        header(F1PacketType::CarTelemetry, 6),
        vec![
            CarTelemetryData::from_values(
                310, 1.0, 0.0, 0.0, 0, 8, 11_500, true, 100, 0, [500; 4], [90; 4], [85; 4], 100,
                [23.0; 4], [0; 4],
            );
            22
        ],
        0,
        0,
        8,
    );
    state.apply_packet(F1Packet::CarTelemetry(telemetry_packet));

    let damage_packet = PacketCarDamageData::from_values(
        header(F1PacketType::CarDamage, 7),
        vec![
            CarDamageData::from_values(
                2025,
                [10.0, 11.0, 12.0, 13.0],
                [1, 2, 3, 4],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                5,
                6,
                7,
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
    );
    state.apply_packet(F1Packet::CarDamage(damage_packet));

    let tyre_sets_packet = PacketTyreSetsData::from_values(
        header(F1PacketType::TyreSets, 8),
        1,
        vec![
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
        ],
        0,
    );
    state.apply_packet(F1Packet::TyreSets(tyre_sets_packet));

    let driver = state.driver(1).expect("driver");
    assert_eq!(state.fastest_index, Some(1));
    assert_eq!(driver.lap_info.best_lap_time_in_ms, Some(80_123));
    assert_eq!(driver.car_info.ers_percent, Some(50.0));
    assert_eq!(driver.car_info.drs_activated, Some(true));
    assert_eq!(driver.car_info.front_left_wing_damage, Some(5));
    assert_eq!(driver.tyre_info.fitted_index, Some(0));
    assert_eq!(
        driver.tyre_info.fitted_tyre_set_key.as_deref(),
        Some("0.C3")
    );
}

#[test]
fn session_state_applies_session_history_and_lap_positions() {
    let mut state = SessionState::new();

    let history_packet = PacketSessionHistoryData::from_values(
        header(F1PacketType::SessionHistory, 9),
        1,
        2,
        0,
        1,
        0,
        0,
        0,
        vec![
            f1_types::LapHistoryData::from_values(80_000, 25_000, 0, 27_000, 0, 28_000, 0, 0),
            f1_types::LapHistoryData::from_values(81_000, 25_500, 0, 27_500, 0, 28_000, 0, 0),
        ],
        vec![],
    );
    state.apply_packet(F1Packet::SessionHistory(history_packet));

    let lap_positions = PacketLapPositionsData::from_values(
        header(F1PacketType::LapPositions, 10),
        3,
        0,
        vec![vec![1, 2, 3], vec![2, 1, 3], vec![1, 2, 3]],
    );
    state.apply_packet(F1Packet::LapPositions(lap_positions));

    let driver = state.driver(1).expect("driver");
    assert_eq!(driver.lap_info.best_lap_time_in_ms, Some(80_000));
    assert_eq!(driver.lap_positions, vec![2, 1, 2]);
}

#[test]
fn session_state_serializes_and_reports_available_data() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));

    assert!(state.is_data_available());

    let value = serde_json::to_value(&state).expect("serialize");
    assert_eq!(value["player_index"], 1);
    assert_eq!(value["session_info"]["track_length"], 5400);
}

#[test]
fn session_state_builds_periodic_update_json() {
    let mut state = SessionState::new();
    state.set_connected_to_sim(true);
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));
    state.apply_packet(F1Packet::SessionHistory(
        PacketSessionHistoryData::from_values(
            header(F1PacketType::SessionHistory, 4),
            0,
            2,
            0,
            2,
            2,
            2,
            2,
            vec![
                f1_types::LapHistoryData::from_values(
                    81_000, 25_500, 0, 27_500, 0, 28_500, 0, 0x0F,
                ),
                f1_types::LapHistoryData::from_values(
                    80_000, 25_000, 0, 27_000, 0, 28_000, 0, 0x0F,
                ),
            ],
            vec![],
        ),
    ));

    let value = state.periodic_update_json();

    assert_eq!(value["live-data"], true);
    assert_eq!(value["f1-game-year"], 25);
    assert_eq!(value["packet-format"], 2025);
    assert_eq!(value["circuit"], "Silverstone");
    assert_eq!(value["formula"], "F1 Modern");
    assert_eq!(value["pit-time-loss"], 28.0);
    assert_eq!(value["session-type"], "Race");
    assert_eq!(value["wdt-status"], true);
    assert_eq!(value["current-lap"], 5);
    assert_eq!(value["player-pit-window"], 10);
    assert_eq!(
        value["table-entries"].as_array().expect("entries").len(),
        22
    );
    assert_eq!(value["table-entries"][0]["driver-info"]["position"], 1);
    assert_eq!(value["table-entries"][0]["driver-info"]["name"], "Driver 0");
    assert_eq!(
        value["table-entries"][0]["lap-info"]["best-lap"]["sector-status"],
        serde_json::json!([2, 2, 2])
    );
    assert_eq!(
        value["table-entries"][0]["lap-info"]["last-lap"]["sector-status"],
        serde_json::json!([2, 2, 2])
    );
}

#[test]
fn session_state_populates_current_lap_delta_ms() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(delta_test_lap_packet(20, 1, 10.0, 1_000)));
    state.apply_packet(F1Packet::LapData(delta_test_lap_packet(21, 1, 20.0, 2_000)));
    state.apply_packet(F1Packet::SessionHistory(
        PacketSessionHistoryData::from_values(
            header(F1PacketType::SessionHistory, 22),
            0,
            1,
            0,
            1,
            1,
            1,
            1,
            vec![f1_types::LapHistoryData::from_values(
                80_000, 25_000, 0, 27_000, 0, 28_000, 0, 0x0F,
            )],
            vec![],
        ),
    ));
    state.apply_packet(F1Packet::LapData(delta_test_lap_packet(23, 2, 15.0, 1_700)));

    let value = state.periodic_update_json();
    assert_eq!(
        value["table-entries"][0]["lap-info"]["curr-lap"]["delta-ms"],
        200
    );
}

#[test]
fn session_state_tracks_race_control_and_warning_history() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));

    let mut updated_lap_packet = sample_lap_packet();
    updated_lap_packet.lap_data[1].penalties = 7;
    updated_lap_packet.lap_data[1].total_warnings = 2;
    state.apply_packet(F1Packet::LapData(updated_lap_packet));

    let event = PacketEventData::from_values(
        header(F1PacketType::Event, 11),
        EventPacketType::Overtake,
        Some(EventDetails::Overtake {
            overtaking_vehicle_idx: 1,
            being_overtaken_vehicle_idx: 0,
        }),
    );
    state.apply_packet(F1Packet::Event(event));

    let tyre_sets_packet = PacketTyreSetsData::from_values(
        header(F1PacketType::TyreSets, 12),
        1,
        vec![
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
        ],
        0,
    );
    state.apply_packet(F1Packet::TyreSets(tyre_sets_packet.clone()));

    let mut tyre_sets_packet_changed = tyre_sets_packet;
    tyre_sets_packet_changed.fitted_index = 1;
    state.apply_packet(F1Packet::TyreSets(tyre_sets_packet_changed));

    let driver_json = state.driver_info_json(1).expect("driver json");
    let race_info = state.race_info_json();

    assert!(
        driver_json["warning-penalty-history"]
            .as_array()
            .expect("warning history")
            .len()
            >= 2
    );
    assert!(
        driver_json["race-control"]
            .as_array()
            .expect("race control")
            .iter()
            .any(|message| message["message-type"] == "OVERTAKE")
    );
    assert!(
        race_info["race-control"]
            .as_array()
            .expect("race control")
            .iter()
            .any(|message| message["message-type"] == "TYRE_CHANGE")
    );
    assert_eq!(
        race_info["overtakes"]["most-heated-rivalries"][0]["driver1"],
        "Driver 0"
    );
    assert_eq!(
        race_info["overtakes"]["most-heated-rivalries"][0]["driver2"],
        "Driver 1"
    );
}

#[test]
fn session_state_builds_time_trial_setup_json() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_time_trial_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::CarSetups(sample_car_setups_packet()));
    state.apply_packet(F1Packet::TimeTrial(sample_time_trial_packet()));

    let value = state.periodic_update_json();
    let tt_data = &value["tt-data"];

    assert_eq!(
        tt_data["tt-setups"]["personal-best-setup"]["front-wing"],
        10
    );
    assert_eq!(
        tt_data["tt-setups"]["player-session-best-setup"]["front-wing"],
        10
    );
    assert_eq!(
        tt_data["tt-setups"]["rival-session-best-setup"]["front-wing"],
        13
    );
}

#[test]
fn session_state_includes_irl_pole_lap_in_time_trial_json() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_time_trial_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.session_info.most_recent_pole_lap = Some(MostRecentPoleLap {
        circuit: "Silverstone".to_string(),
        year: Some(2025),
        driver_name: Some("L. Norris".to_string()),
        driver_num: Some(4),
        team_name: Some("McLaren".to_string()),
        lap_ms: Some(85_000),
        s1_ms: Some(28_000),
        s2_ms: Some(28_500),
        s3_ms: Some(28_500),
        speed_trap_kmph: Some(322),
    });

    let value = state.periodic_update_json();
    let pole_lap = &value["tt-data"]["irl-pole-lap"];

    assert_eq!(pole_lap["driver-name"], "L. Norris");
    assert_eq!(pole_lap["lap-ms"], 85_000);
}

#[test]
fn session_state_builds_tyre_stats_records() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));

    let car0_sets = vec![
        TyreSetData::from_values(
            2025,
            ActualTyreCompound::C3,
            VisualTyreCompound::Soft,
            20,
            true,
            SessionType24::RACE as u8,
            10,
            10,
            0,
            true,
        );
        20
    ];
    let car1_sets = vec![
        TyreSetData::from_values(
            2025,
            ActualTyreCompound::C3,
            VisualTyreCompound::Soft,
            10,
            true,
            SessionType24::RACE as u8,
            8,
            8,
            0,
            true,
        );
        20
    ];
    state.apply_packet(F1Packet::TyreSets(PacketTyreSetsData::from_values(
        header(F1PacketType::TyreSets, 15),
        0,
        car0_sets,
        0,
    )));
    state.apply_packet(F1Packet::TyreSets(PacketTyreSetsData::from_values(
        header(F1PacketType::TyreSets, 16),
        1,
        car1_sets,
        0,
    )));

    let race_info = state.race_info_json();
    let c3_soft = &race_info["records"]["tyre-stats"]["C3 - Soft"];

    assert_eq!(c3_soft["highest-tyre-wear"]["driver-name"], "Driver 0");
    assert_eq!(c3_soft["longest-tyre-stint"]["driver-name"], "Driver 0");
    assert_eq!(
        c3_soft["lowest-tyre-wear-per-lap"]["driver-name"],
        "Driver 1"
    );
}

#[test]
fn session_state_inserts_custom_marker_for_player() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::LapData(sample_lap_packet()));

    let marker = state.insert_custom_marker().expect("marker");
    let race_info = state.race_info_json();

    assert_eq!(marker.track, "Silverstone");
    assert_eq!(marker.event_type, "Race");
    assert_eq!(marker.lap, "5");
    assert_eq!(marker.sector, "SECTOR2");
    assert_eq!(race_info["custom-markers"][0]["track"], "Silverstone");
    assert_eq!(
        race_info["custom-markers"][0]["curr-lap-percentage"],
        "1.87%"
    );
}

#[test]
fn session_state_builds_tyre_delta_notification_payload() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));
    state.apply_packet(F1Packet::TyreSets(sample_player_tyre_sets_packet()));

    let value = state
        .tyre_delta_notification_json()
        .expect("tyre delta payload");
    let messages = value["tyre-delta-messages"].as_array().expect("messages");

    assert_eq!(value["curr-tyre-type"], "Slick");
    assert_eq!(messages.len(), 2);
    assert_eq!(messages[0]["other-tyre-type"], "Wet");
    assert_eq!(messages[0]["tyre-delta"], 2.75);
    assert_eq!(messages[1]["other-tyre-type"], "Intermediate");
    assert_eq!(messages[1]["tyre-delta"], 1.35);
}

#[test]
fn session_state_uses_snapshots_for_historical_driver_modal_data() {
    let mut state = SessionState::new();
    state.apply_packet(F1Packet::Session(sample_session_packet()));
    state.apply_packet(F1Packet::Participants(sample_participants_packet()));

    let mut lap_packet = sample_lap_packet();
    lap_packet.lap_data[1].current_lap_num = 5;
    lap_packet.lap_data[1].car_position = 2;
    state.apply_packet(F1Packet::LapData(lap_packet.clone()));

    let mut status_data = vec![
        CarStatusData::from_values(
            TractionControlAssistMode::Off,
            false,
            FuelMix::Lean,
            50,
            false,
            20.0,
            100.0,
            20.0,
            12_000,
            4_000,
            8,
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
    ];
    status_data[1].fuel_in_tank = 20.0;
    status_data[1].fuel_remaining_laps = 20.0;
    status_data[1].actual_tyre_compound = ActualTyreCompound::C3;
    status_data[1].visual_tyre_compound = VisualTyreCompound::Soft;
    status_data[1].tyres_age_laps = 8;
    status_data[1].ers_store_energy = 2_000_000.0;
    status_data[1].ers_harvested_this_lap_mguk = 100.0;
    status_data[1].ers_deployed_this_lap = 80.0;
    state.apply_packet(F1Packet::CarStatus(PacketCarStatusData::from_values(
        header(F1PacketType::CarStatus, 30),
        status_data,
    )));

    let mut telemetry_data = vec![
        CarTelemetryData::from_values(
            310, 1.0, 0.0, 0.0, 0, 8, 11_500, true, 100, 0, [500; 4], [90; 4], [85; 4], 100,
            [23.0; 4], [0; 4],
        );
        22
    ];
    telemetry_data[1].speed = 321;
    state.apply_packet(F1Packet::CarTelemetry(PacketCarTelemetryData::from_values(
        header(F1PacketType::CarTelemetry, 31),
        telemetry_data,
        0,
        0,
        8,
    )));

    let mut damage_data = vec![
        CarDamageData::from_values(
            2025,
            [10.0, 11.0, 12.0, 13.0],
            [1, 2, 3, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            5,
            6,
            7,
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
    ];
    damage_data[1].tyres_wear = [10.0, 11.0, 12.0, 13.0];
    state.apply_packet(F1Packet::CarDamage(PacketCarDamageData::from_values(
        header(F1PacketType::CarDamage, 32),
        damage_data,
    )));

    state.apply_packet(F1Packet::TyreSets(sample_player_tyre_sets_packet()));

    let history_packet = PacketSessionHistoryData::from_values(
        header(F1PacketType::SessionHistory, 33),
        1,
        5,
        1,
        5,
        5,
        5,
        5,
        vec![
            f1_types::LapHistoryData::from_values(81_000, 25_500, 0, 27_500, 0, 28_500, 0, 0x0F),
            f1_types::LapHistoryData::from_values(81_000, 25_500, 0, 27_500, 0, 28_500, 0, 0x0F),
            f1_types::LapHistoryData::from_values(81_000, 25_500, 0, 27_500, 0, 28_500, 0, 0x0F),
            f1_types::LapHistoryData::from_values(81_000, 25_500, 0, 27_500, 0, 28_500, 0, 0x0F),
            f1_types::LapHistoryData::from_values(80_000, 25_000, 0, 27_000, 0, 28_000, 0, 0x0F),
        ],
        vec![f1_types::TyreStintHistoryData::from_values(
            5,
            ActualTyreCompound::C3,
            VisualTyreCompound::Soft,
        )],
    );
    state.apply_packet(F1Packet::SessionHistory(history_packet));

    let mut lap_packet_next = lap_packet;
    lap_packet_next.header = header(F1PacketType::LapData, 34);
    lap_packet_next.lap_data[1].current_lap_num = 6;
    state.apply_packet(F1Packet::LapData(lap_packet_next));

    let mut status_data_new = vec![
        CarStatusData::from_values(
            TractionControlAssistMode::Off,
            false,
            FuelMix::Lean,
            50,
            false,
            15.0,
            100.0,
            15.0,
            12_000,
            4_000,
            1,
            1,
            100,
            ActualTyreCompound::C4,
            VisualTyreCompound::Medium,
            1,
            VehicleFiaFlags::None,
            0.0,
            0.0,
            1_000_000.0,
            ErsDeployMode::Medium,
            50.0,
            25.0,
            40.0,
            false,
        );
        22
    ];
    status_data_new[1].fuel_in_tank = 15.0;
    status_data_new[1].actual_tyre_compound = ActualTyreCompound::C4;
    status_data_new[1].visual_tyre_compound = VisualTyreCompound::Medium;
    state.apply_packet(F1Packet::CarStatus(PacketCarStatusData::from_values(
        header(F1PacketType::CarStatus, 35),
        status_data_new,
    )));

    let mut damage_data_new = vec![
        CarDamageData::from_values(
            2025,
            [40.0, 41.0, 42.0, 43.0],
            [1, 2, 3, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            5,
            6,
            7,
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
    ];
    damage_data_new[1].tyres_wear = [40.0, 41.0, 42.0, 43.0];
    state.apply_packet(F1Packet::CarDamage(PacketCarDamageData::from_values(
        header(F1PacketType::CarDamage, 36),
        damage_data_new,
    )));

    let mut new_tyre_sets = sample_player_tyre_sets_packet();
    new_tyre_sets.header = header(F1PacketType::TyreSets, 37);
    new_tyre_sets.fitted_index = 1;
    state.apply_packet(F1Packet::TyreSets(new_tyre_sets));

    let driver_json = state.driver_info_json(1).expect("driver json");
    let lap_history = driver_json["lap-time-history"]["lap-history-data"]
        .as_array()
        .expect("lap history");
    let lap_five = lap_history
        .iter()
        .find(|lap| lap["lap-number"] == 5)
        .expect("lap five");
    let per_lap = driver_json["per-lap-info"].as_array().expect("per lap");
    let snapshot_five = per_lap
        .iter()
        .find(|lap| lap["lap-number"] == 5)
        .expect("snapshot five");

    assert_eq!(lap_five["tyre-set-info"]["visual-tyre-compound"], "Soft");
    assert_eq!(lap_five["tyre-set-info"]["tyre-wear"]["average"], 11.5);
    assert_eq!(lap_five["top-speed-kmph"], 321);
    assert_eq!(snapshot_five["car-status-data"]["fuel-in-tank"], 20.0);
    assert_eq!(snapshot_five["car-damage-data"]["tyres-wear"][0], 10.0);
    assert_eq!(
        driver_json["tyre-set-history"][0]["tyre-wear"]["average"],
        11.5
    );
    assert_eq!(
        driver_json["tyre-set-history"][0]["tyre-set-data"]["wear"],
        11.5
    );
    assert_eq!(
        driver_json["tyre-set-history"][0]["tyre-wear-history"]
            .as_array()
            .expect("wear history")
            .len(),
        1
    );
    assert_eq!(
        driver_json["tyre-set-history"][0]["tyre-wear-history"][0]["front-left-wear"],
        10.0
    );

    let race_info = state.race_info_json();
    let position_history = race_info["position-history"]
        .as_array()
        .expect("position history");
    let driver_position_history = position_history
        .iter()
        .find(|entry| entry["name"] == "Driver 1")
        .expect("driver one position history")["driver-position-history"]
        .as_array()
        .expect("driver position history");
    assert_eq!(driver_position_history[0]["lap-number"], 5);
    assert_eq!(driver_position_history[0]["position"], 2);
}
