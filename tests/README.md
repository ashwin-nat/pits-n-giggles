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

Tests run in a shuffled order, a new one each run (pytest-randomly), so a test that leans on another's leftovers
fails rather than passing by luck. Modules are shuffled, then the tests within each. The same seed also seeds `random`
before each test (from the seed and the test's id), so a test's random values change from run to run too. The run's
header (`Using --randomly-seed=2836115104`) and its last line (`Rerun with --randomly-seed=2836115104`, shown under
`-q` too) print the seed, and it reruns that order and those values. Allure results carry it as a `seed` label on
every test, so a report, and each run in its history, says which seed it ran with:

```bash
poetry run pytest tests/ --randomly-seed=2836115104          # rerun that order and those values
poetry run pytest tests/ --randomly-seed=last                # rerun the last run's
poetry run pytest tests/ --randomly-dont-reorganize          # file order, random still seeded
```

`-p no:randomly` also gives file order, but leaves `random` unseeded, so a failure there may not reproduce.

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

# Live API tests (OpenF1 schema checks) — requires network, excluded from default run
poetry run pytest tests/tests_openf1/tests_openf1_integration.py -m openf1 -v -n 0
```

## Coverage Report (local)

```bash
poetry run pytest tests/ --cov --cov-config=scripts/.coveragerc_ut --cov-report=html:reports/coverage
start reports/coverage/index.html   # Windows
open reports/coverage/index.html    # macOS
```

What is measured is set in `scripts/.coveragerc_ut`: `lib/`, plus the backend's
`state_mgmt_layer/` (without `intf/`) and `telemetry_layer/`, which `tests_session_state/` drives. Pass
a bare `--cov`. `--cov=<path>` replaces the config's `source` list rather than adding to it.

Alongside `index.html`, coverage.py also writes `function_index.html` and
`class_index.html` — the same data grouped per function and per class, which is the
quicker way to find an untested method on a class that is otherwise well covered.

Worst-covered modules as text, from whatever `.coverage` is already on disk:

```bash
poetry run coverage report --rcfile=scripts/.coveragerc_ut --sort=cover --skip-covered
```

Everything below is optional and reads the same `.coverage` file — none of it needs a
second test run.

### Directory-Level Rollup and Trend (optional)

coverage.py's own HTML index is a flat file list. For per-directory numbers
(`lib.ipc.pubsub`, `lib.subsystem`, ...) plus a coverage trend chart, render the
Cobertura XML with [ReportGenerator](https://github.com/danielpalme/ReportGenerator).
It is a .NET tool but language-agnostic, and needs the .NET SDK installed once:

```bash
dotnet tool install -g dotnet-reportgenerator-globaltool
```

Then, after any run that produced a `.coverage`:

```bash
poetry run coverage xml -i --rcfile=scripts/.coveragerc_ut -o reports/coverage.xml

reportgenerator \
    -reports:reports/coverage.xml \
    -targetdir:reports/coverage-rg \
    -historydir:reports/coverage-history \
    -reporttypes:"Html_Dark;MarkdownSummaryGithub" \
    -title:"Pits n' Giggles - unit test coverage"

start reports/coverage-rg/index.html
```

`coverage xml` maps each measured directory to a Cobertura `<package>`, which is
what gives the per-directory table. Keeping `-historydir` across runs appends one point
per invocation, so the trend chart fills in over time — delete the directory to reset
it. `MarkdownSummaryGithub` also writes `reports/coverage-rg/SummaryGithub.md`, handy
for pasting into a PR. Method coverage is a paid ReportGenerator feature and shows as
unavailable; line and branch coverage are not.

### Diff Coverage (optional)

Coverage over only the lines a branch changed. `diff-cover` is already in the dev group,
so no extra install:

```bash
poetry run coverage xml -i --rcfile=scripts/.coveragerc_ut -o reports/coverage.xml

poetry run diff-cover reports/coverage.xml \
    --compare-branch=main \
    --html-report reports/diff-coverage.html
```

This is the more useful number when reviewing a refactor: the whole-repo percentage
barely moves, but it will show newly written lines that no test touches.

`-i` on `coverage xml` is deliberate in both cases. It skips entries pointing at source
files that no longer exist, which otherwise abort the report after a branch switch or a
refactor that deleted a module. If a report comes out thinner than expected, re-run the
suite for fresh data rather than trusting a stale `.coverage`.

Everything written under `reports/` is gitignored.

## Allure Report (local)

Requires the Allure 3 CLI (Node.js). `allure-commandline` and the Scoop/Homebrew packages are Allure 2:

```bash
npm install -g allure@3.33.0
```

Then:

```bash
# Clear old results. Not --clean-alluredir: every xdist worker runs it, racing the others' writes
rm -rf reports/allure-results

# Run tests and collect results (add the --cov flags above to feed the coverage reports from the same run)
poetry run pytest tests/ --alluredir=reports/allure-results

# Build the report from scripts/allurerc.yaml, append the run to history, and open it
allure generate -c scripts/allurerc.yaml --clean --open
```

`allure open -c scripts/allurerc.yaml` re-serves the last report without regenerating it.

Each `generate` appends one line to `reports/allure-history.jsonl`, which drives the trend charts and flaky
detection (capped at 200 runs). Deleting `reports/` wholesale resets it. To keep it, delete only
`reports/allure-results/` or `reports/allure-report/`.

Allure has no xfail status. `allure-pytest` reports xfail as skipped, so the strict xfail known bugs are grouped
under the "Known bugs (xfail)" category instead.

The report tree groups tests by epic > feature > story > track (`groupBy` in `scripts/allurerc.yaml`). Suites that
set Allure labels, such as `tests_session_state/`, get their own tree. For every other test, `tests/conftest.py`
fills in folder > file > class.

A test's docstring is its description in the report. `tests/conftest.py` dedents it, since Markdown would render the
source indent as a code block. New tests also get an `@allure.title`, a sentence saying what the test shows. Its
`{placeholders}` take any test argument, parameters and fixtures included, e.g. `"Lap analyzer switched {switch}
mid-lap ({track.name}, {packet_format})"`. Without one, the report shows the function name.

Allure 3 identifies a test by its name plus its *displayed* parameter values (`repr()`, not the pytest `ids`). So
parametrize over plain values (`str`, numbers, enums):
- `bytes` all display as `<class 'bytes'>`, which merges the cases into one test with "retries". Use `str` and
  `.encode()` inside the test.
- Functions and objects without a `__repr__` display with a memory address, so the case is "new" on every run and
  has no history. Parametrize over a name and look the object up inside the test.

## Layout

| Path | Purpose |
|------|---------|
| `tests_base.py` | Shared `F1TelemetryUnitTestsBase` base class |
| `conftest.py` | pytest config: ignore list, serial→xdist group wiring, VS Code detection |
| `tests_*.py` | Standalone unit test modules |
| `tests_config/` | Config validation tests |
| `tests_delta/` | Lap delta tests |
| `tests_data_per_driver/` | Per-driver data structure tests |
| `tests_session_state/` | Session state scenarios - typed packets through the real handler and `SessionState`. See [its README](tests_session_state/README.md) |
| `tests_wdt/` | Watchdog timer tests (async + sync) |
| `tests_event_counter/` | Event counter and latency stat tests |
| `ipc/` | IPC tests — ZeroMQ pub/sub, router/dealer, parent/child (serial) |
| `tests_openf1/` | OpenF1 API tests — mock-based flow tests + live schema validation (`-m openf1`) |
| `integration_test/` | Integration runner — starts the full app, not collected by pytest. See [its README](integration_test/README.md) |

## Session State Scenarios

`tests_session_state/` drives typed packets through the real `F1TelemetryHandler` and `SessionState`. Backend
state and session handling tests go there. Its [README](tests_session_state/README.md) covers how to add a test, the
practices to follow, the fixtures and the report labels.

## Serial vs Parallel

Tests marked `@pytest.mark.serial` (via module-level `pytestmark`) bind real sockets,
ports, or spawn processes and must not run concurrently. Everything else is parallel-safe.

Current split: ~131 serial / ~710 parallel out of 841 total.

---

## Test Style: Existing vs New

### Why existing tests are in backward-compatibility mode

The existing suite was written against `unittest.TestCase` (and
`unittest.IsolatedAsyncioTestCase` for async tests). pytest runs these natively with
zero code changes — `self.assertEqual`, `setUp`/`tearDown`, `subTest`, and async test
methods all work as-is. The suite was migrated to pytest for parallel execution,
reporting, and CI integration, not to rewrite working tests. The effort to convert
~840 existing tests to native pytest style is high with no functional payoff.

### How to write new tests

New test files should use native pytest style — no base class required:

```python
# Sync test
def test_something():
    result = my_function()
    assert result == expected

# Parametrized
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
])
def test_doubles(input, expected):
    assert double(input) == expected

# Async test — no decorator needed, asyncio_mode=auto picks it up
async def test_async_thing():
    result = await my_coroutine()
    assert result == expected
```

Use plain `assert` instead of `self.assert*` — pytest rewrites assertions to give
detailed failure output automatically.

### A note on async tests

Existing async tests use `unittest.IsolatedAsyncioTestCase`, which creates a **fresh
event loop per test method**. This is correct and safe, but slightly slower than
`pytest-asyncio`'s configurable loop scoping.

For new async tests, use `pytest-asyncio` — `asyncio_mode = "auto"` is set in
`pyproject.toml` so any `async def test_*` is collected automatically with no decorator
needed. It integrates with pytest fixtures and requires no base class.
