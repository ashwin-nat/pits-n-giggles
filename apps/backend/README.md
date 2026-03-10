# Pits n' Giggles Backend

The backend now lives in Rust under [`apps/backend/rust`](/Users/vankata/Desktop/Projects/pits-n-giggles/apps/backend/rust).

What it owns:
- telemetry ingest
- packet parsing and dispatch
- shared session state
- frontend HTTP/SSE routes
- launcher IPC control
- autosave and packet forwarding

## Running

From the project root:

```bash
cargo run --manifest-path apps/backend/rust/Cargo.toml -p backend --
```

Replay mode:

```bash
cargo run --manifest-path apps/backend/rust/Cargo.toml -p backend -- --replay-server
```

Launcher-compatible mode:

```bash
cargo run --manifest-path apps/backend/rust/Cargo.toml -p backend -- --config-file config/settings.json --run-ipc-server
```

## Layout

- [`apps/backend/rust/crates/f1-types`](/Users/vankata/Desktop/Projects/pits-n-giggles/apps/backend/rust/crates/f1-types)
- [`apps/backend/rust/crates/telemetry-core`](/Users/vankata/Desktop/Projects/pits-n-giggles/apps/backend/rust/crates/telemetry-core)
- [`apps/backend/rust/crates/state`](/Users/vankata/Desktop/Projects/pits-n-giggles/apps/backend/rust/crates/state)
- [`apps/backend/rust/crates/backend`](/Users/vankata/Desktop/Projects/pits-n-giggles/apps/backend/rust/crates/backend)

The legacy Python backend has been removed. The launcher and packaged builds now start the Rust backend directly.
