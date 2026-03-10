mod control;
mod derived;
mod external;
mod forwarder;
mod frontend_updates;
mod ipc;
mod manual_save;
mod runtime;
mod shutdown;
mod web;

use std::collections::HashSet;
use std::io;
use std::net::SocketAddr;

use f1_types::{F1Packet, F1PacketType};
use state::SessionState;
use telemetry_core::{
    PacketProcessingOutcome, TelemetryManager, TelemetryManagerConfig, TelemetryReceiver,
};

pub use control::SharedBackendControlState;
pub use derived::{DerivedState, SharedDerivedState};
use forwarder::PacketForwarderWorker;
pub use frontend_updates::SharedFrontendUpdateState;
pub use ipc::BackendIpcServer;
pub use runtime::{BackendRuntime, SharedSessionState};
pub use shutdown::SharedShutdownState;
pub use web::{WebServerConfig, build_router, serve};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CaptureConfig {
    pub post_race_data_autosave: bool,
    pub post_quali_data_autosave: bool,
    pub post_fp_data_autosave: bool,
    pub post_tt_data_autosave: bool,
}

impl Default for CaptureConfig {
    fn default() -> Self {
        Self {
            post_race_data_autosave: true,
            post_quali_data_autosave: true,
            post_fp_data_autosave: false,
            post_tt_data_autosave: false,
        }
    }
}

#[derive(Clone, Debug)]
pub struct BackendConfig {
    pub interested_packets: Option<HashSet<F1PacketType>>,
    pub frame_gate_enabled: bool,
    pub min_supported_packet_format: u16,
    pub forward_targets: Vec<SocketAddr>,
    pub udp_custom_action_code: Option<u8>,
    pub udp_tyre_delta_action_code: Option<u8>,
    pub toggle_overlays_udp_action_code: Option<u8>,
    pub cycle_mfd_udp_action_code: Option<u8>,
    pub prev_mfd_page_udp_action_code: Option<u8>,
    pub lap_timer_toggle_udp_action_code: Option<u8>,
    pub timing_tower_toggle_udp_action_code: Option<u8>,
    pub mfd_toggle_udp_action_code: Option<u8>,
    pub track_radar_overlay_toggle_udp_action_code: Option<u8>,
    pub input_overlay_toggle_udp_action_code: Option<u8>,
    pub mfd_interaction_udp_action_code: Option<u8>,
    pub capture: CaptureConfig,
}

impl Default for BackendConfig {
    fn default() -> Self {
        Self {
            interested_packets: None,
            frame_gate_enabled: false,
            min_supported_packet_format: telemetry_core::MIN_SUPPORTED_PACKET_FORMAT,
            forward_targets: Vec::new(),
            udp_custom_action_code: None,
            udp_tyre_delta_action_code: None,
            toggle_overlays_udp_action_code: None,
            cycle_mfd_udp_action_code: None,
            prev_mfd_page_udp_action_code: None,
            lap_timer_toggle_udp_action_code: None,
            timing_tower_toggle_udp_action_code: None,
            mfd_toggle_udp_action_code: None,
            track_radar_overlay_toggle_udp_action_code: None,
            input_overlay_toggle_udp_action_code: None,
            mfd_interaction_udp_action_code: None,
            capture: CaptureConfig::default(),
        }
    }
}

impl From<BackendConfig> for TelemetryManagerConfig {
    fn from(value: BackendConfig) -> Self {
        Self {
            interested_packets: value.interested_packets,
            frame_gate_enabled: value.frame_gate_enabled,
            min_supported_packet_format: value.min_supported_packet_format,
        }
    }
}

pub struct BackendApp {
    telemetry_manager: TelemetryManager,
    state: SessionState,
    packet_forwarder: PacketForwarderWorker,
    udp_custom_action_code: Option<u8>,
    udp_tyre_delta_action_code: Option<u8>,
    last_custom_marker_pressed: bool,
    last_tyre_delta_pressed: bool,
}

impl BackendApp {
    pub fn new(receiver: TelemetryReceiver, config: BackendConfig) -> Self {
        let forward_targets = config.forward_targets.clone();
        let udp_custom_action_code = config.udp_custom_action_code;
        let udp_tyre_delta_action_code = config.udp_tyre_delta_action_code;
        Self {
            telemetry_manager: TelemetryManager::new(receiver, config.into()),
            state: SessionState::new(),
            packet_forwarder: PacketForwarderWorker::start(forward_targets),
            udp_custom_action_code,
            udp_tyre_delta_action_code,
            last_custom_marker_pressed: false,
            last_tyre_delta_pressed: false,
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

    pub fn state(&self) -> &SessionState {
        &self.state
    }

    pub fn state_mut(&mut self) -> &mut SessionState {
        &mut self.state
    }

    pub fn telemetry_manager(&self) -> &TelemetryManager {
        &self.telemetry_manager
    }

    pub fn telemetry_manager_mut(&mut self) -> &mut TelemetryManager {
        &mut self.telemetry_manager
    }

    pub fn process_raw_packet(&mut self, raw_packet: &[u8]) -> PacketProcessingOutcome {
        self.packet_forwarder.try_forward(raw_packet);
        let outcome = self.telemetry_manager.process_raw_packet(raw_packet);
        self.apply_outcome(&outcome);
        outcome
    }

    pub async fn next(&mut self) -> io::Result<PacketProcessingOutcome> {
        let message = self.telemetry_manager.receiver_mut().recv().await?;
        self.packet_forwarder.try_forward(&message.payload);
        let outcome = self.telemetry_manager.process_raw_packet(&message.payload);
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
        F: FnMut(&SessionState, &F1Packet),
    {
        loop {
            let packet = self.next_accepted_packet().await?;
            on_packet(&self.state, &packet);
        }
    }

    fn apply_outcome(&mut self, outcome: &PacketProcessingOutcome) {
        if let PacketProcessingOutcome::Accepted(packet) = outcome {
            self.state.set_connected_to_sim(true);
            self.state.apply_packet(packet.clone());
            self.maybe_insert_custom_marker(packet);
            self.maybe_publish_tyre_delta(packet);
        }
    }

    fn maybe_insert_custom_marker(&mut self, packet: &F1Packet) {
        let Some(action_code) = self.udp_custom_action_code else {
            return;
        };
        let is_pressed = custom_action_pressed(packet, action_code);
        if is_pressed && !self.last_custom_marker_pressed {
            let _ = self.state.insert_custom_marker();
        }
        self.last_custom_marker_pressed = is_pressed;
    }

    fn maybe_publish_tyre_delta(&mut self, packet: &F1Packet) {
        let Some(action_code) = self.udp_tyre_delta_action_code else {
            return;
        };
        let is_pressed = custom_action_pressed(packet, action_code);
        if is_pressed && !self.last_tyre_delta_pressed {
            let _ = self.state.tyre_delta_notification_json();
        }
        self.last_tyre_delta_pressed = is_pressed;
    }
}

fn custom_action_pressed(packet: &F1Packet, action_code: u8) -> bool {
    if !(1..=12).contains(&action_code) {
        return false;
    }

    let F1Packet::Event(event) = packet else {
        return false;
    };
    let Some(f1_types::EventDetails::Buttons { button_status }) = event.event_details.as_ref()
    else {
        return false;
    };
    let udp_flag = 1u32 << (u32::from(action_code) + 19);
    (button_status & udp_flag) != 0
}
