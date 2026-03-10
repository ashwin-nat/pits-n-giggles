use std::io;
use std::path::PathBuf;

use chrono::Local;
use serde_json::{Value, json};

use crate::runtime::SharedSessionState;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SaveMode {
    Manual,
    AutoFinalClassification,
}

pub async fn save_session_to_disk(
    session_state: SharedSessionState,
    version: &str,
) -> io::Result<Value> {
    save_session_to_disk_with_mode(session_state, version, SaveMode::Manual).await
}

pub async fn save_session_to_disk_with_mode(
    session_state: SharedSessionState,
    version: &str,
    mode: SaveMode,
) -> io::Result<Value> {
    let (event_prefix, save_json) =
        session_state.with_read(|state| (state.event_info_prefix(), state.save_data_json(version)));

    let Some(event_prefix) = event_prefix else {
        return Ok(json!({
            "status": "error",
            "message": "No data available to save",
        }));
    };
    let Some(mut save_json) = save_json else {
        return Ok(json!({
            "status": "error",
            "message": "No data available to save",
        }));
    };

    let now = Local::now();
    let date_str = now.format("%Y_%m_%d").to_string();
    let timestamp_str = now.format("%Y_%m_%d_%H_%M_%S").to_string();
    let file_name = match mode {
        SaveMode::Manual => format!("{event_prefix}Manual_{timestamp_str}.json"),
        SaveMode::AutoFinalClassification => format!("{event_prefix}{timestamp_str}.json"),
    };
    let file_path = PathBuf::from("data")
        .join(date_str)
        .join("race-info")
        .join(&file_name);

    if let Some(object) = save_json.as_object_mut() {
        let debug = object
            .entry("debug".to_string())
            .or_insert_with(|| Value::Object(serde_json::Map::new()));
        if let Some(debug_object) = debug.as_object_mut() {
            debug_object.insert(
                "session-uid".to_string(),
                json!(session_state.with_read(|state| state.session_info.session_uid)),
            );
            debug_object.insert(
                "timestamp".to_string(),
                json!(now.format("%Y-%m-%d %H:%M:%S %:z").to_string()),
            );
            debug_object.insert("timezone".to_string(), json!(now.offset().to_string()));
            debug_object.insert(
                "utc-offset-seconds".to_string(),
                json!(now.offset().local_minus_utc()),
            );
            let reason = match mode {
                SaveMode::Manual => "Manual save",
                SaveMode::AutoFinalClassification => "Auto-save after final classification",
            };
            debug_object.insert("reason".to_string(), json!(reason));
            debug_object.insert(
                "packet-count".to_string(),
                json!(session_state.with_read(|state| state.packet_count)),
            );
            debug_object.insert("file-name".to_string(), json!(file_name));
        }
    }

    if let Some(parent) = file_path.parent() {
        tokio::fs::create_dir_all(parent).await?;
    }
    let payload = serde_json::to_vec(&save_json).map_err(io::Error::other)?;
    tokio::fs::write(&file_path, payload).await?;

    Ok(json!({
        "status": "success",
        "message": format!("Data saved to {}", file_path.display()),
    }))
}
