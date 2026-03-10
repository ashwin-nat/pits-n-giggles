use std::sync::Arc;
use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

use tokio::time::Instant;

pub struct WatchdogTimer {
    inner: Arc<WatchdogInner>,
    timeout: Duration,
    check_interval: Duration,
}

struct WatchdogInner {
    last_kick: Mutex<Instant>,
    active: AtomicBool,
    stopped: AtomicBool,
    status_callback: Mutex<Box<dyn FnMut(bool) + Send>>,
}

impl WatchdogTimer {
    pub fn new<F>(timeout: Duration, check_interval: Duration, status_callback: F) -> Self
    where
        F: FnMut(bool) + Send + 'static,
    {
        Self {
            inner: Arc::new(WatchdogInner {
                last_kick: Mutex::new(Instant::now()),
                active: AtomicBool::new(false),
                stopped: AtomicBool::new(false),
                status_callback: Mutex::new(Box::new(status_callback)),
            }),
            timeout,
            check_interval,
        }
    }

    pub fn kick(&self) {
        *self.inner.last_kick.lock().expect("watchdog lock poisoned") = Instant::now();
        if !self.inner.active.swap(true, Ordering::SeqCst) {
            self.emit_status(true);
        }
    }

    pub fn stop(&self) {
        self.inner.stopped.store(true, Ordering::SeqCst);
    }

    pub fn is_active(&self) -> bool {
        self.inner.active.load(Ordering::SeqCst)
    }

    pub async fn run(&self) {
        while !self.inner.stopped.load(Ordering::SeqCst) {
            tokio::time::sleep(self.check_interval).await;

            let elapsed = Instant::now().saturating_duration_since(
                *self.inner.last_kick.lock().expect("watchdog lock poisoned"),
            );
            if self.inner.active.load(Ordering::SeqCst) && elapsed > self.timeout {
                self.inner.active.store(false, Ordering::SeqCst);
                self.emit_status(false);
            }
        }
    }

    fn emit_status(&self, status: bool) {
        let mut callback = self
            .inner
            .status_callback
            .lock()
            .expect("watchdog callback lock poisoned");
        (callback)(status);
    }
}

impl Clone for WatchdogTimer {
    fn clone(&self) -> Self {
        Self {
            inner: Arc::clone(&self.inner),
            timeout: self.timeout,
            check_interval: self.check_interval,
        }
    }
}
