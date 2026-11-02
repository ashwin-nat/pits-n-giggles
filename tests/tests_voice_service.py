"""Voice service lifecycle and privacy checks, without microphone access."""

import importlib
import json
import threading
from unittest.mock import Mock

import pytest

from apps.voice.engineer import DEFAULT_CONFIG


def service():
    return importlib.import_module("apps.voice.service")


@pytest.mark.parametrize(
    "change",
    [
        {"backend": "cloud"},
        {"backend": "typo"},
        {"ollama_url": "https://example.com"},
        {"mcp_url": "http://192.168.0.2:4770/mcp"},
        {"ollama_url": "file:///tmp/model"},
        {"ollama_url": "http://user:password@localhost:11434"},
    ],
)
def test_service_rejects_nonlocal_configuration(change):
    with pytest.raises(ValueError, match="(?i)(local|loopback)"):
        service().validate_local_config(dict(DEFAULT_CONFIG, **change))


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_service_accepts_loopback_configuration(host):
    service().validate_local_config(
        dict(DEFAULT_CONFIG, ollama_url=f"http://{host}:11434")
    )


def test_service_stops_controller_on_shutdown(monkeypatch):
    module = service()
    stop = threading.Event()
    controller = Mock()
    controller.start.side_effect = stop.set
    monkeypatch.setattr(module, "load_config", lambda: dict(DEFAULT_CONFIG))
    monkeypatch.setattr(module, "VoiceController", lambda: controller)
    module.run(stop)
    controller.start.assert_called_once()
    controller.stop.assert_called_once()


def test_service_fails_if_listener_stops(monkeypatch):
    module = service()
    controller = Mock(is_alive=False)
    monkeypatch.setattr(module, "load_config", lambda: dict(DEFAULT_CONFIG))
    monkeypatch.setattr(module, "VoiceController", lambda: controller)
    with pytest.raises(RuntimeError, match="(?i)(listener|worker)"):
        module.run(threading.Event())
    controller.stop.assert_called_once()


def test_service_rejects_unavailable_engineer(monkeypatch):
    module = service()
    controller = Mock(engineer=None)
    monkeypatch.setattr(module, "load_config", lambda: dict(DEFAULT_CONFIG))
    monkeypatch.setattr(module, "VoiceController", lambda: controller)
    with pytest.raises(RuntimeError, match="(?i)engineer"):
        module.run(threading.Event())
    controller.start.assert_not_called()
    controller.stop.assert_called_once()


def test_service_cleans_up_failed_start(monkeypatch):
    module = service()
    controller = Mock()
    controller.start.side_effect = RuntimeError("microphone unavailable")
    monkeypatch.setattr(module, "load_config", lambda: dict(DEFAULT_CONFIG))
    monkeypatch.setattr(module, "VoiceController", lambda: controller)
    with pytest.raises(RuntimeError, match="microphone unavailable"):
        module.run(threading.Event())
    controller.stop.assert_called_once()


def test_check_does_not_start_microphone(monkeypatch, capsys):
    module = service()
    factory = Mock()
    monkeypatch.setattr(module, "VoiceController", factory)
    monkeypatch.setattr(module, "check_dependencies", lambda: {"ok": True})
    assert module.main(["--check"]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}
    factory.assert_not_called()


def test_failed_check_returns_nonzero(monkeypatch):
    module = service()
    monkeypatch.setattr(
        module, "check_dependencies", Mock(side_effect=RuntimeError("MCP unavailable"))
    )
    assert module.main(["--check"]) == 1
