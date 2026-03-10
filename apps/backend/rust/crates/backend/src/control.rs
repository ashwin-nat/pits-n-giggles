use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, RwLock};

use serde_json::{Value, json};
use telemetry_core::PacketProcessingOutcome;

#[derive(Clone, Debug, Default)]
struct ActionCodeConfig {
    udp_custom_action_code: Option<u8>,
    udp_tyre_delta_action_code: Option<u8>,
    toggle_all_overlays_udp_action_code: Option<u8>,
    cycle_mfd_udp_action_code: Option<u8>,
    prev_mfd_page_udp_action_code: Option<u8>,
    lap_timer_toggle_udp_action_code: Option<u8>,
    timing_tower_toggle_udp_action_code: Option<u8>,
    mfd_toggle_udp_action_code: Option<u8>,
    track_radar_overlay_toggle_udp_action_code: Option<u8>,
    input_overlay_toggle_udp_action_code: Option<u8>,
    mfd_interaction_udp_action_code: Option<u8>,
}

#[derive(Debug, Default)]
struct BackendControlStateInner {
    action_codes: RwLock<ActionCodeConfig>,
    accepted_packets: AtomicU64,
    dropped_packets: AtomicU64,
    forwarded_packets: AtomicU64,
    custom_marker_triggers: AtomicU64,
    tyre_delta_triggers: AtomicU64,
}

#[derive(Clone, Debug, Default)]
pub struct SharedBackendControlState(Arc<BackendControlStateInner>);

impl SharedBackendControlState {
    pub fn new(
        udp_custom_action_code: Option<u8>,
        udp_tyre_delta_action_code: Option<u8>,
        toggle_all_overlays_udp_action_code: Option<u8>,
        cycle_mfd_udp_action_code: Option<u8>,
        prev_mfd_page_udp_action_code: Option<u8>,
        lap_timer_toggle_udp_action_code: Option<u8>,
        timing_tower_toggle_udp_action_code: Option<u8>,
        mfd_toggle_udp_action_code: Option<u8>,
        track_radar_overlay_toggle_udp_action_code: Option<u8>,
        input_overlay_toggle_udp_action_code: Option<u8>,
        mfd_interaction_udp_action_code: Option<u8>,
    ) -> Self {
        Self(Arc::new(BackendControlStateInner {
            action_codes: RwLock::new(ActionCodeConfig {
                udp_custom_action_code,
                udp_tyre_delta_action_code,
                toggle_all_overlays_udp_action_code,
                cycle_mfd_udp_action_code,
                prev_mfd_page_udp_action_code,
                lap_timer_toggle_udp_action_code,
                timing_tower_toggle_udp_action_code,
                mfd_toggle_udp_action_code,
                track_radar_overlay_toggle_udp_action_code,
                input_overlay_toggle_udp_action_code,
                mfd_interaction_udp_action_code,
            }),
            ..BackendControlStateInner::default()
        }))
    }

    pub fn udp_custom_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .udp_custom_action_code
    }

    pub fn udp_tyre_delta_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .udp_tyre_delta_action_code
    }

    pub fn toggle_all_overlays_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .toggle_all_overlays_udp_action_code
    }

    pub fn cycle_mfd_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .cycle_mfd_udp_action_code
    }

    pub fn prev_mfd_page_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .prev_mfd_page_udp_action_code
    }

    pub fn lap_timer_toggle_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .lap_timer_toggle_udp_action_code
    }

    pub fn timing_tower_toggle_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .timing_tower_toggle_udp_action_code
    }

    pub fn mfd_toggle_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .mfd_toggle_udp_action_code
    }

    pub fn track_radar_overlay_toggle_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .track_radar_overlay_toggle_udp_action_code
    }

    pub fn input_overlay_toggle_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .input_overlay_toggle_udp_action_code
    }

    pub fn mfd_interaction_udp_action_code(&self) -> Option<u8> {
        self.0
            .action_codes
            .read()
            .expect("control state poisoned")
            .mfd_interaction_udp_action_code
    }

    pub fn update_action_code(&self, field: &str, value: Option<u8>) -> Result<(), String> {
        let mut guard = self.0.action_codes.write().expect("control state poisoned");
        match field {
            "udp_custom_action_code" | "custom_marker" | "custom-marker" => {
                guard.udp_custom_action_code = value;
            }
            "udp_tyre_delta_action_code" | "tyre_delta" | "tyre-delta" => {
                guard.udp_tyre_delta_action_code = value;
            }
            "toggle_overlays_udp_action_code" | "toggle_all_overlays" | "toggle-all-overlays" => {
                guard.toggle_all_overlays_udp_action_code = value;
            }
            "cycle_mfd_udp_action_code" | "cycle_mfd" | "cycle-mfd" => {
                guard.cycle_mfd_udp_action_code = value;
            }
            "prev_mfd_page_udp_action_code" | "prev_mfd_page" | "prev-mfd-page" => {
                guard.prev_mfd_page_udp_action_code = value;
            }
            "lap_timer_toggle_udp_action_code"
            | "toggle_lap_timer_overlay"
            | "toggle-lap-timer-overlay" => {
                guard.lap_timer_toggle_udp_action_code = value;
            }
            "timing_tower_toggle_udp_action_code"
            | "toggle_timing_tower_overlay"
            | "toggle-timing-tower-overlay" => {
                guard.timing_tower_toggle_udp_action_code = value;
            }
            "mfd_toggle_udp_action_code" | "toggle_mfd_overlay" | "toggle-mfd-overlay" => {
                guard.mfd_toggle_udp_action_code = value;
            }
            "track_radar_overlay_toggle_udp_action_code"
            | "toggle_track_radar_overlay"
            | "toggle-track-radar-overlay" => {
                guard.track_radar_overlay_toggle_udp_action_code = value;
            }
            "input_overlay_toggle_udp_action_code"
            | "toggle_input_overlay"
            | "toggle-input-overlay" => {
                guard.input_overlay_toggle_udp_action_code = value;
            }
            "mfd_interaction_udp_action_code" | "mfd_interaction" | "mfd-interaction" => {
                guard.mfd_interaction_udp_action_code = value;
            }
            _ => return Err(format!("Invalid udp action code field: {field}")),
        }
        Ok(())
    }

    pub fn record_outcome(&self, outcome: &PacketProcessingOutcome) {
        match outcome {
            PacketProcessingOutcome::Accepted(_) => {
                self.0.accepted_packets.fetch_add(1, Ordering::Relaxed);
            }
            PacketProcessingOutcome::Dropped(_) => {
                self.0.dropped_packets.fetch_add(1, Ordering::Relaxed);
            }
        }
    }

    pub fn record_forwarded(&self) {
        self.0.forwarded_packets.fetch_add(1, Ordering::Relaxed);
    }

    pub fn record_custom_marker_trigger(&self) {
        self.0
            .custom_marker_triggers
            .fetch_add(1, Ordering::Relaxed);
    }

    pub fn record_tyre_delta_trigger(&self) {
        self.0.tyre_delta_triggers.fetch_add(1, Ordering::Relaxed);
    }

    pub fn stats_json(&self) -> Value {
        let action_codes = self.0.action_codes.read().expect("control state poisoned");
        json!({
            "accepted-packets": self.0.accepted_packets.load(Ordering::Relaxed),
            "dropped-packets": self.0.dropped_packets.load(Ordering::Relaxed),
            "forwarded-packets": self.0.forwarded_packets.load(Ordering::Relaxed),
            "custom-marker-triggers": self.0.custom_marker_triggers.load(Ordering::Relaxed),
            "tyre-delta-triggers": self.0.tyre_delta_triggers.load(Ordering::Relaxed),
            "udp-action-codes": {
                "udp_custom_action_code": action_codes.udp_custom_action_code,
                "udp_tyre_delta_action_code": action_codes.udp_tyre_delta_action_code,
                "toggle_overlays_udp_action_code": action_codes.toggle_all_overlays_udp_action_code,
                "cycle_mfd_udp_action_code": action_codes.cycle_mfd_udp_action_code,
                "prev_mfd_page_udp_action_code": action_codes.prev_mfd_page_udp_action_code,
                "lap_timer_toggle_udp_action_code": action_codes.lap_timer_toggle_udp_action_code,
                "timing_tower_toggle_udp_action_code": action_codes.timing_tower_toggle_udp_action_code,
                "mfd_toggle_udp_action_code": action_codes.mfd_toggle_udp_action_code,
                "track_radar_overlay_toggle_udp_action_code": action_codes.track_radar_overlay_toggle_udp_action_code,
                "input_overlay_toggle_udp_action_code": action_codes.input_overlay_toggle_udp_action_code,
                "mfd_interaction_udp_action_code": action_codes.mfd_interaction_udp_action_code,
            }
        })
    }
}
