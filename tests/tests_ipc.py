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

import threading
import asyncio
import time
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.ipc import IpcParent, IpcChildSync, IpcChildAsync, get_free_tcp_port

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestIPC(F1TelemetryUnitTestsBase):

    def setUp(self):
        self.port = get_free_tcp_port()
        time.sleep(0.1)  # slight pause to avoid port reuse race

    def test_sync_to_sync(self):
        """Test: Parent (sync) -> Child (sync) communication"""
        def handler(msg):
            if msg['cmd'] == 'ping':
                return {'reply': 'pong'}
            return {'error': 'unknown'}

        child = IpcChildSync(self.port)
        child_thread = threading.Thread(target=child.serve, args=(handler,), daemon=True)
        child_thread.start()

        time.sleep(0.1)
        parent = IpcParent(self.port, timeout_ms=500)
        resp = parent.request('ping')
        self.assertEqual(resp.get('reply'), 'pong')

        # stop child
        parent.request('quit')
        parent.close()
        child_thread.join(timeout=2)

    def test_sync_to_async(self):
        """Test: Parent (sync) -> Child (async) communication"""

        async def handler(msg):
            if msg['cmd'] == 'ping':
                return {'reply': 'pong-async'}
            return {'error': 'unknown'}

        child = IpcChildAsync(self.port)

        def run_async_child():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(child.serve(handler))

        thread = threading.Thread(target=run_async_child, daemon=True)
        thread.start()

        time.sleep(0.1)
        parent = IpcParent(self.port, timeout_ms=500)
        resp = parent.request('ping')
        self.assertEqual(resp.get('reply'), 'pong-async')

        # stop child
        parent.request('quit')
        parent.close()
        thread.join(timeout=2)

    def test_unknown_command(self):
        """Test: Child returns error for unknown command"""
        def handler(msg):
            return {'error': 'unknown'}

        child = IpcChildSync(self.port)
        thread = threading.Thread(target=child.serve, args=(handler,), daemon=True)
        thread.start()

        time.sleep(0.1)
        parent = IpcParent(self.port, timeout_ms=500)
        resp = parent.request('invalid_command')
        self.assertEqual(resp.get('error'), 'unknown')
        parent.request('quit')
        parent.close()
        thread.join(timeout=2)

    def test_child_crash(self):
        """Test: Simulate child crashing during response"""
        async def handler(msg):
            raise RuntimeError("Simulated crash")

        child = IpcChildAsync(self.port)

        def run_async_child():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(child.serve(handler))

        thread = threading.Thread(target=run_async_child, daemon=True)
        thread.start()

        time.sleep(0.1)
        parent = IpcParent(self.port, timeout_ms=500)
        resp = parent.request('ping')
        self.assertIn('error', resp)
        parent.close()
        thread.join(timeout=2)

    def test_child_freeze(self):
        """Test: Simulate child freezing (non-responding)"""
        def handler(msg):
            time.sleep(10)  # long block to simulate freeze
            return {'reply': 'late'}

        child = IpcChildSync(self.port)
        thread = threading.Thread(target=child.serve, args=(handler,), daemon=True)
        thread.start()

        time.sleep(0.1)
        parent = IpcParent(self.port, timeout_ms=500)
        resp = parent.request('ping')
        self.assertIn('error', resp)  # Expect timeout error
        parent.close()
        thread.join(timeout=2)

    def test_child_not_started(self):
        """Test: Parent attempts to connect but child was never started"""
        parent = IpcParent(get_free_tcp_port(), timeout_ms=500)
        resp = parent.request('ping')
        self.assertIn('error', resp)

        error_msg = str(resp['error']).lower()
        self.assertTrue(
            any(msg in error_msg for msg in [
                'timed out', 'resource temporarily unavailable', 'connection refused'
            ]),
            msg=f"Unexpected error message: {error_msg}"
        )
        parent.close()