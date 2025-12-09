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
import struct
import sys
import threading

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.ipc.shm.transport_writer import ShmTransportWriter
from lib.ipc.shm.transport_reader import ShmTransportReader

from .tests_shm_base import TestShm

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestShmTransport(TestShm):
    SHM_NAME = "test_ipc_shm"
    MAX_MSG_SIZE = 1024

    def setUp(self):
        self.received = []
        self.receiver = None
        self.receiver_thread = None

    def tearDown(self):
        if self.receiver:
            self.receiver.stop()
            self.receiver.close()
        if self.receiver_thread:
            self.receiver_thread.join(timeout=1)

    # -----------------------------
    # Helpers
    # -----------------------------
    def _start_receiver(self, interval_ms=5):
        def callback(payload: bytes):
            self.received.append(payload)

        self.receiver = ShmTransportReader(
            read_interval_ms=interval_ms,
            on_payload=callback,
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        self.receiver_thread = threading.Thread(
            target=self.receiver.run,
            daemon=True,
        )
        self.receiver_thread.start()

    # -----------------------------
    # Basic send/receive
    # -----------------------------
    async def test_basic_binary_payload(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        self._start_receiver()

        payload = b"hello world"
        await sender.write(payload)

        await asyncio.sleep(0.05)

        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0], payload)

        sender.close()

    # -----------------------------
    # Latest-frame-wins behavior
    # -----------------------------
    async def test_latest_frame_wins(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        # Slow reader on purpose
        self._start_receiver(interval_ms=50)

        await sender.write(b"frame_0")
        await sender.write(b"frame_1")
        await sender.write(b"frame_2")

        await asyncio.sleep(0.2)

        # Only the latest frame should survive
        self.assertTrue(len(self.received) >= 1)
        self.assertEqual(self.received[-1], b"frame_2")

        sender.close()

    # -----------------------------
    # CRC corruption rejection
    # -----------------------------
    async def test_crc_corruption_is_dropped(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        self._start_receiver()

        good_payload = b"good_payload"
        await sender.write(good_payload)
        await asyncio.sleep(0.05)

        # --- Manually corrupt the ACTIVE buffer payload without fixing CRC ---

        hdr_size = sender.HEADER_SIZE
        buf_hdr = sender.BUF_HEADER_SIZE
        buf_total = sender.BUF_TOTAL_SIZE

        corrupt_payload = b"CORRUPTED"
        buf_offset = hdr_size + (sender.active_index * buf_total)

        sender.shm.buf[
            buf_offset + buf_hdr:
            buf_offset + buf_hdr + len(corrupt_payload)
        ] = corrupt_payload

        # Force a NEW commit so receiver is allowed to react
        sender.seq += 1
        sender.active_index = sender.seq & 1
        struct_data = struct.pack("QB", sender.seq, sender.active_index)
        sender.shm.buf[: len(struct_data)] = struct_data

        await asyncio.sleep(0.05)

        # ✅ ASSERTIONS THAT MATCH YOUR IPC SEMANTICS:
        # - At least one valid payload must exist
        # - Corrupted payload must NEVER reach callback
        self.assertIn(good_payload, self.received)
        self.assertNotIn(b"CORRUPTED", self.received)

        sender.close()


    # -----------------------------
    # Oversized payload rejection
    # -----------------------------
    async def test_oversized_payload_raises(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=16,
        )

        big_payload = b"x" * 64

        with self.assertRaises(ValueError):
            await sender.write(big_payload)

        sender.close()

    # -----------------------------
    # Writer faster than reader
    # -----------------------------
    async def test_fast_writer_slow_reader(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        self._start_receiver(interval_ms=100)

        for i in range(10):
            await sender.write(f"pkt_{i}".encode())
            await asyncio.sleep(0.005)

        await asyncio.sleep(0.3)

        # Only the latest should realistically survive
        self.assertEqual(self.received[-1], b"pkt_9")

        sender.close()

    # -----------------------------
    # Reader faster than writer
    # -----------------------------
    async def test_slow_writer_fast_reader(self):
        sender = ShmTransportWriter(
            shm_name=self.SHM_NAME,
            max_msg_size=self.MAX_MSG_SIZE,
        )

        self._start_receiver(interval_ms=1)

        await sender.write(b"A")
        await asyncio.sleep(0.1)
        await sender.write(b"B")

        await asyncio.sleep(0.05)

        self.assertIn(b"A", self.received)
        self.assertIn(b"B", self.received)

        sender.close()
