use std::collections::VecDeque;
use std::sync::{Arc, RwLock};

use serde::Serialize;
use serde_json::{Value, json};

const MAX_FRONTEND_UPDATES: usize = 256;

fn is_frontend_message_type(message_type: &str) -> bool {
    matches!(
        message_type,
        "custom-marker" | "tyre-delta" | "tyre-delta-v2" | "final-classification-notification"
    )
}

fn is_hud_message_type(message_type: &str) -> bool {
    matches!(
        message_type,
        "hud-toggle-notification"
            | "hud-cycle-mfd-notification"
            | "hud-prev-page-mfd-notification"
            | "hud-mfd-interaction-notification"
    )
}

#[derive(Clone, Debug, Serialize)]
pub struct FrontendUpdateEntry {
    pub id: u64,
    pub payload: Value,
}

#[derive(Clone, Debug, Default)]
struct FrontendUpdateState {
    next_id: u64,
    entries: VecDeque<FrontendUpdateEntry>,
}

#[derive(Clone, Default)]
pub struct SharedFrontendUpdateState(Arc<RwLock<FrontendUpdateState>>);

impl SharedFrontendUpdateState {
    pub fn new() -> Self {
        Self(Arc::new(RwLock::new(FrontendUpdateState::default())))
    }

    pub fn push(&self, payload: Value) {
        let mut guard = self.0.write().expect("frontend update state poisoned");
        let id = guard.next_id;
        guard.next_id = guard.next_id.saturating_add(1);
        guard.entries.push_back(FrontendUpdateEntry { id, payload });
        while guard.entries.len() > MAX_FRONTEND_UPDATES {
            guard.entries.pop_front();
        }
    }

    pub fn entries_after(&self, last_id: Option<u64>) -> Vec<FrontendUpdateEntry> {
        self.entries_after_matching(last_id, |_| true)
    }

    pub fn frontend_entries_after(&self, last_id: Option<u64>) -> Vec<FrontendUpdateEntry> {
        self.entries_after_matching(last_id, is_frontend_message_type)
    }

    pub fn hud_entries_after(&self, last_id: Option<u64>) -> Vec<FrontendUpdateEntry> {
        self.entries_after_matching(last_id, is_hud_message_type)
    }

    fn entries_after_matching(
        &self,
        last_id: Option<u64>,
        predicate: impl Fn(&str) -> bool,
    ) -> Vec<FrontendUpdateEntry> {
        let guard = self.0.read().expect("frontend update state poisoned");
        guard
            .entries
            .iter()
            .filter(|entry| last_id.is_none_or(|last_id| entry.id > last_id))
            .filter(|entry| {
                entry
                    .payload
                    .get("message-type")
                    .and_then(Value::as_str)
                    .is_some_and(|message_type| predicate(message_type))
            })
            .cloned()
            .collect()
    }

    pub fn clear(&self) {
        let mut guard = self.0.write().expect("frontend update state poisoned");
        guard.entries.clear();
    }

    pub fn push_custom_marker(&self, marker: Value) {
        self.push(json!({
            "message-type": "custom-marker",
            "message": marker,
        }));
    }

    pub fn push_final_classification_notification(&self, player_position: u8) {
        self.push(json!({
            "message-type": "final-classification-notification",
            "message": {
                "player-position": player_position,
            },
        }));
    }

    pub fn push_tyre_delta_notification(&self, message: Value) {
        self.push(json!({
            "message-type": "tyre-delta-v2",
            "message": message,
        }));
    }

    pub fn push_hud_toggle_notification(&self, oid: &str) {
        self.push(json!({
            "message-type": "hud-toggle-notification",
            "message": {
                "oid": oid,
            },
        }));
    }

    pub fn push_hud_cycle_mfd_notification(&self) {
        self.push(json!({
            "message-type": "hud-cycle-mfd-notification",
            "message": {
                "dummy": "dummy",
            },
        }));
    }

    pub fn push_hud_prev_page_mfd_notification(&self) {
        self.push(json!({
            "message-type": "hud-prev-page-mfd-notification",
            "message": {
                "dummy": "dummy",
            },
        }));
    }

    pub fn push_hud_mfd_interaction_notification(&self) {
        self.push(json!({
            "message-type": "hud-mfd-interaction-notification",
            "message": {
                "dummy": "dummy",
            },
        }));
    }
}
