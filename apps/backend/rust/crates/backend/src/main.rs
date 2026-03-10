mod config;

use std::net::SocketAddr;
use std::path::PathBuf;
use std::process;

use backend::{
    BackendConfig, BackendIpcServer, BackendRuntime, CaptureConfig, SharedShutdownState,
    WebServerConfig, serve,
};
use clap::Parser;
use config::BackendFileConfig;
use telemetry_core::{DEFAULT_TELEMETRY_PORT, PacketProcessingOutcome};

const PID_TAG_PREFIX: &str = "<<PNG_LAUNCHER_CHILD_PID:";
const IPC_PORT_TAG_PREFIX: &str = "<<PNG_LAUNCHER_IPC_PORT:";
const INIT_COMPLETE_TAG: &str = "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>";
const DEFAULT_SERVER_PORT: u16 = 4768;

#[derive(Debug, Parser)]
#[command(name = "png-backend")]
#[command(about = "Rust telemetry backend runtime")]
struct Cli {
    #[arg(long)]
    config_file: Option<PathBuf>,

    #[arg(long, default_value = "0.0.0.0")]
    bind_ip: String,

    #[arg(long)]
    telemetry_port: Option<u16>,

    #[arg(long, default_value = "0.0.0.0")]
    server_bind_ip: String,

    #[arg(long)]
    server_port: Option<u16>,

    #[arg(long)]
    replay_server: bool,

    #[arg(long)]
    run_ipc_server: bool,

    #[arg(long)]
    debug: bool,

    #[arg(long = "forward-target")]
    forward_targets: Vec<SocketAddr>,

    #[arg(long)]
    frame_gate: bool,

    #[arg(long, default_value_t = telemetry_core::MIN_SUPPORTED_PACKET_FORMAT)]
    min_packet_format: u16,

    #[arg(long, default_value_t = 250)]
    stats_interval_packets: u64,

    #[arg(long)]
    quiet: bool,

    #[arg(long)]
    show_sample_data_at_start: bool,

    #[arg(long)]
    udp_custom_action_code: Option<u8>,

    #[arg(long)]
    udp_tyre_delta_action_code: Option<u8>,

    #[arg(long)]
    toggle_overlays_udp_action_code: Option<u8>,

    #[arg(long)]
    cycle_mfd_udp_action_code: Option<u8>,

    #[arg(long)]
    prev_mfd_page_udp_action_code: Option<u8>,

    #[arg(long)]
    lap_timer_toggle_udp_action_code: Option<u8>,

    #[arg(long)]
    timing_tower_toggle_udp_action_code: Option<u8>,

    #[arg(long)]
    mfd_toggle_udp_action_code: Option<u8>,

    #[arg(long)]
    track_radar_overlay_toggle_udp_action_code: Option<u8>,

    #[arg(long)]
    input_overlay_toggle_udp_action_code: Option<u8>,

    #[arg(long)]
    mfd_interaction_udp_action_code: Option<u8>,

    #[arg(long)]
    post_race_data_autosave: Option<bool>,

    #[arg(long)]
    post_quali_data_autosave: Option<bool>,

    #[arg(long)]
    post_fp_data_autosave: Option<bool>,

    #[arg(long)]
    post_tt_data_autosave: Option<bool>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    report_pid();

    let file_config = cli
        .config_file
        .as_ref()
        .map(|path| BackendFileConfig::load(path))
        .transpose()?;
    let telemetry_port = cli
        .telemetry_port
        .or(file_config
            .as_ref()
            .and_then(|config| config.network.telemetry_port))
        .unwrap_or(DEFAULT_TELEMETRY_PORT);
    let server_port = cli
        .server_port
        .or(file_config
            .as_ref()
            .and_then(|config| config.network.server_port))
        .unwrap_or(DEFAULT_SERVER_PORT);
    let forward_targets = if cli.forward_targets.is_empty() {
        file_config
            .as_ref()
            .map(BackendFileConfig::forwarding_targets)
            .transpose()?
            .unwrap_or_default()
    } else {
        cli.forward_targets.clone()
    };
    let frame_gate_enabled = cli.frame_gate
        || file_config
            .as_ref()
            .and_then(|config| config.network.enable_pkt_ordering)
            .unwrap_or(false);
    let https_enabled = file_config
        .as_ref()
        .and_then(|config| config.https.enabled)
        .unwrap_or(false);

    let config = BackendConfig {
        frame_gate_enabled,
        min_supported_packet_format: cli.min_packet_format,
        forward_targets,
        udp_custom_action_code: cli.udp_custom_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.network.udp_custom_action_code)),
        udp_tyre_delta_action_code: cli.udp_tyre_delta_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.network.udp_tyre_delta_action_code)),
        toggle_overlays_udp_action_code: cli.toggle_overlays_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.toggle_overlays_udp_action_code)),
        cycle_mfd_udp_action_code: cli.cycle_mfd_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.cycle_mfd_udp_action_code)),
        prev_mfd_page_udp_action_code: cli.prev_mfd_page_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.prev_mfd_page_udp_action_code)),
        lap_timer_toggle_udp_action_code: cli.lap_timer_toggle_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.lap_timer_toggle_udp_action_code)),
        timing_tower_toggle_udp_action_code: cli.timing_tower_toggle_udp_action_code.or(
            file_config
                .as_ref()
                .and_then(|config| config.hud.timing_tower_toggle_udp_action_code),
        ),
        mfd_toggle_udp_action_code: cli.mfd_toggle_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.mfd_toggle_udp_action_code)),
        track_radar_overlay_toggle_udp_action_code: cli
            .track_radar_overlay_toggle_udp_action_code
            .or(file_config
                .as_ref()
                .and_then(|config| config.hud.track_radar_overlay_toggle_udp_action_code)),
        input_overlay_toggle_udp_action_code: cli.input_overlay_toggle_udp_action_code.or(
            file_config
                .as_ref()
                .and_then(|config| config.hud.input_overlay_toggle_udp_action_code),
        ),
        mfd_interaction_udp_action_code: cli.mfd_interaction_udp_action_code.or(file_config
            .as_ref()
            .and_then(|config| config.hud.mfd_interaction_udp_action_code)),
        capture: CaptureConfig {
            post_race_data_autosave: cli
                .post_race_data_autosave
                .or(file_config
                    .as_ref()
                    .and_then(|config| config.capture.post_race_data_autosave))
                .unwrap_or(true),
            post_quali_data_autosave: cli
                .post_quali_data_autosave
                .or(file_config
                    .as_ref()
                    .and_then(|config| config.capture.post_quali_data_autosave))
                .unwrap_or(true),
            post_fp_data_autosave: cli
                .post_fp_data_autosave
                .or(file_config
                    .as_ref()
                    .and_then(|config| config.capture.post_fp_data_autosave))
                .unwrap_or(false),
            post_tt_data_autosave: cli
                .post_tt_data_autosave
                .or(file_config
                    .as_ref()
                    .and_then(|config| config.capture.post_tt_data_autosave))
                .unwrap_or(false),
        },
        ..BackendConfig::default()
    };

    let telemetry_bind_addr = format!("{}:{}", cli.bind_ip, telemetry_port);
    let mut runtime = if cli.replay_server {
        BackendRuntime::bind_tcp(&telemetry_bind_addr, config).await?
    } else {
        BackendRuntime::bind_udp(&telemetry_bind_addr, config).await?
    };
    let shared_state = runtime.state();
    let derived_state = runtime.derived_state();
    let frontend_update_state = runtime.frontend_update_state();
    let control_state = runtime.control_state();
    let shutdown_state = SharedShutdownState::new();
    let shutdown_wait = shutdown_state.clone();
    let mut ipc_server = if cli.run_ipc_server {
        let server = BackendIpcServer::start(
            shared_state.clone(),
            control_state.clone(),
            shutdown_state.clone(),
        )?;
        report_ipc_port(server.port());
        Some(server)
    } else {
        None
    };
    let web_config = WebServerConfig {
        bind_ip: cli.server_bind_ip.clone(),
        port: server_port,
        show_overlay_sample_data_at_start: cli.show_sample_data_at_start,
        https_enabled,
        cert_path: file_config
            .as_ref()
            .and_then(|config| config.https.cert_file_path.as_ref().map(PathBuf::from)),
        key_path: file_config
            .as_ref()
            .and_then(|config| config.https.key_file_path.as_ref().map(PathBuf::from)),
        ..WebServerConfig::default()
    };

    let local_addr = runtime
        .telemetry_manager()
        .receiver()
        .local_addr()
        .map_err(|error| format!("failed to inspect bound address: {error}"))?;

    let mut web_task = tokio::spawn(async move {
        serve(
            shared_state,
            derived_state,
            frontend_update_state,
            control_state,
            shutdown_state,
            web_config,
        )
        .await
    });

    if !cli.quiet {
        eprintln!(
            "telemetry listening on {} via {}",
            local_addr,
            if cli.replay_server { "tcp" } else { "udp" }
        );
        eprintln!(
            "web listening on {}:{} via {}",
            cli.server_bind_ip,
            server_port,
            if https_enabled { "https" } else { "http" },
        );
    }
    notify_init_complete();

    loop {
        tokio::select! {
            result = runtime.next() => {
                match result? {
                    PacketProcessingOutcome::Accepted(packet) => {
                        let snapshot = runtime.state().snapshot();
                        if !cli.quiet && snapshot.packet_count % cli.stats_interval_packets == 0 {
                            eprintln!(
                                "packets={} last={} player={:?} active={:?}",
                                snapshot.packet_count,
                                packet.packet_type(),
                                snapshot.player_index,
                                snapshot.num_active_cars,
                            );
                        }
                    }
                    PacketProcessingOutcome::Dropped(_) => {}
                }
            }
            result = &mut web_task => {
                let web_result = result.map_err(|error| format!("web task join error: {error}"))?;
                web_result?;
                return Err("web server exited unexpectedly".into());
            }
            _ = shutdown_wait.notified() => {
                if !cli.quiet {
                    eprintln!(
                        "shutdown requested: {}",
                        shutdown_wait.reason().unwrap_or_else(|| "N/A".to_string())
                    );
                }
                break;
            }
            result = tokio::signal::ctrl_c() => {
                result?;
                if !cli.quiet {
                    eprintln!("shutdown requested");
                }
                break;
            }
        }
    }

    if let Some(server) = ipc_server.as_mut() {
        server.close();
    }

    Ok(())
}

fn report_pid() {
    println!("{PID_TAG_PREFIX}{}>>", process::id());
}

fn notify_init_complete() {
    println!("{INIT_COMPLETE_TAG}");
}

fn report_ipc_port(port: u16) {
    println!("{IPC_PORT_TAG_PREFIX}{port}>>");
}
