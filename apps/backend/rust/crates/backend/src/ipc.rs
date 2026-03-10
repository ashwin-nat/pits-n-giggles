use std::io;
use std::str;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use serde_json::{Value, json};
use tokio::runtime::Handle;

use crate::control::SharedBackendControlState;
use crate::manual_save::save_session_to_disk;
use crate::runtime::SharedSessionState;
use crate::shutdown::SharedShutdownState;

const IPC_SERVER_NAME: &str = "Backend";
const PNG_LOST_CONN_TO_PARENT: i32 = 101;

pub struct BackendIpcServer {
    port: u16,
    running: Arc<AtomicBool>,
    server_thread: Option<JoinHandle<()>>,
    heartbeat_thread: Option<JoinHandle<()>>,
}

impl BackendIpcServer {
    pub fn start(
        session_state: SharedSessionState,
        control_state: SharedBackendControlState,
        shutdown_state: SharedShutdownState,
    ) -> io::Result<Self> {
        let context = zmq::Context::new();
        let socket = context.socket(zmq::REP).map_err(io::Error::other)?;
        socket.bind("tcp://127.0.0.1:*").map_err(io::Error::other)?;
        let endpoint = socket.get_last_endpoint().map_err(io::Error::other)?;
        let endpoint = match endpoint {
            Ok(endpoint) => endpoint,
            Err(endpoint) => str::from_utf8(&endpoint)
                .map_err(io::Error::other)?
                .to_string(),
        };
        let port = endpoint
            .rsplit(':')
            .next()
            .ok_or_else(|| io::Error::other("invalid ipc endpoint"))?
            .parse::<u16>()
            .map_err(io::Error::other)?;

        let running = Arc::new(AtomicBool::new(true));
        let last_heartbeat = Arc::new(Mutex::new(Some(Instant::now())));
        let missed_heartbeats = Arc::new(AtomicU32::new(0));
        let runtime_handle = Handle::current();

        let heartbeat_thread = {
            let running = running.clone();
            let last_heartbeat = last_heartbeat.clone();
            let missed_heartbeats = missed_heartbeats.clone();
            thread::Builder::new()
                .name("png-ipc-heartbeat".to_string())
                .spawn(move || {
                    while running.load(Ordering::Relaxed) {
                        thread::sleep(Duration::from_secs(5));
                        if !running.load(Ordering::Relaxed) {
                            break;
                        }

                        let Some(last) =
                            *last_heartbeat.lock().expect("ipc heartbeat mutex poisoned")
                        else {
                            continue;
                        };
                        if last.elapsed() > Duration::from_secs(5) {
                            let missed = missed_heartbeats.fetch_add(1, Ordering::Relaxed) + 1;
                            if missed >= 3 {
                                std::process::exit(PNG_LOST_CONN_TO_PARENT);
                            }
                        }
                    }
                })
                .map_err(io::Error::other)?
        };

        let server_thread = {
            let running = running.clone();
            let last_heartbeat = last_heartbeat.clone();
            let missed_heartbeats = missed_heartbeats.clone();
            thread::Builder::new()
                .name("png-ipc-server".to_string())
                .spawn(move || {
                    while running.load(Ordering::Relaxed) {
                        let mut items = [socket.as_poll_item(zmq::POLLIN)];
                        if zmq::poll(&mut items, 100).is_err() {
                            continue;
                        }
                        if !items[0].is_readable() {
                            continue;
                        }

                        let response = match socket.recv_bytes(0) {
                            Ok(bytes) => match serde_json::from_slice::<Value>(&bytes) {
                                Ok(message) => handle_ipc_message(
                                    message,
                                    &runtime_handle,
                                    &session_state,
                                    &control_state,
                                    &shutdown_state,
                                    &running,
                                    &last_heartbeat,
                                    &missed_heartbeats,
                                ),
                                Err(error) => json!({
                                    "status": "error",
                                    "message": error.to_string(),
                                }),
                            },
                            Err(error) => json!({
                                "status": "error",
                                "message": error.to_string(),
                            }),
                        };

                        let _ = socket.send(
                            serde_json::to_vec(&response).unwrap_or_else(|_| {
                                b"{\"status\":\"error\",\"message\":\"serialization failure\"}"
                                    .to_vec()
                            }),
                            0,
                        );
                    }
                })
                .map_err(io::Error::other)?
        };

        Ok(Self {
            port,
            running,
            server_thread: Some(server_thread),
            heartbeat_thread: Some(heartbeat_thread),
        })
    }

    pub fn port(&self) -> u16 {
        self.port
    }

    pub fn close(&mut self) {
        self.running.store(false, Ordering::Relaxed);
        if let Some(thread) = self.server_thread.take() {
            let _ = thread.join();
        }
        if let Some(thread) = self.heartbeat_thread.take() {
            let _ = thread.join();
        }
    }
}

impl Drop for BackendIpcServer {
    fn drop(&mut self) {
        self.close();
    }
}

#[allow(clippy::too_many_arguments)]
fn handle_ipc_message(
    message: Value,
    runtime_handle: &Handle,
    session_state: &SharedSessionState,
    control_state: &SharedBackendControlState,
    shutdown_state: &SharedShutdownState,
    running: &Arc<AtomicBool>,
    last_heartbeat: &Arc<Mutex<Option<Instant>>>,
    missed_heartbeats: &Arc<AtomicU32>,
) -> Value {
    let cmd = message.get("cmd").and_then(Value::as_str);
    let args = message
        .get("args")
        .cloned()
        .unwrap_or_else(|| Value::Object(serde_json::Map::new()));

    match cmd {
        Some("__heartbeat__") => {
            *last_heartbeat.lock().expect("ipc heartbeat mutex poisoned") = Some(Instant::now());
            missed_heartbeats.store(0, Ordering::Relaxed);
            json!({
                "status": "success",
                "reply": "__heartbeat_ack__",
                "source": IPC_SERVER_NAME,
            })
        }
        Some("__ping__") => json!({
            "reply": "__pong__",
            "source": IPC_SERVER_NAME,
        }),
        Some("__terminate__") => {
            running.store(false, Ordering::Relaxed);
            json!({
                "status": "success",
                "message": "terminated",
            })
        }
        Some("__shutdown__") => {
            let reason = args
                .get("reason")
                .and_then(Value::as_str)
                .unwrap_or("N/A")
                .to_string();
            shutdown_state.request_shutdown(reason);
            running.store(false, Ordering::Relaxed);
            json!({
                "status": "success",
            })
        }
        Some("manual-save") => runtime_handle.block_on(async {
            match save_session_to_disk(session_state.clone(), env!("CARGO_PKG_VERSION")).await {
                Ok(value) => value,
                Err(error) => json!({
                    "status": "error",
                    "message": format!("Failed to write session info: {error}"),
                }),
            }
        }),
        Some("udp-action-code-change") => {
            let field = args
                .get("action_code_field")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let value = args
                .get("value")
                .and_then(Value::as_u64)
                .and_then(|value| u8::try_from(value).ok());
            match control_state.update_action_code(field, value) {
                Ok(()) => json!({
                    "status": "success",
                }),
                Err(message) => json!({
                    "status": "failure",
                    "message": message,
                }),
            }
        }
        Some("get-stats") => json!({
            "status": "success",
            "stats": {
                "__CONTROL__": control_state.stats_json(),
                "__HEALTH__": session_state.with_read(|state| json!({
                    "connected-to-sim": state.connected_to_sim,
                    "packet-count": state.packet_count,
                    "session-uid": state.session_info.session_uid,
                    "num-active-cars": state.num_active_cars,
                })),
            },
        }),
        Some(command) => json!({
            "status": "error",
            "message": format!("Unknown command: {command}"),
        }),
        None => json!({
            "status": "error",
            "message": "Missing command name",
        }),
    }
}
