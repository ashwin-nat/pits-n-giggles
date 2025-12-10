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
import time
import threading
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.ipc import PngShmReader, PngShmWriter

from .tests_shm_base import TestShm

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestShmE2E(TestShm):

    # ------------------------------------------------------------
    # E2E TEST 1: Single Topic Round Trip
    # ------------------------------------------------------------

    async def test_e2e_single_topic_round_trip(self):
        received = {}

        # --- Reader setup ---
        reader = PngShmReader()

        @reader.on("telemetry")
        def handle(data):
            received.update(data)
            reader.stop()  # clean shutdown after first hit

        reader_thread = threading.Thread(target=reader.read, daemon=True)
        reader_thread.start()

        # Give reader time to attach to SHM
        time.sleep(0.05)

        # --- Writer side ---
        writer = PngShmWriter()
        payload = {"speed": 321, "gear": 8}

        writer.add("telemetry", payload)
        await writer.write()

        # Wait for reader to consume
        reader_thread.join(timeout=2)

        self.assertEqual(received, payload)

        writer.close()
        reader.close()

    # ------------------------------------------------------------
    # E2E TEST 2: Multi Topic + UTF-8 + Batching
    # ------------------------------------------------------------

    async def test_e2e_multi_topic_utf8_batch(self):
        received = {}

        reader = PngShmReader()

        @reader.on("telemetry")
        def handle_telemetry(data):
            received["telemetry"] = data

        @reader.on("track")
        def handle_track(data):
            received["track"] = data
            reader.stop()

        reader_thread = threading.Thread(target=reader.read, daemon=True)
        reader_thread.start()

        time.sleep(0.05)

        writer = PngShmWriter()

        telemetry_payload = {
            "speed": 333,
            "comment": "Δ fuel = −0.42 kg ✅",
            "emoji": "🏎️🔥",
        }

        track_payload = {
            "name": "Autódromo Internacional do Algarve",
            "short": "Portimão",
            "pt": "São Paulo",
            "es": "A Coruña",
            "es_phrase": "¿Dónde está el piloto?",
        }

        writer.add("telemetry", telemetry_payload)
        writer.add("track", track_payload)
        await writer.write()

        reader_thread.join(timeout=2)

        self.assertEqual(received["telemetry"], telemetry_payload)
        self.assertEqual(received["track"], track_payload)

        writer.close()
        reader.close()

    async def test_e2e_out_of_order_init_reader_first(self):
        received = {}

        # Start reader FIRST (writer does not exist yet)
        reader = PngShmReader()

        @reader.on("telemetry")
        def handle(data):
            received.update(data)
            reader.stop()

        reader_thread = threading.Thread(target=reader.read, daemon=True)
        reader_thread.start()

        # Give reader time to enter attach-wait loop
        await asyncio.sleep(0.1)

        # Now start writer AFTER reader
        writer = PngShmWriter()

        payload = {"speed": 301, "gear": 7}
        writer.add("telemetry", payload)
        await writer.write()

        reader_thread.join(timeout=3)

        self.assertEqual(received, payload)

        writer.close()
        reader.close()

    async def test_e2e_writer_crash_and_restart(self):
        received = []

        writer = PngShmWriter()
        reader = PngShmReader()

        @reader.on("telemetry")
        def handle(data):
            received.append(data)

        reader_thread = threading.Thread(target=reader.read, daemon=True)
        reader_thread.start()

        # Allow reader to attach
        await asyncio.sleep(0.1)

        payload1 = {"speed": 310}
        writer.add("telemetry", payload1)
        await writer.write()
        await asyncio.sleep(0.1)

        # Simulate writer crash
        writer.close()
        del writer

        # Give reader time to detect loss
        await asyncio.sleep(0.2)
        writer = PngShmWriter()

        payload2 = {"speed": 325}
        deadline = asyncio.get_running_loop().time() + 1.0
        received_payload2 = False

        while asyncio.get_running_loop().time() < deadline:
            writer.add("telemetry", payload2)
            await writer.write()

            await asyncio.sleep(0.03)  # ~30 FPS pacing

            if payload2 in received:
                received_payload2 = True
                break

        reader.stop()
        reader_thread.join(timeout=3)

        writer.close()
        reader.close()

        self.assertEqual(received[0], payload1)
        self.assertTrue(
            received_payload2,
            "Reader never recovered after writer restart",
        )
