# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import asyncio
import json
import logging
import socket
import unittest
import urllib.error
import urllib.request

from apps.save_viewer.save_viewer_state import init_state
from apps.save_viewer.save_web_server import SaveViewerWebServer


def _get_free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestSaveViewerWebServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.logger = logging.getLogger("test-save-viewer-web-server")
        init_state(self.logger)
        self.port = _get_free_tcp_port()
        self.server = SaveViewerWebServer(self.port, "test-version", self.logger)
        self.server_task = asyncio.create_task(self.server.run())
        await self._wait_for_server()

    async def asyncTearDown(self) -> None:
        await self.server.stop()
        await self.server_task

    async def _wait_for_server(self) -> None:
        base_url = f"http://127.0.0.1:{self.port}/telemetry-info"
        for _ in range(50):
            try:
                with urllib.request.urlopen(base_url, timeout=0.5) as response:
                    if response.status == 200:
                        return
            except Exception:
                await asyncio.sleep(0.05)
        self.fail("Save viewer server did not start in time")

    def test_root_and_static_routes(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=2) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Save Data", body)
            self.assertNotIn("{% if live_data_mode %}", body)

        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/static/js/socketio.js?v=test-version",
            timeout=2,
        ) as response:
            self.assertEqual(response.status, 200)

        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/tyre-icons/soft.svg", timeout=2) as response:
            self.assertEqual(response.status, 200)

    def test_json_routes_and_validation(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/telemetry-info", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertIn("table-entries", payload)

        with self.assertRaises(urllib.error.HTTPError) as missing_index:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/driver-info", timeout=2)
        self.assertEqual(missing_index.exception.code, 400)
        missing_index.exception.close()

        with self.assertRaises(urllib.error.HTTPError) as bad_index:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/driver-info?index=abc", timeout=2)
        self.assertEqual(bad_index.exception.code, 400)
        bad_index.exception.close()
