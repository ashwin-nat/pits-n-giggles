# MCP Server

Exposes live F1 telemetry from Pits n' Giggles as MCP tools.

## Transports

| Mode | Transport | When |
|------|-----------|------|
| Standalone / inspector | **stdio** | launched directly (no `--managed` flag) |
| Managed | **HTTP (SSE)** | launched by the Launcher with `--managed` |

## Testing with MCP Inspector

### Prerequisites

- Node.js installed (`node --version` to verify)
- `png_config.json` present in the repo root (run the Launcher once to generate it)
- Poetry environment set up (`poetry install`)

---

### stdio transport

#### Run the inspector

From the repo root:

```bash
npx @modelcontextprotocol/inspector poetry run python -m apps.mcp_server
```

This launches MCP Inspector in your browser and spawns the MCP server as a stdio subprocess. The inspector proxies JSON-RPC over the subprocess's stdin/stdout.

#### Optional flags

```bash
# Enable debug logging (written to png_mcp_stdio.log by default)
npx @modelcontextprotocol/inspector poetry run python -m apps.mcp_server -- --debug

# Custom log file
npx @modelcontextprotocol/inspector poetry run python -m apps.mcp_server -- --log-file my_debug.log

# Custom config file
npx @modelcontextprotocol/inspector poetry run python -m apps.mcp_server -- --config-file path/to/png_config.json
```

> **Note:** Arguments after `--` are passed to the MCP server process, not to the inspector.

#### Logs

stdio-mode logs go to `png_mcp_stdio.log` in the working directory (unless `--log-file` overrides it). Tail this file in a second terminal to watch tool calls in real time:

```bash
# Linux/macOS
tail -f png_mcp_stdio.log

# Windows (PowerShell)
Get-Content png_mcp_stdio.log -Wait
```

---

### HTTP transport

The HTTP server is the transport used when the MCP server is managed by the Launcher (`--managed`). You can also start it manually for testing without the full Launcher stack.

#### Start the server manually

```bash
poetry run python -m apps.mcp_server --managed --debug
```

The `--managed` flag switches the transport to HTTP. The server binds on `127.0.0.1:<mcp_http_port>` (default **4770**, configured in `png_config.json` under `MCP.mcp_http_port`).

> **Note:** `--managed` also tries to notify a parent process via IPC. When run standalone this IPC call is a no-op, so it is safe to ignore any IPC-related log lines.

#### Verify the server is up

```bash
curl http://localhost:4770/test
```

Expected response:

```json
{"message": "Pits n' Giggles MCP Server v<version>"}
```

#### Connect MCP Inspector to the running HTTP server

Open MCP Inspector and point it at the running server's MCP endpoint:

```bash
npx @modelcontextprotocol/inspector
```

When the inspector UI opens, switch the transport to **SSE** and enter:

```
http://localhost:4770/mcp
```

Click **Connect**. The inspector will negotiate the MCP session over SSE and list all available tools.

#### Logs

HTTP-mode logs (when `--managed`) are written as JSONL to stdout, captured by the parent process. When running manually for testing, redirect stdout to a file:

```bash
poetry run python -m apps.mcp_server --managed --debug 2>&1 | tee mcp_http.log
```

---

### What to expect (both transports)

1. The inspector opens at `http://localhost:5173` (default port).
2. Under **Tools**, you will see all registered tools:
   - `get_session_info`
   - `get_race_table`
   - `get_drivers_list`
   - `get_driver_lap_times`
   - `get_session_events_for_driver`
   - `get_player_driver_info`
   - `get_car_damage`
3. Tools that require a live session return `"available": false` when no telemetry is active. This is expected — no errors will be shown.
4. Tools that hit the core backend (`get_driver_lap_times`, `get_session_events_for_driver`, `get_car_damage`) additionally call the backend REST API on `localhost:<server_port>`. These return `"ok": false` with an appropriate error if the backend is not running.

## Architecture notes

- **`mcp_main.py`** — entry point; parses args, selects transport (`stdio` when unmanaged, `http` when `--managed`).
- **`mcp_server/mcp_server.py`** — `MCPBridge`: owns the `FastMCP` instance, registers tools, runs the server loop.
- **`mcp_server/tools/`** — one file per tool; pure functions that read from `apps.mcp_server.state` or call the backend REST API.
- **`subscriber.py`** — subscribes to the ZeroMQ broker and feeds live telemetry into the shared state store.
- **`state.py`** — in-process key/value store for telemetry snapshots published by the subscriber.
