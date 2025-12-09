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

"""
Shared Memory IPC Sender (Async, Binary Payload, CRC Protected)

- Writes raw bytes only (no JSON, no event/type).
- Upper layers handle serialization/presentation.
- Double-buffered, latest-frame-wins.
- CRC32 used for integrity verification.
"""

import struct
import logging
import zlib
from multiprocessing import shared_memory
from typing import Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SharedMemorySender:
    DEFAULT_SHM_NAME = "png_ipc_atomic"
    DEFAULT_MAX_MSG_SIZE = 128 * 1024  # bytes per buffer

    # Header: seq (uint64), active_index (uint8)
    HEADER_FMT = "QB"

    # Buffer header: size (uint32), crc32 (uint32)
    BUF_HEADER_FMT = "II"

    def __init__(
        self,
        shm_name: str = DEFAULT_SHM_NAME,
        max_msg_size: int = DEFAULT_MAX_MSG_SIZE,
        logger: Optional[logging.Logger] = None,
    ):
        if logger is None:
            logger = logging.getLogger(f"{__name__}.SharedMemorySender")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self.shm_name = shm_name
        self.max_msg_size = max_msg_size

        self.seq: int = 0
        self.active_index: int = 0

        self.HEADER_SIZE = struct.calcsize(self.HEADER_FMT)
        self.BUF_HEADER_SIZE = struct.calcsize(self.BUF_HEADER_FMT)
        self.BUF_TOTAL_SIZE = self.BUF_HEADER_SIZE + self.max_msg_size
        self.TOTAL_SIZE = self.HEADER_SIZE + (2 * self.BUF_TOTAL_SIZE)

        try:
            self.shm = shared_memory.SharedMemory(
                name=self.shm_name, create=True, size=self.TOTAL_SIZE
            )
            self.logger.info("Created shared memory IPC region")
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=self.shm_name)
            self.logger.info("Attached to existing shared memory IPC region")

        # Hard reset header on startup
        struct.pack_into(self.HEADER_FMT, self.shm.buf, 0, 0, 0)

    async def write(self, payload: bytes) -> None:
        """
        Atomically publish a binary payload into shared memory.

        :param payload: Raw bytes.
        """
        self.seq += 1
        self.active_index = self.seq & 1  # toggle 0/1

        size = len(payload)
        if size > self.max_msg_size:
            raise ValueError(f"IPC payload too large ({size} > {self.max_msg_size})")

        crc = zlib.crc32(payload) & 0xFFFFFFFF

        buf_offset = self.HEADER_SIZE + (self.active_index * self.BUF_TOTAL_SIZE)

        # Write buffer: [size][crc][payload]
        struct.pack_into(self.BUF_HEADER_FMT, self.shm.buf, buf_offset, size, crc)
        self.shm.buf[
            buf_offset + self.BUF_HEADER_SIZE:
            buf_offset + self.BUF_HEADER_SIZE + size
        ] = payload

        # Commit: publish seq + active index
        struct.pack_into(
            self.HEADER_FMT,
            self.shm.buf,
            0,
            self.seq,
            self.active_index,
        )

    def close(self) -> None:
        try:
            self.shm.close()
        except Exception:
            pass
