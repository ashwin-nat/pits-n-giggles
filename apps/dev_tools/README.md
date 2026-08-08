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
```

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