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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import json
import logging
import mimetypes
import platform
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlsplit

import apps.save_viewer.save_viewer_state as SaveViewerState
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.error_status import PngHttpPortInUseError, is_port_in_use_error
from lib.event_counter import EventCounter

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "apps" / "frontend"
_TEMPLATE_PATH = _FRONTEND_DIR / "html" / "driver-view.html"
_ASSETS_DIR = _REPO_ROOT / "assets"
_STATIC_ROUTE_MAP = {
    "/favicon.ico": (_ASSETS_DIR / "favicon.ico", "image/vnd.microsoft.icon"),
    "/tyre-icons/soft.svg": (_ASSETS_DIR / "tyre-icons" / "soft_tyre.svg", "image/svg+xml"),
    "/tyre-icons/super-soft.svg": (_ASSETS_DIR / "tyre-icons" / "super_soft_tyre.svg", "image/svg+xml"),
    "/tyre-icons/medium.svg": (_ASSETS_DIR / "tyre-icons" / "medium_tyre.svg", "image/svg+xml"),
    "/tyre-icons/hard.svg": (_ASSETS_DIR / "tyre-icons" / "hard_tyre.svg", "image/svg+xml"),
    "/tyre-icons/intermediate.svg": (_ASSETS_DIR / "tyre-icons" / "intermediate_tyre.svg", "image/svg+xml"),
    "/tyre-icons/wet.svg": (_ASSETS_DIR / "tyre-icons" / "wet_tyre.svg", "image/svg+xml"),
}

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _ReusableThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = platform.system() != "Windows"


class _SaveViewerRequestHandler(BaseHTTPRequestHandler):
    server_version = "PitsNGigglesSaveViewer/1.0"

    @property
    def png_server(self) -> "SaveViewerWebServer":
        return self.server.png_server

    def log_message(self, format: str, *args) -> None:
        self.png_server.m_logger.debug("Save viewer HTTP: " + format, *args)

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        path = parsed.path
        self.png_server.m_stats.track_event("__HTTP__", path)

        if path == "/":
            self._send_html(self.png_server.render_driver_view())
            return
        if path == "/telemetry-info":
            self._send_json(SaveViewerState.getTelemetryInfo())
            return
        if path == "/race-info":
            self._send_json(SaveViewerState.getRaceInfo())
            return
        if path == "/driver-info":
            self._handle_driver_info(parsed.query)
            return
        if path.startswith("/static/"):
            self._serve_static_file(path[len("/static/"):])
            return
        if path in _STATIC_ROUTE_MAP:
            file_path, mime_type = _STATIC_ROUTE_MAP[path]
            self._serve_file(file_path, mime_type)
            return

        self._send_json(
            {
                "error": "Not Found",
                "message": f"Unsupported path: {path}",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    def _handle_driver_info(self, raw_query: str) -> None:
        query = parse_qs(raw_query)
        index_values = query.get("index")

        if not index_values or not index_values[0]:
            self._send_json(
                {
                    "error": "Invalid parameters",
                    "message": 'Provide "index" parameter',
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        index = index_values[0]
        if not index.isdigit():
            self._send_json(
                {
                    "error": "Invalid parameter value",
                    "message": '"index" parameter must be numeric',
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        driver_info = SaveViewerState.getDriverInfo(int(index))
        if driver_info:
            self._send_json(driver_info, status=HTTPStatus.OK)
            return

        self._send_json(
            {
                "error": "Invalid parameter value",
                "message": "Invalid index",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    def _serve_static_file(self, relative_path: str) -> None:
        sanitized_path = Path(relative_path)
        if sanitized_path.is_absolute() or ".." in sanitized_path.parts:
            self._send_json(
                {
                    "error": "Invalid path",
                    "message": "Static path traversal is not allowed",
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        full_path = _FRONTEND_DIR / sanitized_path
        mime_type, _ = mimetypes.guess_type(str(full_path))
        self._serve_file(full_path, mime_type or "application/octet-stream")

    def _serve_file(self, file_path: Path, mime_type: str) -> None:
        if not file_path.is_file():
            self._send_json(
                {
                    "error": "Not Found",
                    "message": f"File not found: {file_path.name}",
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        payload = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, body: Dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class SaveViewerWebServer:
    """
    A small threaded HTTP server for the save viewer.

    Socket.IO is intentionally not supported here. The frontend already has a
    polling fallback, which keeps the save viewer functional without the old
    Quart/Socket.IO dependency stack.
    """

    def __init__(
        self,
        port: int,
        ver_str: str,
        logger: logging.Logger,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        debug_mode: bool = False,
    ):
        self.m_port = port
        self.m_ver_str = ver_str
        self.m_logger = logger
        self.m_cert_path = cert_path
        self.m_key_path = key_path
        self.m_debug_mode = debug_mode
        self.m_stats = EventCounter()
        self._httpd: Optional[_ReusableThreadingHTTPServer] = None
        self._driver_view_template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    def render_driver_view(self) -> str:
        template = _apply_conditional_block(
            self._driver_view_template,
            "{% if live_data_mode %}",
            "{% endif %}",
            False,
        )
        template = _apply_conditional_block(
            template,
            "{% if not live_data_mode %}",
            "{% endif %}",
            True,
        )
        return (
            template.replace(
                "{{ 'Live' if live_data_mode else 'Save Data' }}",
                "Save Data",
            )
            .replace("{{ version }}", self.m_ver_str)
            .replace("{{ url_for('static', filename='", "/static/")
            .replace("') }}", f"?v={self.m_ver_str}")
        )

    async def run(self) -> None:
        try:
            httpd = _ReusableThreadingHTTPServer(("0.0.0.0", self.m_port), _SaveViewerRequestHandler)
        except OSError as exc:
            if is_port_in_use_error(exc.errno):
                self.m_logger.error("Port %s is already in use", self.m_port)
                raise PngHttpPortInUseError() from exc
            raise

        httpd.png_server = self
        self._httpd = httpd
        notify_parent_init_complete()
        await asyncio.to_thread(httpd.serve_forever, 0.25)

    async def stop(self) -> None:
        if self._httpd is None:
            return

        httpd = self._httpd
        self._httpd = None
        await asyncio.to_thread(httpd.shutdown)
        await asyncio.to_thread(httpd.server_close)
        self.m_logger.debug("Save viewer web server stopped")

    def get_stats(self) -> dict:
        return self.m_stats.get_stats()


# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _apply_conditional_block(template: str, block_start: str, block_end: str, include_inner: bool) -> str:
    output = template
    while True:
        start = output.find(block_start)
        if start == -1:
            break
        search_from = start + len(block_start)
        end_relative = output[search_from:].find(block_end)
        if end_relative == -1:
            break
        end = search_from + end_relative
        replacement = output[search_from:end] if include_inner else ""
        output = output[:start] + replacement + output[end + len(block_end):]
    return output


def init_server_task(port: int, ver_str: str, logger: logging.Logger, tasks: List[asyncio.Task]) -> SaveViewerWebServer:
    """Initialize the web server and return the server object for proper cleanup."""
    server = SaveViewerWebServer(port, ver_str, logger)
    tasks.append(asyncio.create_task(server.run(), name="Web Server Task"))
    return server
