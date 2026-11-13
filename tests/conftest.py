import os
import random
from pathlib import Path

import allure
import pytest
from allure_commons.types import LabelType

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


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    # The report tree groups by epic > feature > story. Tests that set none are grouped by folder > file > class
    tests_dir = Path(__file__).parent
    for item in session.items:
        if any(mark.kwargs.get("label_type") == LabelType.EPIC for mark in item.iter_markers(name="allure_label")):
            continue
        folder = item.path.parent.relative_to(tests_dir).as_posix()
        item.add_marker(allure.epic(folder if folder != "." else "tests"))
        item.add_marker(allure.feature(item.path.name))
        if item.cls is not None:
            item.add_marker(allure.story(item.cls.__name__))
