# Tests

Dependencies are managed with Poetry.

## Quick Start

From the repository root:

```bash
poetry run python tests/unit_tests.py
```

This is the primary test entrypoint and runs the unit test suite with the custom colored test runner.

## Run A Single Test Module

The test files import `tests_base` as a local module, so module-level runs are easiest from the `tests/` directory:

```bash
cd tests
poetry run python -m unittest tests_event_counter
```

## Run A Single Test Class

From `tests/`:

```bash
poetry run python -m unittest tests_event_counter.TestEventCounter
```

## Run A Single Test Case

From `tests/`:

```bash
poetry run python -m unittest tests_event_counter.TestEventCounter.test_one_negative_latency_among_five_packets
```

## Profiling Test Execution

`tests/unit_tests.py` supports profiling:

```bash
poetry run python tests/unit_tests.py --profile
```

## Layout Notes

- `tests/unit_tests.py`: Central test runner.
- `tests/tests_base.py`: Shared base class and custom output formatting.
- `tests/tests_*.py`: Most standalone unit test modules.
- `tests/tests_config/`, `tests/tests_delta/`, `tests/ipc/`: Grouped domain-specific tests.
- `tests/integration_test/`: Integration-level test artifacts.

## Common Issues

- `ModuleNotFoundError: tests_base` during module-level runs:
  - Run from `tests/` as shown above, or use `tests/unit_tests.py` from repo root.
- Permission errors in temp directories:
  - Usually environment/sandbox related; rerun in a local unrestricted shell if needed.
