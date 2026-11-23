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

"""TcpTransport, the replay server's receiver, on a real loopback socket."""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import asyncio
import struct

import allure
import pytest

from lib.socket_receiver import tcp_receiver
from lib.socket_receiver.tcp_receiver import TcpTransport

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

pytestmark = [pytest.mark.serial, allure.epic("Telemetry manager"), allure.feature("TCP transport")]

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Connection handling")
@allure.title("A connection that fails to set up is dropped and the next one is served")
async def test_failed_connection_setup_retries_with_the_next_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """A client connects, and wrapping its socket in a stream fails with a reset, as when a client resets straight
    after connecting. A second client then connects and sends one framed packet.

    Expected: the transport keeps running and delivers the second client's packet."""
    real_open_connection = asyncio.open_connection
    attempts = 0

    async def open_connection_failing_once(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionResetError("reset during setup")
        return await real_open_connection(*args, **kwargs)

    monkeypatch.setattr(tcp_receiver.asyncio, "open_connection", open_connection_failing_once)
    transport = TcpTransport(port=0, bind_ip="127.0.0.1")
    port = transport.m_socket.getsockname()[1]
    received: asyncio.Future = asyncio.get_running_loop().create_future()

    @transport.on_packet
    async def _on_packet(message: bytes) -> None:
        if not received.done():
            received.set_result(message)

    run_task = asyncio.create_task(transport.run())
    try:
        _, first_writer = await real_open_connection("127.0.0.1", port)
        _, second_writer = await real_open_connection("127.0.0.1", port)
        second_writer.write(struct.pack("!I", 5) + b"hello")
        await second_writer.drain()

        await asyncio.wait({received, run_task}, timeout=5, return_when=asyncio.FIRST_COMPLETED)
        assert not run_task.done(), f"run() ended: {run_task.exception()!r}"
        assert received.result() == b"hello"
        first_writer.close()
        second_writer.close()
    finally:
        await transport.close()
        run_task.cancel()
        await asyncio.gather(run_task, return_exceptions=True)
