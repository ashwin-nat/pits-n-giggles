use std::io;
use std::sync::{Arc, RwLock};

use f1_types::{EventDetails, EventPacketType, F1Packet};
use state::SessionState;
use telemetry_core::{PacketProcessingOutcome, TelemetryManager, TelemetryReceiver};

use crate::control::SharedBackendControlState;
use crate::derived::{DerivedStateWorker, SharedDerivedState, should_refresh_derived_state};
use crate::external::{ExternalMetadataWorker, PoleLapRequest};
use crate::forwarder::PacketForwarderWorker;
use crate::frontend_updates::SharedFrontendUpdateState;
use crate::manual_save::{SaveMode, save_session_to_disk_with_mode};
use crate::{BackendConfig, CaptureConfig};

#[derive(Clone, Default)]
pub struct SharedSessionState(Arc<RwLock<SessionState>>);

impl SharedSessionState {
    pub fn new() -> Self {
        Self(Arc::new(RwLock::new(SessionState::new())))
    }

    pub fn snapshot(&self) -> SessionState {
        self.0.read().expect("session state poisoned").clone()
    }

    pub fn with_read<T>(&self, reader: impl FnOnce(&SessionState) -> T) -> T {
        let guard = self.0.read().expect("session state poisoned");
        reader(&guard)
    }

    pub fn with_write<T>(&self, writer: impl FnOnce(&mut SessionState) -> T) -> T {
        let mut guard = self.0.write().expect("session state poisoned");
        writer(&mut guard)
    }
}

pub struct BackendRuntime {
    telemetry_manager: TelemetryManager,
    state: SharedSessionState,
    derived_state: SharedDerivedState,
    frontend_update_state: SharedFrontendUpdateState,
    control_state: SharedBackendControlState,
    packet_forwarder: PacketForwarderWorker,
    derived_worker: DerivedStateWorker,
    metadata_worker: ExternalMetadataWorker,
    last_pole_lap_request: Option<PoleLapRequest>,
    last_session_uid: Option<u64>,
    data_cleared_this_session: bool,
    last_final_classification_notified_session_uid: Option<u64>,
    last_final_classification_autosaved_session_uid: Option<u64>,
    last_custom_marker_pressed: bool,
    last_tyre_delta_pressed: bool,
    last_toggle_all_overlays_pressed: bool,
    last_cycle_mfd_pressed: bool,
    last_prev_mfd_page_pressed: bool,
    last_lap_timer_toggle_pressed: bool,
    last_timing_tower_toggle_pressed: bool,
    last_mfd_toggle_pressed: bool,
    last_track_radar_toggle_pressed: bool,
    last_input_overlay_toggle_pressed: bool,
    last_mfd_interaction_pressed: bool,
    capture_config: CaptureConfig,
}

impl BackendRuntime {
    pub fn new(receiver: TelemetryReceiver, config: BackendConfig) -> Self {
        let telemetry_config = config.clone().into();
        let state = SharedSessionState::new();
        let derived_state = SharedDerivedState::new();
        let frontend_update_state = SharedFrontendUpdateState::new();
        let control_state = SharedBackendControlState::new(
            config.udp_custom_action_code,
            config.udp_tyre_delta_action_code,
            config.toggle_overlays_udp_action_code,
            config.cycle_mfd_udp_action_code,
            config.prev_mfd_page_udp_action_code,
            config.lap_timer_toggle_udp_action_code,
            config.timing_tower_toggle_udp_action_code,
            config.mfd_toggle_udp_action_code,
            config.track_radar_overlay_toggle_udp_action_code,
            config.input_overlay_toggle_udp_action_code,
            config.mfd_interaction_udp_action_code,
        );
        let forward_targets = config.forward_targets.clone();
        let derived_worker = DerivedStateWorker::start(derived_state.clone());
        let metadata_worker = ExternalMetadataWorker::start(state.clone());
        Self {
            telemetry_manager: TelemetryManager::new(receiver, telemetry_config),
            state,
            derived_state,
            frontend_update_state,
            control_state,
            packet_forwarder: PacketForwarderWorker::start(forward_targets),
            derived_worker,
            metadata_worker,
            last_pole_lap_request: None,
            last_session_uid: None,
            data_cleared_this_session: false,
            last_final_classification_notified_session_uid: None,
            last_final_classification_autosaved_session_uid: None,
            last_custom_marker_pressed: false,
            last_tyre_delta_pressed: false,
            last_toggle_all_overlays_pressed: false,
            last_cycle_mfd_pressed: false,
            last_prev_mfd_page_pressed: false,
            last_lap_timer_toggle_pressed: false,
            last_timing_tower_toggle_pressed: false,
            last_mfd_toggle_pressed: false,
            last_track_radar_toggle_pressed: false,
            last_input_overlay_toggle_pressed: false,
            last_mfd_interaction_pressed: false,
            capture_config: config.capture,
        }
    }

    pub async fn bind_udp(
        bind_addr: impl tokio::net::ToSocketAddrs,
        config: BackendConfig,
    ) -> io::Result<Self> {
        let receiver = TelemetryReceiver::bind_udp(bind_addr).await?;
        Ok(Self::new(receiver, config))
    }

    pub async fn bind_tcp(
        bind_addr: impl tokio::net::ToSocketAddrs,
        config: BackendConfig,
    ) -> io::Result<Self> {
        let receiver = TelemetryReceiver::bind_tcp(bind_addr).await?;
        Ok(Self::new(receiver, config))
    }

    pub fn state(&self) -> SharedSessionState {
        self.state.clone()
    }

    pub fn derived_state(&self) -> SharedDerivedState {
        self.derived_state.clone()
    }

    pub fn frontend_update_state(&self) -> SharedFrontendUpdateState {
        self.frontend_update_state.clone()
    }

    pub fn control_state(&self) -> SharedBackendControlState {
        self.control_state.clone()
    }

    pub fn telemetry_manager(&self) -> &TelemetryManager {
        &self.telemetry_manager
    }

    pub fn telemetry_manager_mut(&mut self) -> &mut TelemetryManager {
        &mut self.telemetry_manager
    }

    pub fn process_raw_packet(&mut self, raw_packet: &[u8]) -> PacketProcessingOutcome {
        self.packet_forwarder.try_forward(raw_packet);
        self.control_state.record_forwarded();
        let outcome = self.telemetry_manager.process_raw_packet(raw_packet);
        self.control_state.record_outcome(&outcome);
        self.apply_outcome(&outcome);
        outcome
    }

    pub async fn next(&mut self) -> io::Result<PacketProcessingOutcome> {
        let message = self.telemetry_manager.receiver_mut().recv().await?;
        self.packet_forwarder.try_forward(&message.payload);
        self.control_state.record_forwarded();
        let outcome = self.telemetry_manager.process_raw_packet(&message.payload);
        self.control_state.record_outcome(&outcome);
        self.apply_outcome(&outcome);
        Ok(outcome)
    }

    pub async fn next_accepted_packet(&mut self) -> io::Result<F1Packet> {
        loop {
            match self.next().await? {
                PacketProcessingOutcome::Accepted(packet) => return Ok(packet),
                PacketProcessingOutcome::Dropped(_) => {}
            }
        }
    }

    pub async fn run<F>(&mut self, mut on_packet: F) -> io::Result<()>
    where
        F: FnMut(SharedSessionState, &F1Packet),
    {
        loop {
            let packet = self.next_accepted_packet().await?;
            on_packet(self.state.clone(), &packet);
        }
    }

    fn apply_outcome(&mut self, outcome: &PacketProcessingOutcome) {
        if let PacketProcessingOutcome::Accepted(packet) = outcome {
            if !self.preprocess_packet(packet) {
                return;
            }
            self.state.with_write(|state| {
                state.set_connected_to_sim(true);
                state.apply_packet(packet.clone());
            });
            self.maybe_insert_custom_marker(packet);
            self.maybe_publish_tyre_delta(packet);
            self.maybe_publish_hud_notifications(packet);
            self.maybe_autosave_final_classification(packet);
            self.maybe_publish_final_classification_notification(packet);
            if matches!(packet, F1Packet::Session(_)) {
                self.schedule_pole_lap_refresh_if_needed();
            }
            if should_refresh_derived_state(packet) {
                self.derived_worker.try_schedule(self.state.snapshot());
            }
        }
    }

    fn preprocess_packet(&mut self, packet: &F1Packet) -> bool {
        match packet {
            F1Packet::Session(session) => {
                if session.session_duration == 0 {
                    self.clear_all_data_structures();
                    return false;
                }

                let should_clear = self.state.with_read(|state| {
                    state
                        .session_info
                        .session_uid
                        .is_some_and(|session_uid| session_uid != session.header.session_uid)
                });
                if should_clear {
                    self.clear_all_data_structures();
                    return false;
                }
            }
            F1Packet::Event(event) => match event.event_code {
                EventPacketType::SessionStarted => {
                    self.last_session_uid = Some(event.header.session_uid);
                    self.clear_all_data_structures();
                }
                EventPacketType::StartLights => {
                    if matches!(
                        event.event_details.as_ref(),
                        Some(EventDetails::StartLights { num_lights: 1 })
                    ) {
                        let session_uid = event.header.session_uid;
                        if self.last_session_uid != Some(session_uid) {
                            self.last_session_uid = Some(session_uid);
                            self.data_cleared_this_session = false;
                        }
                        if !self.data_cleared_this_session {
                            self.clear_all_data_structures();
                        }
                    }
                }
                _ => {}
            },
            _ => {}
        }
        true
    }

    fn clear_all_data_structures(&mut self) {
        self.state.with_write(|state| {
            state.clear();
            state.set_connected_to_sim(true);
        });
        self.derived_state.clear();
        self.frontend_update_state.clear();
        self.last_pole_lap_request = None;
        self.last_final_classification_notified_session_uid = None;
        self.last_final_classification_autosaved_session_uid = None;
        self.last_custom_marker_pressed = false;
        self.last_tyre_delta_pressed = false;
        self.last_toggle_all_overlays_pressed = false;
        self.last_cycle_mfd_pressed = false;
        self.last_prev_mfd_page_pressed = false;
        self.last_lap_timer_toggle_pressed = false;
        self.last_timing_tower_toggle_pressed = false;
        self.last_mfd_toggle_pressed = false;
        self.last_track_radar_toggle_pressed = false;
        self.last_input_overlay_toggle_pressed = false;
        self.last_mfd_interaction_pressed = false;
        self.data_cleared_this_session = true;
    }

    fn schedule_pole_lap_refresh_if_needed(&mut self) {
        let request = self.state.with_read(|state| {
            Some(PoleLapRequest {
                session_uid: state.session_info.session_uid?,
                packet_format: state.session_info.packet_format?,
                track_id_raw: state.session_info.track_id_raw?,
                formula_raw: state.session_info.formula_raw?,
                session_type_raw: state.session_info.session_type_raw?,
            })
        });

        if self.last_pole_lap_request == request {
            return;
        }

        self.last_pole_lap_request = request.clone();
        if let Some(request) = request {
            self.metadata_worker.try_schedule(request);
        }
    }

    fn maybe_insert_custom_marker(&mut self, packet: &F1Packet) {
        let Some(action_code) = self.control_state.udp_custom_action_code() else {
            return;
        };
        let is_pressed = crate::custom_action_pressed(packet, action_code);
        if is_pressed && !self.last_custom_marker_pressed {
            self.state.with_write(|state| {
                if let Some(marker) = state.insert_custom_marker() {
                    let marker = serde_json::to_value(marker).unwrap_or(serde_json::Value::Null);
                    self.frontend_update_state.push_custom_marker(marker);
                }
            });
            self.control_state.record_custom_marker_trigger();
        }
        self.last_custom_marker_pressed = is_pressed;
    }

    fn maybe_publish_tyre_delta(&mut self, packet: &F1Packet) {
        let Some(action_code) = self.control_state.udp_tyre_delta_action_code() else {
            return;
        };
        let is_pressed = crate::custom_action_pressed(packet, action_code);
        if is_pressed && !self.last_tyre_delta_pressed {
            if let Some(message) = self
                .state
                .with_read(|state| state.tyre_delta_notification_json())
            {
                self.frontend_update_state
                    .push_tyre_delta_notification(message);
                self.control_state.record_tyre_delta_trigger();
            }
        }
        self.last_tyre_delta_pressed = is_pressed;
    }

    fn maybe_publish_hud_notifications(&mut self, packet: &F1Packet) {
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.toggle_all_overlays_udp_action_code(),
            &mut self.last_toggle_all_overlays_pressed,
            |updates| updates.push_hud_toggle_notification(""),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.cycle_mfd_udp_action_code(),
            &mut self.last_cycle_mfd_pressed,
            |updates| updates.push_hud_cycle_mfd_notification(),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.prev_mfd_page_udp_action_code(),
            &mut self.last_prev_mfd_page_pressed,
            |updates| updates.push_hud_prev_page_mfd_notification(),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.lap_timer_toggle_udp_action_code(),
            &mut self.last_lap_timer_toggle_pressed,
            |updates| updates.push_hud_toggle_notification("lap_timer"),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.timing_tower_toggle_udp_action_code(),
            &mut self.last_timing_tower_toggle_pressed,
            |updates| updates.push_hud_toggle_notification("timing_tower"),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.mfd_toggle_udp_action_code(),
            &mut self.last_mfd_toggle_pressed,
            |updates| updates.push_hud_toggle_notification("mfd"),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state
                .track_radar_overlay_toggle_udp_action_code(),
            &mut self.last_track_radar_toggle_pressed,
            |updates| updates.push_hud_toggle_notification("track_radar"),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.input_overlay_toggle_udp_action_code(),
            &mut self.last_input_overlay_toggle_pressed,
            |updates| updates.push_hud_toggle_notification("input_telemetry"),
        );
        Self::handle_button_action(
            &self.frontend_update_state,
            packet,
            self.control_state.mfd_interaction_udp_action_code(),
            &mut self.last_mfd_interaction_pressed,
            |updates| updates.push_hud_mfd_interaction_notification(),
        );
    }

    fn handle_button_action(
        frontend_update_state: &SharedFrontendUpdateState,
        packet: &F1Packet,
        action_code: Option<u8>,
        last_pressed: &mut bool,
        on_press: impl FnOnce(&SharedFrontendUpdateState),
    ) {
        let Some(action_code) = action_code else {
            return;
        };
        let is_pressed = crate::custom_action_pressed(packet, action_code);
        if is_pressed && !*last_pressed {
            on_press(frontend_update_state);
        }
        *last_pressed = is_pressed;
    }

    fn maybe_publish_final_classification_notification(&mut self, packet: &F1Packet) {
        if !matches!(packet, F1Packet::FinalClassification(_)) {
            return;
        }

        let maybe_position = self.state.with_read(|state| {
            let session_uid = state.session_info.session_uid?;
            if self.last_final_classification_notified_session_uid == Some(session_uid) {
                return None;
            }
            let packet_format = state.session_info.packet_format?;
            let session_type_raw = state.session_info.session_type_raw?;
            let session_supported = if packet_format == 2023 {
                f1_types::SessionType23::try_from(session_type_raw)
                    .map(|value| value.is_race_type_session() || value.is_quali_type_session())
                    .unwrap_or(false)
            } else {
                f1_types::SessionType24::try_from(session_type_raw)
                    .map(|value| value.is_race_type_session() || value.is_quali_type_session())
                    .unwrap_or(false)
            };
            if !session_supported {
                return None;
            }

            let player_index = usize::from(state.player_index?);
            Some((
                session_uid,
                state.driver(player_index)?.driver_info.position?,
            ))
        });

        if let Some((session_uid, player_position)) = maybe_position {
            self.last_final_classification_notified_session_uid = Some(session_uid);
            self.frontend_update_state
                .push_final_classification_notification(player_position);
        }
    }

    fn maybe_autosave_final_classification(&mut self, packet: &F1Packet) {
        if !matches!(packet, F1Packet::FinalClassification(_)) {
            return;
        }

        let should_autosave = self.state.with_read(|state| {
            let session_uid = state.session_info.session_uid?;
            if self.last_final_classification_autosaved_session_uid == Some(session_uid) {
                return None;
            }
            let packet_format = state.session_info.packet_format?;
            let session_type_raw = state.session_info.session_type_raw?;
            autosave_enabled_for_session(packet_format, session_type_raw, self.capture_config)
                .then_some(session_uid)
        });

        if let Some(session_uid) = should_autosave {
            self.last_final_classification_autosaved_session_uid = Some(session_uid);
            let session_state = self.state.clone();
            tokio::spawn(async move {
                if let Err(error) = save_session_to_disk_with_mode(
                    session_state,
                    env!("CARGO_PKG_VERSION"),
                    SaveMode::AutoFinalClassification,
                )
                .await
                {
                    eprintln!("failed to auto-save final classification: {error}");
                }
            });
        }
    }
}

fn autosave_enabled_for_session(
    packet_format: u16,
    session_type_raw: u8,
    capture_config: CaptureConfig,
) -> bool {
    if packet_format == 2023 {
        let Ok(session_type) = f1_types::SessionType23::try_from(session_type_raw) else {
            return false;
        };
        if session_type.is_fp_type_session() {
            return capture_config.post_fp_data_autosave;
        }
        if session_type.is_quali_type_session() {
            return capture_config.post_quali_data_autosave;
        }
        if session_type.is_race_type_session() {
            return capture_config.post_race_data_autosave;
        }
        if session_type.is_time_trial_type_session() {
            return capture_config.post_tt_data_autosave;
        }
        false
    } else {
        let Ok(session_type) = f1_types::SessionType24::try_from(session_type_raw) else {
            return false;
        };
        if session_type.is_fp_type_session() {
            return capture_config.post_fp_data_autosave;
        }
        if session_type.is_quali_type_session() {
            return capture_config.post_quali_data_autosave;
        }
        if session_type.is_race_type_session() {
            return capture_config.post_race_data_autosave;
        }
        if session_type.is_time_trial_type_session() {
            return capture_config.post_tt_data_autosave;
        }
        false
    }
}
