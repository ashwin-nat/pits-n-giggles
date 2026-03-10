use std::sync::{Arc, RwLock};

use tokio::sync::Notify;

#[derive(Clone, Debug, Default)]
pub struct SharedShutdownState {
    notify: Arc<Notify>,
    reason: Arc<RwLock<Option<String>>>,
}

impl SharedShutdownState {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn request_shutdown(&self, reason: String) {
        *self.reason.write().expect("shutdown state poisoned") = Some(reason);
        self.notify.notify_waiters();
    }

    pub async fn notified(&self) {
        self.notify.notified().await;
    }

    pub fn reason(&self) -> Option<String> {
        self.reason.read().expect("shutdown state poisoned").clone()
    }
}
