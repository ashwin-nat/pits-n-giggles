# Tests

Dependencies are managed with Poetry.

## Running the Suite

From the repository root:

```bash
poetry run pytest tests/
```

Parallel-safe tests run across all CPU cores automatically. Serial tests (IPC, sockets,
process management) are funnelled to a single worker. No flags needed.

To force single-process (useful when debugging a specific failure):

```bash
poetry run pytest tests/ -n 0
```

## Running a Subset

```bash
# Single file
poetry run pytest tests/tests_version.py

# By name pattern (class, method, or keyword)
poetry run pytest tests/ -k "TestWatchDogTimerAsync"
poetry run pytest tests/ -k "test_initial_state_idle"

# Only the serial (IPC/socket/process) suites
poetry run pytest tests/ -m serial

# Only the parallel-safe suites
poetry run pytest tests/ -m "not serial"
```

## Coverage Report (local)

```bash
poetry run pytest tests/ --cov=lib --cov-config=scripts/.coveragerc_ut --cov-report=html:reports/coverage
start reports/coverage/index.html   # Windows
open reports/coverage/index.html    # macOS
```

## Allure Report (local)

Requires the Allure CLI installed separately (pick any one):

```bash
npm install -g allure-commandline   # requires Node.js — works on all platforms
scoop install allure                # Windows (Scoop)
brew install allure                 # macOS (Homebrew)
```

Then:

```bash
# Run tests and collect results
poetry run pytest tests/ --alluredir=reports/allure-results

# Generate and open the report in a browser
allure serve reports/allure-results
```

## Layout

| Path | Purpose |
|------|---------|
| `tests_base.py` | Shared `F1TelemetryUnitTestsBase` base class |
| `conftest.py` | pytest config: ignore list, serial→xdist group wiring, VS Code detection |
| `tests_*.py` | Standalone unit test modules |
| `tests_config/` | Config validation tests |
| `tests_delta/` | Lap delta tests |
| `tests_data_per_driver/` | Per-driver data structure tests |
| `tests_wdt/` | Watchdog timer tests (async + sync) |
| `tests_event_counter/` | Event counter and latency stat tests |
| `ipc/` | IPC tests — ZeroMQ pub/sub, router/dealer, parent/child (serial) |
| `integration_test/` | Integration runner — starts the full app, not collected by pytest |
| `unit_tests.py` | Legacy unittest runner — kept for reference, superseded by pytest |

## Serial vs Parallel

Tests marked `@pytest.mark.serial` (via module-level `pytestmark`) bind real sockets,
ports, or spawn processes and must not run concurrently. Everything else is parallel-safe.

Current split: ~131 serial / ~710 parallel out of 841 total.
