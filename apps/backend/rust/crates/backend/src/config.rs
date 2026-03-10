use std::fs;
use std::io;
use std::net::SocketAddr;
use std::path::Path;

use serde::Deserialize;

#[derive(Debug, Default, Deserialize)]
pub struct BackendFileConfig {
    #[serde(default, rename = "Network")]
    pub network: NetworkConfig,
    #[serde(default, rename = "Capture")]
    pub capture: CaptureConfig,
    #[serde(default, rename = "Forwarding")]
    pub forwarding: ForwardingConfig,
    #[serde(default, rename = "HUD")]
    pub hud: HudConfig,
    #[serde(default, rename = "HTTPS")]
    pub https: HttpsConfig,
}

impl BackendFileConfig {
    pub fn load(path: &Path) -> io::Result<Self> {
        let raw = fs::read_to_string(path)?;
        serde_json::from_str(&raw).map_err(|error| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("failed to parse config file {}: {error}", path.display()),
            )
        })
    }

    pub fn forwarding_targets(&self) -> io::Result<Vec<SocketAddr>> {
        let mut targets = Vec::new();
        for value in [
            self.forwarding.target_1.as_deref(),
            self.forwarding.target_2.as_deref(),
            self.forwarding.target_3.as_deref(),
        ]
        .into_iter()
        .flatten()
        {
            let trimmed = value.trim();
            if trimmed.is_empty() {
                continue;
            }
            let target = trimmed.parse::<SocketAddr>().map_err(|error| {
                io::Error::new(
                    io::ErrorKind::InvalidData,
                    format!("invalid forwarding target `{trimmed}`: {error}"),
                )
            })?;
            targets.push(target);
        }
        Ok(targets)
    }
}

#[derive(Debug, Default, Deserialize)]
pub struct NetworkConfig {
    pub telemetry_port: Option<u16>,
    pub server_port: Option<u16>,
    pub udp_tyre_delta_action_code: Option<u8>,
    pub udp_custom_action_code: Option<u8>,
    pub enable_pkt_ordering: Option<bool>,
}

#[derive(Debug, Default, Deserialize)]
pub struct CaptureConfig {
    pub post_race_data_autosave: Option<bool>,
    pub post_quali_data_autosave: Option<bool>,
    pub post_fp_data_autosave: Option<bool>,
    pub post_tt_data_autosave: Option<bool>,
}

#[derive(Debug, Default, Deserialize)]
pub struct ForwardingConfig {
    pub target_1: Option<String>,
    pub target_2: Option<String>,
    pub target_3: Option<String>,
}

#[derive(Debug, Default, Deserialize)]
pub struct HudConfig {
    pub toggle_overlays_udp_action_code: Option<u8>,
    pub cycle_mfd_udp_action_code: Option<u8>,
    pub prev_mfd_page_udp_action_code: Option<u8>,
    pub lap_timer_toggle_udp_action_code: Option<u8>,
    pub timing_tower_toggle_udp_action_code: Option<u8>,
    pub mfd_toggle_udp_action_code: Option<u8>,
    pub track_radar_overlay_toggle_udp_action_code: Option<u8>,
    pub input_overlay_toggle_udp_action_code: Option<u8>,
    pub mfd_interaction_udp_action_code: Option<u8>,
}

#[derive(Debug, Default, Deserialize)]
pub struct HttpsConfig {
    pub enabled: Option<bool>,
    pub key_file_path: Option<String>,
    pub cert_file_path: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::BackendFileConfig;

    #[test]
    fn parses_backend_relevant_sections() {
        let config = serde_json::from_str::<BackendFileConfig>(
            r#"{
                "Network": {
                    "telemetry_port": 30000,
                    "server_port": 40000,
                    "udp_custom_action_code": 5,
                    "enable_pkt_ordering": true
                },
                "Capture": {
                    "post_race_data_autosave": false
                },
                "Forwarding": {
                    "target_1": "127.0.0.1:20778",
                    "target_2": ""
                },
                "HUD": {
                    "mfd_toggle_udp_action_code": 9
                },
                "HTTPS": {
                    "enabled": true,
                    "key_file_path": "/tmp/key.pem",
                    "cert_file_path": "/tmp/cert.pem"
                }
            }"#,
        )
        .unwrap();

        assert_eq!(config.network.telemetry_port, Some(30000));
        assert_eq!(config.network.server_port, Some(40000));
        assert_eq!(config.network.udp_custom_action_code, Some(5));
        assert_eq!(config.network.enable_pkt_ordering, Some(true));
        assert_eq!(config.capture.post_race_data_autosave, Some(false));
        assert_eq!(
            config.forwarding_targets().unwrap(),
            vec!["127.0.0.1:20778".parse().unwrap()]
        );
        assert_eq!(config.hud.mfd_toggle_udp_action_code, Some(9));
        assert_eq!(config.https.enabled, Some(true));
        assert_eq!(config.https.key_file_path.as_deref(), Some("/tmp/key.pem"));
        assert_eq!(
            config.https.cert_file_path.as_deref(),
            Some("/tmp/cert.pem")
        );
    }
}
