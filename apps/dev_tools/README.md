# Dev Tools
Just a collection of tools that make dev life easy

## Running

From the root directory
```bash
poetry run python -m apps.dev_tools.telemetry_replayer --file-name <f1pcap-file-path>
poetry run python -m apps.dev_tools.telemetry_recorder
poetry run python -m apps.dev_tools.compress_pcap <src-file> <dst-file>
poetry run python -m apps.dev_tools.udp_action_code_injector --action-code <code>
```

## UDP Action Code Injector

Crafts a synthetic `BUTTON_STATUS` event packet carrying the given UDP action code and sends it to the backend — useful for triggering UDP-action-bound features (e.g. custom markers) without the game running.

- `--action-code <int>` (required) — the UDP action code to inject
- `--ip-addr` (default `127.0.0.1`) and `--port` (default `20777`) — destination server
- Sends over TCP with length-prefix framing by default; pass `--udp-mode` to send as a plain UDP datagram instead