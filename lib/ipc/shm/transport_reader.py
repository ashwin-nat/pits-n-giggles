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

import struct
import time
import logging
import zlib
from multiprocessing import shared_memory
from typing import Optional, Callable

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ShmTransportReader:
    """
    Shared Memory IPC Receiver (Sync, Binary Payload, CRC Protected)

    - Reads only the latest committed binary payload.
    - Drops frame if:
    - seq == last_seq
    - CRC check fails
    - Polling interval is specified in INTEGER MILLISECONDS.
    - Provides a clean stop() method.
    """
    DEFAULT_SHM_NAME = "png_ipc_atomic"
    DEFAULT_MAX_MSG_SIZE = 128 * 1024  # must match sender

    HEADER_FMT = "QB"
    BUF_HEADER_FMT = "II"  # size, crc

    def __init__(
        self,
        read_interval_ms: int,
        on_payload: Callable[[bytes], None],
        shm_name: str = DEFAULT_SHM_NAME,
        max_msg_size: int = DEFAULT_MAX_MSG_SIZE,
        logger: Optional[logging.Logger] = None,
    ):
        if logger is None:
            logger = logging.getLogger(f"{__name__}.SharedMemoryReceiver")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self.read_interval_sec = read_interval_ms / 1000.0
        self.shm_name = shm_name
        self.max_msg_size = max_msg_size
        self.callback = on_payload

        self.last_seq: int = 0
        self._running: bool = True

        self.HEADER_SIZE = struct.calcsize(self.HEADER_FMT)
        self.BUF_HEADER_SIZE = struct.calcsize(self.BUF_HEADER_FMT)
        self.BUF_TOTAL_SIZE = self.BUF_HEADER_SIZE + self.max_msg_size

        self.shm = None
        self.logger.debug("Shared memory receiver attached")

    def run(self) -> None:
        """
        Blocking polling loop with automatic re-attach if writer restarts.
        """
        self.logger.info("Shared memory receiver run loop started")

        while self._running:

            # ----------------------------------
            # 1) ATTACH PHASE (wait forever)
            # ----------------------------------
            if self.shm is None:
                self.logger.info("Waiting for shared memory IPC region...")
                while self._running:
                    try:
                        self.shm = shared_memory.SharedMemory(name=self.shm_name)
                        self.logger.info("Shared memory receiver attached")
                        break
                    except FileNotFoundError:
                        time.sleep(0.01)

            # ----------------------------------
            # 2) READ PHASE (normal operation)
            # ----------------------------------
            try:
                payload = self._read_latest()
                if payload is not None:
                    self.callback(payload)

            # ----------------------------------
            # 3) CRASH / RESTART DETECTION
            # ----------------------------------
            except (BufferError, ValueError, OSError):
                # Writer crashed and likely unlinked SHM
                self.logger.warning(
                    "Shared memory lost — waiting for writer to restart"
                )

                try:
                    self.shm.close()
                except Exception:
                    pass

                # Force a clean re-attach on next loop
                self.shm = None

            time.sleep(self.read_interval_sec)

        self.logger.info("Shared memory receiver stopped")


    def stop(self) -> None:
        """
        Request a clean shutdown of the run loop.
        """
        self._running = False

    def _read_latest(self) -> Optional[bytes]:
        seq, active_index = struct.unpack_from(self.HEADER_FMT, self.shm.buf, 0)

        if seq == self.last_seq:
            return None

        buf_offset = self.HEADER_SIZE + (active_index * self.BUF_TOTAL_SIZE)

        size, expected_crc = struct.unpack_from(
            self.BUF_HEADER_FMT, self.shm.buf, buf_offset
        )

        raw = bytes(
            self.shm.buf[
                buf_offset + self.BUF_HEADER_SIZE:
                buf_offset + self.BUF_HEADER_SIZE + size
            ]
        )

        actual_crc = zlib.crc32(raw) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            self.logger.warning("CRC mismatch — dropped corrupted IPC frame")
            self.last_seq = seq
            return None

        self.last_seq = seq
        return raw

    def close(self) -> None:
        try:
            self.shm.close()
        except Exception:
            pass
