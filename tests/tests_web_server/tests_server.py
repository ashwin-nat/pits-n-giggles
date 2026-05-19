# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# pylint: skip-file

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from lib.logger import PngLogger
from lib.web_server.client_types import ClientType
from lib.web_server.server import BaseWebServer

# ----------------------------------------------------------------------------------------------------------------------

logging.setLoggerClass(PngLogger)


def _make_server(**kwargs) -> BaseWebServer:
    logger = logging.getLogger("test_web_server")
    defaults = dict(
        port=8080,
        ver_str="0.0.0-test",
        logger=logger,
        bind_address="127.0.0.1",
    )
    defaults.update(kwargs)
    return BaseWebServer(**defaults)


class TestBaseWebServer:

    def test_constructor_stores_port(self):
        server = _make_server(port=1234)
        assert server.m_port == 1234

    def test_constructor_stores_bind_address(self):
        server = _make_server(bind_address="0.0.0.0")
        assert server.m_bind_address == "0.0.0.0"

    def test_constructor_stores_ver_str(self):
        server = _make_server(ver_str="1.2.3")
        assert server.m_ver_str == "1.2.3"

    def test_constructor_stores_cert_and_key_paths(self):
        server = _make_server(cert_path="/cert.pem", key_path="/key.pem")
        assert server.m_cert_path == "/cert.pem"
        assert server.m_key_path == "/key.pem"

    def test_constructor_defaults_cert_key_to_none(self):
        server = _make_server()
        assert server.m_cert_path is None
        assert server.m_key_path is None

    def test_constructor_socketio_enabled_by_default(self):
        server = _make_server()
        assert server.m_sio is not None

    def test_constructor_socketio_disabled(self):
        server = _make_server(enable_socketio=False)
        assert server.m_sio is None

    def test_constructor_empty_client_event_mappings_when_none(self):
        server = _make_server()
        assert server.m_client_event_mappings == {}

    def test_constructor_stores_client_event_mappings(self):
        mappings = {ClientType.RACE_TABLE: ["event-a", "event-b"]}
        server = _make_server(client_event_mappings=mappings)
        assert server.m_client_event_mappings == mappings

    def test_get_stats_returns_dict(self):
        server = _make_server()
        stats = server.get_stats()
        assert isinstance(stats, dict)

    def test_get_stats_initially_empty(self):
        server = _make_server()
        assert server.get_stats() == {}

    def test_register_post_start_callback(self):
        server = _make_server()
        cb = AsyncMock()
        server.register_post_start_callback(cb)
        assert server._post_start_callback is cb

    def test_register_on_client_register_callback(self):
        server = _make_server()
        cb = AsyncMock()
        server.register_on_client_register_callback(cb)
        assert server._on_client_register_callback is cb

    def test_register_on_client_disconnect_callback(self):
        server = _make_server()
        cb = AsyncMock()
        server.register_on_client_disconnect_callback(cb)
        assert server._on_client_disconnect_callback is cb

    def test_is_client_of_type_connected_false_when_no_clients(self):
        server = _make_server()
        assert server.is_client_of_type_connected(ClientType.RACE_TABLE) is False
        assert server.is_client_of_type_connected(ClientType.PLAYER_STREAM_OVERLAY) is False

    def test_is_any_client_interested_in_event_false_for_unknown_event(self):
        server = _make_server()
        assert server.is_any_client_interested_in_event("some-event") is False

    # ---- validate_int_get_request_param --------------------------------------------------------

    def test_validate_int_get_request_param_returns_none_for_valid_int(self):
        server = _make_server()
        assert server.validate_int_get_request_param(42, "index") is None

    def test_validate_int_get_request_param_returns_none_for_numeric_string(self):
        server = _make_server()
        assert server.validate_int_get_request_param("7", "index") is None

    def test_validate_int_get_request_param_returns_error_for_none(self):
        server = _make_server()
        result = server.validate_int_get_request_param(None, "index")
        assert result is not None
        assert "index" in result.get("message", "")

    def test_validate_int_get_request_param_returns_error_for_non_numeric_string(self):
        server = _make_server()
        result = server.validate_int_get_request_param("abc", "index")
        assert result is not None
        assert "index" in result.get("message", "")

    def test_validate_int_get_request_param_returns_error_for_float_string(self):
        server = _make_server()
        result = server.validate_int_get_request_param("3.14", "index")
        assert result is not None

    @pytest.mark.parametrize("value", [0, 1, 100, "0", "999"])
    def test_validate_int_get_request_param_valid_values(self, value):
        server = _make_server()
        assert server.validate_int_get_request_param(value, "param") is None

    @pytest.mark.parametrize("value", [None, "abc", "3.14", "", "12x"])
    def test_validate_int_get_request_param_invalid_values(self, value):
        server = _make_server()
        assert server.validate_int_get_request_param(value, "param") is not None
