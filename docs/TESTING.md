# Testing

This document outlines the different types of tests used in this project and how to run them.

The project currently has **609 unit tests** covering the core library and application logic.

## 1. Unit Tests

Unit tests cover most of the code under the `lib/` directory.

To run unit tests:
```bash
poetry run python tests/unit_tests.py
```

To run unit tests with code coverage:
```bash
poetry run python scripts/coverage_ut.py
```

### Coverage Reports

The coverage scripts generate an HTML report in the `htmlcov/` directory. Open
`htmlcov/index.html` in a browser to inspect line-by-line coverage.

A baseline coverage run (excluding integration tests) is available via:
```bash
poetry run python scripts/coverage_base.py
```

## 2. Integration Tests

Integration tests cover the main application code, specifically `apps/backend` and `lib/`.

To run integration tests:
```bash
poetry run python tests/integration_test/runner.py
```

To run integration tests with code coverage:
```bash
poetry run python scripts/coverage_integration_tests.py
```
