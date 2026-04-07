"""Shared pytest fixtures and configuration."""

import json
from pathlib import Path

import pytest

_CFG_PATH = Path(__file__).resolve().parent.parent / "png_config.json"


def _load_network_cfg() -> dict:
    """Load network section from png_config.json (project default config)."""
    if _CFG_PATH.exists():
        with open(_CFG_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("Network", {})
    return {}


@pytest.fixture
def hostname() -> str:
    cfg = _load_network_cfg()
    return cfg.get("bind_address", "localhost")


@pytest.fixture
def port() -> int:
    cfg = _load_network_cfg()
    return cfg.get("server_port", 5000)


@pytest.fixture
def endpoints_config() -> dict:
    """Endpoint -> list of acceptable HTTP status codes."""
    return {
        "/favicon.ico": [200],
        "/tyre-icons/soft.svg": [200],
        "/tyre-icons/super-soft.svg": [200],
        "/tyre-icons/medium.svg": [200],
        "/tyre-icons/hard.svg": [200],
        "/tyre-icons/intermediate.svg": [200],
        "/tyre-icons/wet.svg": [200],
        "/": [200],
        "/eng-view": [200],
        "/player-stream-overlay": [200],
        "/telemetry-info": [200],
        "/race-info": [200],
        "/driver-info?index=0": [200, 404],
        "/stream-overlay-info": [200],
        "/static/css/style.css": [200],
        "/static/css/modals.css": [200],
        "/static/css/weather.css": [200],
        "/static/css/conditions.css": [200],
        "/static/css/speedLimit.css": [200],
        "/static/css/tyreStintHistoryModal.css": [200],
        "/static/js/preferences.js": [200],
        "/static/js/utils.js": [200],
        "/static/js/iconCache.js": [200],
        "/static/js/weatherUI.js": [200],
        "/static/js/graph.js": [200],
        "/static/js/driverDataModalPopulator.js": [200],
        "/static/js/raceStatsModalPopulator.js": [200],
        "/static/js/tyreStintHistoryModal.js": [200],
        "/static/js/modals.js": [200],
        "/static/js/raceTableRowPopulator.js": [200],
        "/static/js/timeTrialDataPopulator.js": [200],
        "/static/js/telemetryRenderer.js": [200],
        "/static/js/frontendUpdate.js": [200],
        "/static/js/app.js": [200],
    }
