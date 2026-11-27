---
description: Debug a telemetry bug from a symptom to a tested fix - inspect recordings offline, replay through the app when needed, and for state bugs write the failing test before the fix
allowed-tools: Read, Grep, Glob, Bash, PowerShell, Edit, Write
---

Debug a bug in how the app handles telemetry: a wrong value in a dashboard, a save, a `.pngt`, the HUD or the
lap analyzer. Work from the symptom inwards, one layer at a time, until the bad value is pinned to the first
layer that produces it. Don't change code until you know which layer that is.

```text
viewer / HUD / save  ->  recorded data (.pngt, save JSON)  ->  app state  ->  parsed packets  ->  raw capture
```

## 1. Pin the symptom to data

Turn "the line looks wrong" into exact values: file, driver index, lap, lap time or session time, and the bad
value next to its neighbours. A table of before / bad / after samples is the evidence everything else is
checked against.

- `.pngt`: `lib.pngt.reader.read_session(path)` gives the laps and their telemetry columns per driver.
- `.pngt` session JSON: `poetry run python -m apps.dev_tools.extract_pngt_session <file> [-o out.json]`.
- Save JSON: `poetry run python -m apps.dev_tools.check_save_invariants <files>` for impossible states.

Note how wide it is: one driver or all of them, one sample or a run, which sensors. "All 22 cars at the same
instant" points at something session-wide (a flashback, a restart), not one car's stream.

## 2. Find the recording

Look in `test_data/` first, named `f1_<yy>_<sp|mp>_<session>_<circuit>_<meta>.f1pcap`. To place the bad sample
in the capture, use its lap and lap time with `pcap_trace --at-lap` (below) rather than adding up lap times.

## 3. Inspect the raw packets offline

Prefer reading the capture directly over replaying it: it is faster, needs no app, and shows every packet.

Timeline of laps, driver status, fitted sets, key events, and rewinds and restarts with the frames and session
times either side:

```bash
poetry run python -m apps.dev_tools.pcap_trace <file> [--car N ...] [--all-events] [--json]
```

Every packet around a moment, in capture order, with the car's values from each packet. A time seen twice (a
flashback) shows both passes:

```bash
poetry run python -m apps.dev_tools.pcap_trace <file> --around <session_time> [--window 0.1] --car N
```

From a `.pngt` sample's lap and lap time straight to the packets, every pass included:

```bash
poetry run python -m apps.dev_tools.pcap_trace <file> --at-lap 5 --lap-time 68.260 --car N
```

Every position spike in the capture, alongside the rewinds that may explain it:

```bash
poetry run python -m apps.dev_tools.pcap_trace <file> --car N --jumps 30
```

For anything else (checking a fix's condition against every packet, say), write a script in the scratchpad (not
the repo) that parses every packet with the app's own parser. The shape:

```python
import logging, sys
sys.path.insert(0, r"<repo root>")
from lib.f1_types import F1PacketType
from lib.packet_cap import F1PacketCapture
from lib.telemetry_manager.factory import PacketParserFactory

cap = F1PacketCapture(file_name=sys.argv[1])
factory = PacketParserFactory(set(F1PacketType), logging.getLogger("x"))
for idx, (ts, raw) in enumerate(cap.getPackets()):
    pkt = factory.parse(raw)
    if pkt is None:
        continue
    h = pkt.m_header
    # filter on h.m_sessionTime / h.m_packetId, print per-car fields such as
    # pkt.m_carMotionData[i], pkt.m_lapData[i], pkt.m_carTelemetryData[i]
```

A typical pass: `--jumps` or `--at-lap` to find the moment, then `--around` it with a wider window. The header
fields name the event:

| Header pattern | Means |
|---|---|
| `frameIdentifier` goes back, `overallFrameIdentifier` keeps counting, same session time seen twice | Flashback; the FLBK event comes just before the landing |
| Both frames back to 0, same session UID | Restart |
| New `sessionUID` | New session |

Also note packet order within a frame. The game sends LAP_DATA before MOTION, CAR_TELEMETRY and CAR_STATUS, so
anything sampled on LAP_DATA sees the previous frame's copies.

**Ours or the game's:** if the raw packet already has the bad value, it's the game (or the capture). If the raw
packets are clean and the app's output isn't, it's ours. Then say which layer: parser, frame gate
(`lib/telemetry_manager/frame_gate.py`), state (`apps/backend/state_mgmt_layer/`), or a consumer.

## 4. Replay through the app, when offline isn't enough

Replay when you need the app's own state, logs or UI: something a packet dump can't show.

1. Add temporary `self.m_logger.debug(...)` calls where the state changes.
2. **Pick a telemetry port that nothing else uses.** Never use 20777, the game's default: the game or another
   telemetry app is likely to be on it. Pick another port, such as 20799, and check it's free
   (`netstat -ano | grep <port>` prints nothing). Copy `png_config.json` to the scratchpad and set
   `Network.telemetry_port` in the copy. Don't edit the user's own config.
3. Start the launcher in replay mode with that config. Never start a subsystem on its own; it fails the
   heartbeat and exits:

   ```bash
   poetry run python -m apps.launcher --replay-server --debug --config-file <scratchpad>/png_config.json
   ```

4. Send the capture to the same port:

   ```bash
   poetry run python -m apps.dev_tools.telemetry_replayer --file-name <file> --port <port>
   ```

   `--udp-mode --speed-multiplier N` replays over UDP at real timing, for timing-sensitive bugs.
5. Read `png.log` in the user data dir.
6. Remove the temporary logs before the fix goes for review. Keep a log only if the user wants it there.

### Sending commands to a running subsystem

`ipc_injector` sends management IPC messages to a subsystem the launcher is running: to ping it, read its stats,
or drive a command without clicking through the UI. Write the message (or a list of them, sent in order) to a
JSON file in the scratchpad. Passing a file avoids shell quoting problems.

```bash
poetry run python -m apps.dev_tools.ipc_injector --port <port> <msg.json>
```

```json
{"cmd": "set-overlays-opacity", "args": {"opacity": 50}}
```

**Finding the port.** Ports change on every run. With `--debug`, take the latest
`<name> IPC port reported: <port>` line in `png.log` (names: Core, Pit Wall, Web, HUD, MCP). Without it, those
lines aren't written: take the subsystem's listening ports from `netstat -ano` and ping them. The reply's
`source` names the owner (`backend`, `pit_wall` for the broker, `web`, `hud`, `mcp`).

**Commands.** `__ping__` and `__get_stats__` work on every subsystem; redirect stats to a file, as the HUD's run
to tens of KB. The rest are the `mgmt.on("<cmd>")` handlers: grep `apps/` for them and read the handler for
its args.

- Exit 0 means every reply had `"status": "success"`. `__ping__` replies have no status, so a good ping exits 1.
- `success` only means the handler ran. Confirm the effect in `png.log` or on screen.
- Commands change the live app. Send the configured value back afterwards, and ask before one that can't be
  put back that way (a real `set-overlays-layout` moves the user's overlays).
- `__shutdown__` and `__terminate__` need `--force`. `__heartbeat__` is always refused.

## 5. Write it up as you go

Findings go in `plans/` (see CLAUDE.md), not only in chat: the evidence table, the packet table that shows
the cause, the root cause in a paragraph, and the fix options with their costs. Hand the user the docs-server
URL and open it. Keep it current through the fix, and mark the issue resolved at the end.

When presenting options, recommend one. For each option, say what else reads the state it touches: a fix in a
shared copy or field can break consumers that the bug never affected.

## 6. Fix a state bug: test first, then the fix

If the bug is in backend state or session handling (`SessionState`, `DataPerDriver`, the lap recorder, flashback
and lap-boundary logic), the test comes before the fix:

1. **Write the scenario** in `tests/tests_session_state/`. Read its `README.md` first and follow it: the right
   module and story, `title()`, a docstring naming the recording and overall frame, session types limited to
   those where the mechanism exists, both tracks for anything touching per-lap history. Send packets in the
   order the game sends them in that frame. Assert the invariant the bug breaks, not the shape of one fix, so
   any correct fix passes it.
2. **Mark it a strict xfail**: `@pytest.mark.xfail(strict=True, reason="<what is wrong>")`.
3. **Prove it catches the bug**: run it normally (every case XFAIL), then one case with `--runxfail -n 0` and
   check that the failure shows the real symptom's values.
4. **Show the test to the user and wait.** Don't start the fix until they've accepted the test.
5. **Fix**, and remove the xfail marker. The test must pass in every case.
6. **Run the gates**: `poetry run pytest tests/tests_session_state/ -q`, then `poetry run pytest tests/ -q`, and
   `poetry run pylint --rcfile scripts/.pylintrc apps lib` at 10.00.
7. **Read every other failure.** Change an existing test's expectation only when the fix is meant to change
   it, and add a one-line comment saying why. Several hundred failures mean the fix is wrong, not the tests.
8. **Check the fix against real recordings.** Run the fix's condition over the original capture and one other
   with the same mechanism, and count what it touches (e.g. "skips 1 of 27 066 LAP_DATA, the landing"). It
   should touch the bug's cases and nothing unexplained.

A bug outside the state layer still gets a failing test first where a test suite exists for it: `tests/` for
`lib/`, `pnpm typecheck` and the viewer's tests for the frontend.

## 7. Hand over

Present the diff for review and commit only after sign-off. Stage and commit in one go. Commit messages and
plans follow the repo rules (no em dashes, no attribution trailers). Run `graphify update .` after code
changes. Say what wasn't run: the integration runner (`/diff-report`) is the gate for changes to recorded data,
and existing `.pngt` or save files keep the bad values from before the fix.
