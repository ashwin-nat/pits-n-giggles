use std::sync::{Arc, Mutex};
use std::time::Duration;

use telemetry_core::WatchdogTimer;

#[tokio::test(start_paused = true)]
async fn watchdog_starts_idle() {
    let transitions = Arc::new(Mutex::new(Vec::new()));
    let timer = WatchdogTimer::new(Duration::from_millis(500), Duration::from_millis(10), {
        let transitions = Arc::clone(&transitions);
        move |state| transitions.lock().expect("lock").push(state)
    });

    let runner = tokio::spawn({
        let timer = timer.clone();
        async move { timer.run().await }
    });

    tokio::time::advance(Duration::from_millis(100)).await;
    tokio::task::yield_now().await;

    assert!(transitions.lock().expect("lock").is_empty());

    timer.stop();
    runner.await.expect("join");
}

#[tokio::test(start_paused = true)]
async fn watchdog_transitions_active_timeout_active() {
    let transitions = Arc::new(Mutex::new(Vec::new()));
    let timer = WatchdogTimer::new(Duration::from_millis(500), Duration::from_millis(10), {
        let transitions = Arc::clone(&transitions);
        move |state| transitions.lock().expect("lock").push(state)
    });

    let runner = tokio::spawn({
        let timer = timer.clone();
        async move { timer.run().await }
    });

    timer.kick();
    tokio::task::yield_now().await;
    assert_eq!(*transitions.lock().expect("lock"), vec![true]);
    assert!(timer.is_active());

    timer.kick();
    tokio::task::yield_now().await;
    assert_eq!(*transitions.lock().expect("lock"), vec![true]);

    tokio::time::advance(Duration::from_millis(1_000)).await;
    tokio::task::yield_now().await;
    assert_eq!(*transitions.lock().expect("lock"), vec![true, false]);
    assert!(!timer.is_active());

    timer.kick();
    tokio::task::yield_now().await;
    assert_eq!(*transitions.lock().expect("lock"), vec![true, false, true]);
    assert!(timer.is_active());

    timer.stop();
    runner.await.expect("join");
}
