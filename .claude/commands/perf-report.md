---
description: Generate a performance metrics report by extracting stats from the perf DB or launcher log file
allowed-tools: Read, Grep, Glob, Bash(python3:*)
---

Generate a full telemetry performance metrics report by extracting stats from the perf metrics DB (default) or a launcher log file (fallback/explicit).

## Input

Resolve the data source in this order:

1. If the user provides a `.db` path → use DB extraction (below).
2. If the user provides a `.log` path or explicitly says "use log file" → use log extraction (below).
3. Otherwise, use the Glob tool to search for `png_perf.db` in the project root. If found, use DB extraction.
4. If not found, search for `png.log` in the project root. If found, use log extraction.
5. If neither is found, ask the user for a path.

## Steps

1. **Extract the stats JSON.**

   **From the DB (default):**

   Use `scripts/perf_extract.py`. It has two modes:

   - **List sessions** — shows all IDs and timestamps so you can identify the right one:
     ```
     python scripts/perf_extract.py png_perf.db --list
     ```
   - **Fetch latest** — most recent row by `id DESC`, fastest option:
     ```
     python scripts/perf_extract.py png_perf.db --latest
     ```
   - **Fetch a specific session** — by row ID or closest timestamp:
     ```
     python scripts/perf_extract.py png_perf.db --fetch --id 7
     python scripts/perf_extract.py png_perf.db --fetch --time 17:15
     ```

   Use `--latest` when the user asks for the latest/most recent session or gives no qualifier. If the user mentions a specific session (e.g. "the run around 17:15" or "session 3"), run `--list` first to confirm, then `--fetch` with the appropriate qualifier.

   **From the log file (fallback/explicit):**

   The launcher writes final subsystem stats to the log on shutdown. Search for the marker string `"Final subsystem stats: "`. The line looks like:

   ```
   [2025-01-01 12:00:00.000] [INFO] Pits n' Giggles vX.Y.Z shutdown complete (forced=False). Final subsystem stats: {...json...}
   ```

   ```python
   import json, sys

   log_path = sys.argv[1]
   marker = "Final subsystem stats: "
   stats = None

   with open(log_path) as f:
       for line in f:
           if marker in line:
               json_str = line[line.index(marker) + len(marker):]
               stats = json.loads(json_str.strip())

   if stats is None:
       print("ERROR: marker not found in log file", file=sys.stderr)
       sys.exit(1)

   print(json.dumps(stats, indent=2))
   ```

   If multiple matching lines exist (multiple sessions in one log), use the **last** one.
   If the marker is not found, tell the user and stop.

2. **Compute all metrics** from the extracted stats dict:

   **Message Loss Rate** (per topic):
   ```
   loss_rate = (sent - received) / sent * 100
   ```
   - `sent` = `stats["Core"]["egress"]["ipc_pub"]["__OUTGOING__"]["__TOPIC_OUTGOING__"][topic]["count"]`
   - `received` = `stats["HUD"]["ingress"]["subscriber"][topic]["__PACKETS__"]["count"]`

   **Latency** (per topic from `stats["HUD"]["ingress"]["subscriber"][topic]["__LATENCY__"]`):
   - p50, p95, p99 in µs (divide `_ns` values by 1000)
   - tail_ratio = p99 / p50

   **Handler success rate**:
   ```
   rate = handler_ok / (handler_ok + handler_errors) * 100
   ```
   from `stats["HUD"]["ingress"]["subscriber"]["__TOTAL__"]`

   **Frame timing** (per overlay from `stats["HUD"]["overlays"]`):
   - avg FPS, missed frame %, pacing error

   **Broker traffic**:
   - Total packets and bytes from `stats["Pit Wall"]["__OVERALL__"]["traffic"]`

3. **Apply health thresholds**:
   - ✓ loss < 1%, latency p99 < 2ms, tail ratio < 2.0, handler success > 99%, FPS within ±5%
   - ⚠ loss > 2%, p99 > 5ms, tail > 3.0, FPS < 95%
   - 🚩 loss > 10%, p99 > 10ms, handler success < 95%, missed frames > 70%

4. **Output a complete markdown report** with these sections:
   1. **Executive Summary** — 1-2 sentences on overall health
   2. **Ingress (Core → Broker)** — UDP packet counts, types processed, dropped (frame gate + parser)
   3. **Egress (Core → Broker)** — IPC publish totals, per-topic breakdown, reconnections
   4. **Ingress (Broker → HUD)** — subscriber totals, loss rate, missed messages, stale drops, per-topic
   5. **Latency Analysis** — p50/p95/p99/tail ratio per topic, with ✓/⚠/🚩
   6. **HUD Processing Pipeline** — frame timing, FPS accuracy, missed frame %, command latency per overlay
   7. **Broker Statistics** — overall traffic, per-topic packets/bytes, subscription events
   8. **System Health Summary** — table of all major metrics with status indicators
   9. **Observations & Recommendations** — what's healthy, what needs watching

Output the report directly to the terminal in markdown. Do not write it to a file unless the user asks.
