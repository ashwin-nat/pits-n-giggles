use std::collections::HashMap;
use std::convert::Infallible;
use std::io;
use std::path::{Path, PathBuf};
use std::time::Duration;

use axum::extract::{Query, State};
use axum::http::StatusCode;
use axum::response::sse::{Event, KeepAlive, Sse};
use axum::response::{Html, IntoResponse};
use axum::routing::{get, post};
use axum::{Json, Router};
use axum_server::tls_rustls::RustlsConfig;
use serde::Deserialize;
use serde_json::{Value, json};
use tokio::fs;
use tower_http::services::ServeDir;

use crate::control::SharedBackendControlState;
use crate::derived::{SharedDerivedState, merge_driver_info_json, merge_periodic_update_json};
use crate::frontend_updates::SharedFrontendUpdateState;
use crate::manual_save::save_session_to_disk;
use crate::runtime::SharedSessionState;
use crate::shutdown::SharedShutdownState;

const DEFAULT_SERVER_PORT: u16 = 4768;

#[derive(Clone, Debug)]
pub struct WebServerConfig {
    pub bind_ip: String,
    pub port: u16,
    pub version: String,
    pub show_overlay_sample_data_at_start: bool,
    pub https_enabled: bool,
    pub cert_path: Option<PathBuf>,
    pub key_path: Option<PathBuf>,
    pub frontend_dir: PathBuf,
}

impl Default for WebServerConfig {
    fn default() -> Self {
        Self {
            bind_ip: "0.0.0.0".to_string(),
            port: DEFAULT_SERVER_PORT,
            version: env!("CARGO_PKG_VERSION").to_string(),
            show_overlay_sample_data_at_start: false,
            https_enabled: false,
            cert_path: None,
            key_path: None,
            frontend_dir: PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../frontend"),
        }
    }
}

#[derive(Clone)]
struct AppState {
    session_state: SharedSessionState,
    derived_state: SharedDerivedState,
    frontend_update_state: SharedFrontendUpdateState,
    control_state: SharedBackendControlState,
    shutdown_state: SharedShutdownState,
    version: String,
    show_overlay_sample_data_at_start: bool,
    frontend_dir: PathBuf,
}

pub fn build_router(
    session_state: SharedSessionState,
    derived_state: SharedDerivedState,
    frontend_update_state: SharedFrontendUpdateState,
    control_state: SharedBackendControlState,
    shutdown_state: SharedShutdownState,
    config: WebServerConfig,
) -> Router {
    let css_dir = config.frontend_dir.join("css");
    let js_dir = config.frontend_dir.join("js");
    let app_state = AppState {
        session_state,
        derived_state,
        frontend_update_state,
        control_state,
        shutdown_state,
        version: config.version,
        show_overlay_sample_data_at_start: config.show_overlay_sample_data_at_start,
        frontend_dir: config.frontend_dir,
    };

    Router::new()
        .route("/", get(index_handler))
        .route("/eng-view", get(engineer_view_handler))
        .route("/player-stream-overlay", get(player_stream_overlay_handler))
        .route("/health", get(health_handler))
        .route("/telemetry-info", get(telemetry_info_handler))
        .route("/race-info", get(race_info_handler))
        .route("/driver-info", get(driver_info_handler))
        .route("/stream-overlay-info", get(stream_overlay_info_handler))
        .route("/save-data", post(save_data_handler))
        .route("/control/stats", get(control_stats_handler))
        .route(
            "/control/udp-action-code",
            post(update_udp_action_code_handler),
        )
        .route("/control/shutdown", post(shutdown_handler))
        .route("/frontend-updates", get(frontend_updates_handler))
        .route("/hud-updates", get(hud_updates_handler))
        .route("/events/race-table", get(race_table_events_handler))
        .route("/events/stream-overlay", get(stream_overlay_events_handler))
        .route(
            "/events/frontend-updates",
            get(frontend_updates_events_handler),
        )
        .route("/events/hud-updates", get(hud_updates_events_handler))
        .nest_service("/static/css", ServeDir::new(css_dir))
        .nest_service("/static/js", ServeDir::new(js_dir))
        .with_state(app_state)
}

pub async fn serve(
    session_state: SharedSessionState,
    derived_state: SharedDerivedState,
    frontend_update_state: SharedFrontendUpdateState,
    control_state: SharedBackendControlState,
    shutdown_state: SharedShutdownState,
    config: WebServerConfig,
) -> io::Result<()> {
    let bind_addr = format!("{}:{}", config.bind_ip, config.port);
    let router = build_router(
        session_state,
        derived_state,
        frontend_update_state,
        control_state,
        shutdown_state,
        config.clone(),
    );
    if config.https_enabled {
        let cert_path = config.cert_path.ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidInput,
                "HTTPS is enabled but no certificate path was provided",
            )
        })?;
        let key_path = config.key_path.ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidInput,
                "HTTPS is enabled but no key path was provided",
            )
        })?;
        let tls_config = RustlsConfig::from_pem_file(cert_path, key_path)
            .await
            .map_err(io::Error::other)?;
        axum_server::bind_rustls(bind_addr.parse().map_err(io::Error::other)?, tls_config)
            .serve(router.into_make_service())
            .await
            .map_err(io::Error::other)
    } else {
        let listener = tokio::net::TcpListener::bind(&bind_addr).await?;
        axum::serve(listener, router)
            .await
            .map_err(io::Error::other)
    }
}

#[derive(Deserialize)]
struct UpdateUdpActionCodeRequest {
    action_code_field: String,
    value: Option<u8>,
}

#[derive(Deserialize)]
struct ShutdownRequest {
    reason: Option<String>,
}

async fn index_handler(State(state): State<AppState>) -> impl IntoResponse {
    render_page_response(
        state.frontend_dir.join("html/driver-view.html"),
        state.version.clone(),
        true,
    )
    .await
}

async fn engineer_view_handler(State(state): State<AppState>) -> impl IntoResponse {
    render_page_response(
        state.frontend_dir.join("html/eng-view.html"),
        state.version.clone(),
        true,
    )
    .await
}

async fn player_stream_overlay_handler(State(state): State<AppState>) -> impl IntoResponse {
    render_page_response(
        state.frontend_dir.join("html/player-stream-overlay.html"),
        state.version.clone(),
        true,
    )
    .await
}

async fn health_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(state.session_state.with_read(|session_state| {
        json!({
            "connected-to-sim": session_state.connected_to_sim,
            "packet-count": session_state.packet_count,
            "session-uid": session_state.session_info.session_uid,
            "num-active-cars": session_state.num_active_cars,
        })
    }))
}

async fn telemetry_info_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(current_telemetry_value(&state))
}

async fn race_info_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(
        state
            .session_state
            .with_read(|session_state| session_state.race_info_json()),
    )
}

async fn driver_info_handler(
    State(state): State<AppState>,
    Query(params): Query<HashMap<String, String>>,
) -> impl IntoResponse {
    let Some(index) = params.get("index") else {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({
                "error": "Missing parameter",
                "message": "Expected query parameter `index`",
            })),
        )
            .into_response();
    };

    let Ok(index) = index.parse::<usize>() else {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({
                "error": "Invalid parameter value",
                "message": "Expected integer query parameter `index`",
                "index": index,
            })),
        )
            .into_response();
    };

    match state
        .session_state
        .with_read(|session_state| session_state.driver_info_json(index))
    {
        Some(mut value) => {
            merge_driver_info_json(&mut value, index, &state.derived_state.snapshot());
            (StatusCode::OK, Json(value)).into_response()
        }
        None => (
            StatusCode::NOT_FOUND,
            Json(json!({
                "error": "Invalid parameter value",
                "message": "Invalid index",
                "index": index,
            })),
        )
            .into_response(),
    }
}

async fn stream_overlay_info_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(current_stream_overlay_value(&state))
}

async fn save_data_handler(State(state): State<AppState>) -> impl IntoResponse {
    match save_session_to_disk(state.session_state.clone(), &state.version).await {
        Ok(value) => {
            let status = match value.get("status").and_then(Value::as_str) {
                Some("success") => StatusCode::OK,
                _ => StatusCode::BAD_REQUEST,
            };
            (status, Json(value)).into_response()
        }
        Err(error) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({
                "status": "error",
                "message": format!("Failed to write session info: {error}"),
            })),
        )
            .into_response(),
    }
}

async fn control_stats_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(json!({
        "status": "success",
        "stats": state.control_state.stats_json(),
        "health": state.session_state.with_read(|session_state| {
            json!({
                "connected-to-sim": session_state.connected_to_sim,
                "packet-count": session_state.packet_count,
                "session-uid": session_state.session_info.session_uid,
                "num-active-cars": session_state.num_active_cars,
            })
        }),
    }))
}

async fn update_udp_action_code_handler(
    State(state): State<AppState>,
    Json(payload): Json<UpdateUdpActionCodeRequest>,
) -> impl IntoResponse {
    match state
        .control_state
        .update_action_code(&payload.action_code_field, payload.value)
    {
        Ok(()) => (
            StatusCode::OK,
            Json(json!({
                "status": "success",
                "stats": state.control_state.stats_json(),
            })),
        )
            .into_response(),
        Err(message) => (
            StatusCode::BAD_REQUEST,
            Json(json!({
                "status": "failure",
                "message": message,
            })),
        )
            .into_response(),
    }
}

async fn shutdown_handler(
    State(state): State<AppState>,
    payload: Option<Json<ShutdownRequest>>,
) -> impl IntoResponse {
    let reason = payload
        .and_then(|payload| payload.reason.clone())
        .unwrap_or_else(|| "HTTP shutdown request".to_string());
    state.shutdown_state.request_shutdown(reason.clone());
    (
        StatusCode::OK,
        Json(json!({
            "status": "success",
            "reason": reason,
        })),
    )
        .into_response()
}

async fn frontend_updates_handler(
    State(state): State<AppState>,
    Query(params): Query<HashMap<String, String>>,
) -> impl IntoResponse {
    let after = params
        .get("after")
        .and_then(|value| value.parse::<u64>().ok());
    Json(json!({
        "entries": state.frontend_update_state.frontend_entries_after(after),
    }))
}

async fn hud_updates_handler(
    State(state): State<AppState>,
    Query(params): Query<HashMap<String, String>>,
) -> impl IntoResponse {
    let after = params
        .get("after")
        .and_then(|value| value.parse::<u64>().ok());
    Json(json!({
        "entries": state.frontend_update_state.hud_entries_after(after),
    }))
}

async fn race_table_events_handler(
    State(state): State<AppState>,
) -> Sse<impl futures_core::Stream<Item = Result<Event, Infallible>>> {
    sse_stream(
        state,
        "race-table-update",
        current_telemetry_value,
        |state| {
            let derived_state = state.derived_state.snapshot();
            let session_packet_count = state
                .session_state
                .with_read(|session_state| session_state.packet_count);
            (session_packet_count, derived_state.source_packet_count)
        },
    )
}

async fn stream_overlay_events_handler(
    State(state): State<AppState>,
) -> Sse<impl futures_core::Stream<Item = Result<Event, Infallible>>> {
    sse_stream(
        state,
        "stream-overlay-update",
        current_stream_overlay_value,
        |state| {
            let session_packet_count = state
                .session_state
                .with_read(|session_state| session_state.packet_count);
            (session_packet_count, 0)
        },
    )
}

async fn frontend_updates_events_handler(
    State(state): State<AppState>,
) -> Sse<impl futures_core::Stream<Item = Result<Event, Infallible>>> {
    let frontend_update_state = state.frontend_update_state.clone();
    let stream = async_stream::stream! {
        let mut last_id = None;
        loop {
            let entries = frontend_update_state.frontend_entries_after(last_id);
            if !entries.is_empty() {
                for entry in entries {
                    last_id = Some(entry.id);
                    yield Ok(Event::default()
                        .event("frontend-update")
                        .json_data(entry.payload.clone())
                        .expect("frontend update event should serialize"));
                }
            }
            tokio::time::sleep(Duration::from_millis(150)).await;
        }
    };

    Sse::new(stream).keep_alive(
        KeepAlive::new()
            .interval(Duration::from_secs(15))
            .text("keep-alive-text"),
    )
}

async fn hud_updates_events_handler(
    State(state): State<AppState>,
) -> Sse<impl futures_core::Stream<Item = Result<Event, Infallible>>> {
    let frontend_update_state = state.frontend_update_state.clone();
    let stream = async_stream::stream! {
        let mut last_id = None;
        loop {
            let entries = frontend_update_state.hud_entries_after(last_id);
            if !entries.is_empty() {
                for entry in entries {
                    last_id = Some(entry.id);
                    let Some(event_name) = entry.payload.get("message-type").and_then(Value::as_str) else {
                        continue;
                    };
                    yield Ok(Event::default()
                        .event(event_name)
                        .json_data(entry.payload.clone())
                        .expect("hud update event should serialize"));
                }
            }
            tokio::time::sleep(Duration::from_millis(150)).await;
        }
    };

    Sse::new(stream).keep_alive(
        KeepAlive::new()
            .interval(Duration::from_secs(15))
            .text("keep-alive-text"),
    )
}

async fn render_page_response(
    path: PathBuf,
    version: String,
    live_data_mode: bool,
) -> impl IntoResponse {
    match fs::read_to_string(&path).await {
        Ok(content) => (
            StatusCode::OK,
            Html(render_template(content, &version, live_data_mode)),
        )
            .into_response(),
        Err(error) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({
                "error": "Template read failed",
                "message": error.to_string(),
                "path": path.display().to_string(),
            })),
        )
            .into_response(),
    }
}

fn render_template(template: String, version: &str, live_data_mode: bool) -> String {
    let template = apply_conditional_block(
        &template,
        "{% if live_data_mode %}",
        "{% endif %}",
        live_data_mode,
    );
    let template = apply_conditional_block(
        &template,
        "{% if not live_data_mode %}",
        "{% endif %}",
        !live_data_mode,
    );

    template
        .replace(
            "{{ 'Live' if live_data_mode else 'Save Data' }}",
            if live_data_mode { "Live" } else { "Save Data" },
        )
        .replace("{{ version }}", version)
        .replace("{{ url_for('static', filename='", "/static/")
        .replace("') }}", "")
}

fn apply_conditional_block(
    template: &str,
    block_start: &str,
    block_end: &str,
    include_inner: bool,
) -> String {
    let mut output = template.to_string();
    while let Some(start) = output.find(block_start) {
        let search_from = start + block_start.len();
        let Some(relative_end) = output[search_from..].find(block_end) else {
            break;
        };
        let end = search_from + relative_end;
        let replacement = if include_inner {
            output[search_from..end].to_string()
        } else {
            String::new()
        };
        output.replace_range(start..end + block_end.len(), &replacement);
    }
    output
}

fn current_telemetry_value(state: &AppState) -> Value {
    let derived_state = state.derived_state.snapshot();
    state.session_state.with_read(|session_state| {
        let mut value = session_state.periodic_update_json();
        merge_periodic_update_json(&mut value, &derived_state);
        value
    })
}

fn current_stream_overlay_value(state: &AppState) -> Value {
    state.session_state.with_read(|session_state| {
        session_state.stream_overlay_json(state.show_overlay_sample_data_at_start)
    })
}

fn sse_stream<F, V>(
    state: AppState,
    event_name: &'static str,
    value_builder: V,
    version_fn: F,
) -> Sse<impl futures_core::Stream<Item = Result<Event, Infallible>>>
where
    F: Fn(&AppState) -> (u64, u64) + Send + Sync + 'static,
    V: Fn(&AppState) -> Value + Send + Sync + 'static,
{
    let stream = async_stream::stream! {
        let mut interval = tokio::time::interval(Duration::from_millis(100));
        let mut last_version = (u64::MAX, u64::MAX);
        loop {
            interval.tick().await;
            let version = version_fn(&state);
            if version == last_version {
                continue;
            }
            last_version = version;
            let payload = value_builder(&state);
            yield Ok(Event::default().event(event_name).json_data(payload).expect("serialize sse payload"));
        }
    };

    Sse::new(stream).keep_alive(KeepAlive::new().interval(Duration::from_secs(3)))
}

#[allow(dead_code)]
fn _ensure_path(_path: &Path, _value: &Value) {}
