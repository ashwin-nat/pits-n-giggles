import os
import random
import pytest

_GLOBAL_SEED = 42


@pytest.fixture(autouse=True)
def _seed_rng():
    random.seed(_GLOBAL_SEED)

# tests_wdt.py conflicts with the tests_wdt/ package (same base name).
# The package supersedes the file; exclude the file so pytest doesn't choke.
collect_ignore = ["tests_wdt.py"]


def pytest_configure(config):
    # VS Code's pytest extension communicates results via a named pipe that
    # xdist worker subprocesses cannot reach. Disable xdist when that pipe is
    # present so the beaker UI works correctly.
    if os.environ.get("TEST_RUN_PIPE"):
        config.option.numprocesses = 0
        config.option.dist = "no"


def pytest_collection_modifyitems(items):
    # Under xdist (--dist=loadgroup), all serial-marked tests share one group
    # so they land on the same worker and run sequentially. Tests without the
    # mark distribute freely across workers.
    for item in items:
        if item.get_closest_marker("serial"):
            item.add_marker(pytest.mark.xdist_group(name="serial"))
