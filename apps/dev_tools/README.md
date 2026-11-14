# Dev Tools
Just a collection of tools that make dev life easy

## Running

From the root directory
```bash
poetry run python -m apps.dev_tools.telemetry_replayer --file-name <f1pcap-file-path>
poetry run python -m apps.dev_tools.telemetry_recorder
poetry run python -m apps.dev_tools.compress_pcap <src-file> <dst-file>
poetry run python -m apps.dev_tools.udp_action_code_injector --action-code <code>
poetry run python -m apps.dev_tools.check_save_invariants "data/**/*.json"
poetry run python -m apps.dev_tools.pcap_trace <f1pcap-file-path> [--car N ...] [--all-events] [--json]
```

## Recording Trace

Prints a car's lap and driver status timeline from an `.f1pcap`, straight from the packets, with no app running.
Useful for checking what the game actually sends in a scenario (a flashback landing, an out lap becoming a flying
lap, a garage tyre change) before writing a test for it.

- One line per change of lap number or driver status: overall frame, frame, lap distance, lap time, pit status,
  and the latest fuel, MGU-K harvest this lap, average tyre wear and fitted set
- Fitted set changes and the key events (flashback, session start/end, lights, chequered flag, retirement) in between
- `--car N` traces car N, and can be repeated. Default: the player
- `--all-events` prints every event, not just the key ones
- `--json` prints one JSON object per line instead of the table, for scripts. Each has a `kind`: `info`, `event`,
  `tyre_sets` or `lap`

## Save Invariant Checker

Checks saved session JSON against the state-layer invariants — relationships that must hold
for *any* session, so there is no recorded baseline to maintain. Catches impossible states
(wear decreasing within a stint, gaps between stint boundaries, duplicate positions), not
merely changed ones.

- Takes files, directories or glob patterns
- `-q` / `--quiet` — only print files that have violations
- `--max-violations N` — cap violations printed per file (default 10, `0` for all)
- Exits 1 if any file has a violation

Wear rules are skipped for time trial sessions and for drivers with restricted telemetry,
since neither reports tyre wear. Skips are counted in the per-file summary, so a pass never
hides the fact that nothing was checked.

The same checks run automatically after every replay in `tests/integration_test/runner.py`.

## UDP Action Code Injector

Crafts a synthetic `BUTTON_STATUS` event packet carrying the given UDP action code and sends it to the backend — useful for triggering UDP-action-bound features (e.g. custom markers) without the game running.

- `--action-code <int>` (required) — the UDP action code to inject
- `--ip-addr` (default `127.0.0.1`) and `--port` (default `20777`) — destination server
- Sends over TCP with length-prefix framing by default; pass `--udp-mode` to send as a plain UDP datagram instead