# Session State Harness

These tests cover the backend's state layer as a whole. A scenario builds typed packets, injects them into the real
`F1TelemetryHandler` and `SessionState`, and asserts on the resulting state and on what the handler asked the
outside world to do (saves, tokens, process pool calls). The socket, parser and raw-packet path are skipped.
Everything from the frame gate onward is production code.

```text
Packets (packet_helpers.py) -> InjectingTelemetryManager.inject() -> F1TelemetryHandler -> SessionState
```

Backend state and session handling tests go here. Don't stand in for `SessionState` or `DataPerDriver` with
`MagicMock` or `SimpleNamespace`. Pure value objects (init, `toJSON`, `repr`) can still have plain unit tests
elsewhere, using real objects.

Running, test order, coverage and the Allure report are in [../README.md](../README.md).

```bash
poetry run pytest tests/tests_session_state/ -q                 # the harness, in parallel
poetry run pytest tests/tests_session_state/ -n 0 -k "<name>"   # one test, in one process, for debugging
poetry run pytest tests/tests_session_state/ -rx -q             # list the known bugs (strict xfails)
```

## Files

| File | What's in it |
| --- | --- |
| `conftest.py` | The fixtures below |
| `harness.py` | `InjectingTelemetryManager`, `FakeSubsystem`, the recorders, `PlayerCar`, the session and track constants, and the shared packet sequences |
| `packet_helpers.py` | `Packets` (typed packet builders bound to a packet format) and the per-car specs: `car()`, `player()`, `ai()`, `classified()`, `damage()`, `fuel_and_ers()`, `speed()`, `world_position()`, `lap_time()` |
| `tests_lap_boundaries.py` | Lap boundaries: which samples the lap recorder keeps, and under which lap |
| `tests_flashbacks.py` | Flashbacks across the lap recorder, the delta manager and the per-lap snapshots |
| `tests_lap_rebaseline.py` | Per-lap re-baseline: the lap-0 snapshot, a stint's starting wear, the per-lap stats |
| `tests_tyre_change.py` | Tyre change: pending set changes, the tyre set history, flashbacks across it |
| `tests_frame_gate_scenarios.py` | Frame gate: several packets of one type on one frame |
| `tests_session_handling.py` | Session handling: the session UID gate, the same-UID restart check, the saves they request |
| `tests_pngt_save_gate.py` | `.pngt` save gate: when a lap telemetry save is made, and what goes into it |
| `tests_race_end.py` | Race end: the AI lap timer reset at the flag, and the recorder's rollback cases |
| `tests_unified_save.py` | Unified save: one container per save, gating, claims, concurrency, `stop()` |

## Adding a test

1. **Find the mechanism in a recording first.** `test_data/` holds real captures, named
   `f1_<yy>_<sp|mp>_<session>_<circuit>_<meta>.f1pcap`. `apps/dev_tools/pcap_trace` prints a car's lap, status,
   tyre set and session timeline from one:

   ```bash
   poetry run python -m apps.dev_tools.pcap_trace test_data/f1_26_sp_quali_suzuka_flashback_mid_lap.f1pcap
   poetry run python -m apps.dev_tools.pcap_trace <file> --car 2 --all-events --json
   ```

   Take the packet sequence and values from there: what the game sends is the point. Name the recording, and the
   overall frame when it helps, in the docstring. If no recording has the mechanism, build the sequence, say so in
   the docstring, and note what a recording would need to show.
2. **Pick the module by feature.** Add a module only when no feature fits. A new module sets
   `pytestmark = allure.feature("...")`, since collection fails for a test without a feature. Use
   `@allure.story("...")` for each section of a file.
3. **Pick the fixtures.** `player_car` for the player's laps. `manager`, `packets` and `state` for several cars, or
   for packets `PlayerCar` doesn't send. `saves`, `tokens` and `fake_subsystem` for what the handler asks for.
4. **Parametrize only where it means something:**
   - **Session type:** `@pytest.mark.parametrize("session", [FP, QUALI])` with `FP`, `QUALI`, `RACE`, `TT` and
     `ALL_SESSIONS` from `harness.py`. List only the session types the mechanism exists in, as the recordings show
     it (table below).
   - **Track:** anything that touches per-lap history or snapshots runs on both topologies. Take `track` (or
     `player_car`, which takes it), which runs on Silverstone (normal, finish line before the pit garage) and Monaco
     (weird, pit garage before the line). `tests_tyre_change.py` overrides it to add an unrecognised track.
   - **Packet format:** format-independent logic runs on every format, with
     `@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)` (or in the module's `pytestmark`).
     Rows pinned to one game's numbers stay on the default (2026) or pin their format.
   - **Save format:** `@SAVE_FORMATS` only on tests that assert a save is made. A test that asserts nothing is saved
     gains nothing from the second format.
   - Parametrize over plain values (`str`, numbers, enums). Allure keys a test's history on its displayed
     parameters, so a function or object without a `__repr__` makes the case new on every run. Parametrize over a
     name and look the object up inside the test, as `SENSOR_SOURCES` in `tests_lap_boundaries.py` does.
5. **Title and docstring.** A lap scenario (one taking `session`, `track` and `packet_format`) uses
   `@title("...")` from `harness.py`, which appends the session, track and format. Others use
   `@allure.title("... ({packet_format})")`, with any test argument as a placeholder. The docstring is the report's
   description: first what's injected, then a paragraph starting `Expected:`.
6. **Assert state directly** (`state.m_driver_data[i]...`, `player_car.completed_laps()`), not through JSON, and
   don't add production getters for a test. Keep assert messages for asserts whose failure isn't obvious.
7. **Check that it can fail.** Break the code under test (swap a field, drop a branch), run the test, and see it
   fail, then restore the code. A scenario that passes either way tests nothing.
8. **Run the harness and pylint** before handing it in:

   ```bash
   poetry run pytest tests/tests_session_state/ -q
   poetry run pylint --rcfile scripts/.pylintrc tests/tests_session_state
   ```

A scenario:

```python
@allure.story("Out lap to flying lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A first run's lap starts at the line, not the garage")
async def test_out_lap_to_flying_lap_starts_the_lap(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. Garage, an out lap counting up from -5581 m to the line, then a flying lap.

    Expected: when lap 2 starts, lap 1 is stored holding only the flying lap's samples, from 0.6 m."""
    await player_car.session(session)
    await player_car.drive(GARAGE, 1, 228.7)
    await player_car.drive(OUT_LAP, 1, -5581.1, -2900.0, -1.2)
    await player_car.drive(FLYING, 1, 0.6, 2900.0, 5800.0)
    await player_car.drive(FLYING, 2, 0.6)

    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0]}
```

Without `player_car`, inject packets yourself:

```python
await manager.inject(packets.session(session_uid=100, session_type="RACE", track=TrackID.Silverstone,
                                     total_laps=5, track_length=5891))
await manager.inject(packets.lap(car(0, lap=1, lap_distance=1000), car(1, lap=1, lap_distance=900), session_uid=100))
```

## Practices

- **Extend the helpers, don't reach around them.** Packet helper arguments are only the fields some scenario sets.
  When a scenario needs another field, add it as an explicit argument in the same change, rather than setting it on
  the packet afterwards. A packet sequence used in two places becomes a `harness.py` function (`flashback()`,
  `button_events()`) or a `PlayerCar` method.
- **Wait for saves with `saves_finished(handler)`**, not `asyncio.sleep(0)`. A unified save runs part of its work in a
  thread, so one loop turn doesn't finish it.
- **Don't depend on test order.** Tests run shuffled. Rerun a failing order with the `--randomly-seed=N` the run
  prints at the end.
- **Nothing touches the real data directory.** `user_data_dir` points every save at `tmp_path`. Don't write
  anywhere else.
- **Lap distances are float32 on the wire.** `PlayerCar` rounds what it reads back to 0.1 m. Compare raw values at
  float32 precision.
- **Generators and constructed sequences stay within what the game can send.** For example, a flashback goes back at
  most one lap: the buffer is about 30 s and the shortest lap about 1:02. A test that goes past that on purpose says
  so in its docstring, as a robustness check (`test_flashback_two_laps_back_drops_both_laps`).
- **Known bugs are strict xfails**: `@pytest.mark.xfail(strict=True, reason="...")`, with a reason saying what's
  wrong, or `request.applymarker(...)` inside the test when only some cases are affected. A fix flips them to XPASS,
  which fails the run, so the fix also removes the marker.
- **Docstrings say how to use a thing. Comments state why, in at most two lines.**

## Fixtures

| Fixture | What it is |
|---------|------------|
| `manager` | `InjectingTelemetryManager` with the handler's callbacks registered. `await manager.inject(packet)` |
| `packets` | Packet helpers bound to `packet_format` (default 2026). Frames count up on their own |
| `frame_gate_enabled` | False by default. `@pytest.mark.parametrize("frame_gate_enabled", [True], indirect=True)` turns the frame gate on |
| `state`, `handler` | The real `SessionState` and `F1TelemetryHandler`. `handler` is stopped at teardown, which waits for its save tasks |
| `save_task_stop_timeout_s` | 5 s by default, how long the handler's `stop()` waits for each save task. `@pytest.mark.parametrize("save_task_stop_timeout_s", [0.01], indirect=True)` shortens it |
| `settings` | Every session type autosaves and records laps, every lap analyzer sensor on, just-in-case saves on |
| `unified_save` | False by default (separate JSON and `.pngt` files, as the app ships). `@pytest.mark.parametrize("unified_save", [True], indirect=True)` turns on `Capture.unified_save_format`, and `harness.SAVE_FORMATS` runs a test on both |
| `saves` | Records save requests as (trigger, content, session UID), e.g. `("just_in_case", "pngt", 100)`, the same on either save format: separate-files saves write nothing, and each half of a unified container counts as a JSON or `.pngt` request. Triggers are `final_classification`, `just_in_case` and `manual`. Also keeps each `.pngt` save's `write_session()` args (`pngt_args`), and, once the task runs, the JSON's debug block (`json_debug`) and the `.pngt` name (`pngt_names`) |
| `tokens` | Records the handler's `report_*_from_child` tokens (save skipped, session saved, `.pngt` save start and end) |
| `fake_subsystem` | Records `fire_and_forget` names, `dealer.fire` calls and `run_in_process` calls (where unified saves land), runs nothing. `block()` / `release()` / `fail_with()` control when a `run_in_process` call finishes. `run_in_process` pickles its args as the real process pool does |
| `user_data_dir` | Autouse. `lib.file_path.get_app_base_dir` points at `tmp_path`, so every `resolve_user_file` lands there and nothing is written under the real `data/` |
| `track` | Both `LAP_TRACKS` (Silverstone normal, Monaco weird), so a test on `player_car` runs on each. A module can override it, as `tests_tyre_change.py` does to add an unrecognised track |
| `player_car` | `harness.PlayerCar`, the player's car on `track`. `session()`, `baseline()`, `drive(status, lap, *distances)`, `flashback(status, lap, distance)`, `car_status()`, `car_damage()`, `tyre_sets()`, `speed()` and `position()` send packets. `completed_laps()`, `in_progress_lap()`, `delta_laps()`, `stints()` and `fuel(lap)` read the lap recorder, the delta manager, the tyre set history and the per-lap snapshots |
| `caplog` | Wired to the real `PngLogger` the state layer uses |

`harness.py` also has the driver status aliases (`GARAGE`, `OUT_LAP`, `FLYING`, `IN_LAP`, `ON_TRACK`),
`racing_status(session)` and `leaving_garage_status(session)` for the statuses that differ between session types,
`flashback()` and `button_events()` for any car, and `saves_finished(handler)`.

## Session types

`FP`, `QUALI`, `RACE` and `TT` are `SessionType24` members. `PlayerCar.session()` passes the name on, and `Packets`
picks `SessionType23`'s value for 2023, where RACE and TIME_TRIAL are numbered differently. What the recordings show
for each:

| Session type | Garage | Out lap -> flying lap | Flashbacks |
| --- | --- | --- | --- |
| `FP` (Practice 1) | yes | yes | yes |
| `QUALI` (Short Qualifying) | yes | yes | yes |
| `RACE` | no | no: ON_TRACK from the grid on | yes |
| `TT` (Time Trial) | at the start | no: the garage goes straight to FLYING_LAP at a negative distance | none recorded |

Select one with `-k "Practice 1"`.

## Report labels

Every test here sits under the "Session state" epic, with its file's feature and its section's story. A track case
built with `track_param(track, kind)` is tagged "normal track", "weird track" or "unknown track". Select one kind with
`--allure-label track=weird` or `-k weird`, and features or stories with `--allure-features` and
`--allure-stories`.

Each injected packet is a report step, nested under the scenario step that sent it (a `PlayerCar.drive()` call,
`Race.flashback()`, ...). A test that does not pass also gets every packet it injected attached as one JSON file,
"injected packets".
