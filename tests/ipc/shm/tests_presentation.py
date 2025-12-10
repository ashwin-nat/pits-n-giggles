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

import asyncio
import os
import json
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.ipc.shm.presentation import PngShmWriter, PngShmReader

from .tests_shm_base import TestShm

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class FakeWriterTransport:
    def __init__(self):
        self.payloads = []
        self.closed = False

    async def write(self, payload: bytes):
        self.payloads.append(payload)

    def close(self):
        self.closed = True


class FakeReaderTransport:
    def __init__(self):
        self.on_run_called = False
        self.on_stop_called = False
        self.on_close_called = False

    def run(self):
        self.on_run_called = True

    def stop(self):
        self.on_stop_called = True

    def close(self):
        self.on_close_called = True


# ------------------------------------------------------------
# Test Case
# ------------------------------------------------------------

class TestShmPresentation(TestShm):
    # -------------------------------
    # WRITER TESTS
    # -------------------------------

    async def test_writer_single_topic(self):
        transport = FakeWriterTransport()
        shm = PngShmWriter(transport=transport)

        shm.add("telemetry", {"speed": 300})
        await shm.write()

        self.assertEqual(len(transport.payloads), 1)

        frame = json.loads(transport.payloads[0].decode())
        self.assertEqual(frame["telemetry"]["speed"], 300)

    async def test_writer_multiple_topics(self):
        transport = FakeWriterTransport()
        shm = PngShmWriter(transport=transport)

        shm.add("a", {"x": 1})
        shm.add("b", {"y": 2})
        await shm.write()

        frame = json.loads(transport.payloads[0].decode())
        self.assertEqual(frame["a"]["x"], 1)
        self.assertEqual(frame["b"]["y"], 2)

    async def test_writer_clears_frame_after_write(self):
        transport = FakeWriterTransport()
        shm = PngShmWriter(transport=transport)

        shm.add("a", {"x": 1})
        await shm.write()
        await shm.write()  # second call should do nothing

        self.assertEqual(len(transport.payloads), 1)

    async def test_writer_close(self):
        transport = FakeWriterTransport()
        shm = PngShmWriter(transport=transport)

        shm.close()
        self.assertTrue(transport.closed)

    # -------------------------------
    # READER TESTS
    # -------------------------------

    def test_reader_single_topic_dispatch(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        received = {}

        @shm.on("telemetry")
        def handler(data):
            received["telemetry"] = data

        payload = json.dumps({"telemetry": {"speed": 320}}).encode()
        shm.on_payload(payload)

        self.assertIn("telemetry", received)
        self.assertEqual(received["telemetry"]["speed"], 320)

    def test_reader_multiple_topics_dispatch(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        received = {}

        @shm.on("a")
        def ha(data):
            received["a"] = data

        @shm.on("b")
        def hb(data):
            received["b"] = data

        payload = json.dumps({
            "a": {"x": 1},
            "b": {"y": 2},
        }).encode()

        shm.on_payload(payload)

        self.assertEqual(received["a"]["x"], 1)
        self.assertEqual(received["b"]["y"], 2)

    def test_reader_ignores_unregistered_topics(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        called = False

        @shm.on("known")
        def handler(data):
            nonlocal called
            called = True

        payload = json.dumps({"unknown": {"x": 1}}).encode()
        shm.on_payload(payload)

        self.assertFalse(called)

    def test_reader_invalid_json_is_dropped(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        called = False

        @shm.on("a")
        def handler(data):
            nonlocal called
            called = True

        shm.on_payload(b"not-json-at-all")

        self.assertFalse(called)

    def test_reader_handler_exception_does_not_break_dispatch(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        called = False

        @shm.on("bad")
        def bad_handler(data):
            raise RuntimeError("boom")

        @shm.on("good")
        def good_handler(data):
            nonlocal called
            called = True

        payload = json.dumps({
            "bad": {"x": 1},
            "good": {"y": 2},
        }).encode()

        shm.on_payload(payload)

        self.assertTrue(called)

    def test_reader_run_stop_close_forwarded(self):
        transport = FakeReaderTransport()
        shm = PngShmReader(transport=transport)

        shm.read()
        shm.stop()
        shm.close()

        self.assertTrue(transport.on_run_called)
        self.assertTrue(transport.on_stop_called)
        self.assertTrue(transport.on_close_called)

    async def test_utf8_payload_round_trip_with_iberian_chars(self):
        transport = FakeWriterTransport()
        writer = PngShmWriter(transport=transport)

        utf8_payload = {
            "track": "Portimão",
            "city_pt": "São Paulo",
            "city_es": "A Coruña",
            "question_es": "¿Dónde está el piloto?",
            "exclaim_es": "¡Vámonos!",
            "driver": "Ayrton 🇧🇷",
            "team": "Sauber–Ferrari",
            "comment": "Δ fuel = −0.42 kg ✅",
            "japanese": "こんにちは",
            "emoji": "🏎️🔥",
            "tilde_test": "niño, piñata, cañón",
            "cedilla_test": "ação, coração, milhão",
        }

        writer.add("telemetry", utf8_payload)
        await writer.write()

        # Ensure something was written
        self.assertEqual(len(transport.payloads), 1)

        # Feed into the reader
        reader_transport = FakeReaderTransport()
        reader = PngShmReader(transport=reader_transport)

        received = {}

        @reader.on("telemetry")
        def handler(data):
            received.update(data)

        reader.on_payload(transport.payloads[0])

        # Full UTF-8 integrity check
        self.assertEqual(received, utf8_payload)
