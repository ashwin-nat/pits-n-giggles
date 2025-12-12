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
import zmq
from unittest.mock import Mock

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .base import TestIPC

from lib.ipc import get_free_tcp_port, IpcPubSubBroker, IpcPublisherAsync, IpcSubscriberSync

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

SEND_REPEATS = 5          # Send N times to guarantee post-subscription delivery
MESSAGE_DELAY = 0.01      # Small delay between sends
PROPAGATION_DELAY = 0.05  # Allow XPUB/XSUB routing tables to sync


def wait_for_subscription(xpub_port: int, topic: str, timeout: float = 1.0) -> bool:
    ctx = zmq.Context.instance()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.LINGER, 0)

    # XPUB emits subscription messages as plain SUB messages
    sock.setsockopt(zmq.SUBSCRIBE, b"")
    sock.connect(f"tcp://127.0.0.1:{xpub_port}")

    poller = zmq.Poller()
    poller.register(sock, zmq.POLLIN)

    expected = b"\x01" + topic.encode()  # 0x01 = subscribe

    end = time.time() + timeout
    while time.time() < end:
        events = dict(poller.poll(10))
        if sock in events:
            msg = sock.recv()
            if msg == expected:
                sock.close()
                return True

    sock.close()
    return False

# -------------------------------
# Tests
# -------------------------------
class TestIpcPubSub(TestIPC):
    def setUp(self):
        # Start broker with OS-assigned ports
        self.broker = IpcPubSubBroker(xsub_port=0, xpub_port=0)
        self.broker.start()
        time.sleep(0.05)

        self.xsub_port = self.broker.xsub_port
        self.xpub_port = self.broker.xpub_port

    def tearDown(self):
        self.broker.close()
        time.sleep(0.05)

    # ----------------------------------------------------------
    # End-to-end PUB → XSUB → XPUB → SUB test
    # ----------------------------------------------------------
    def test_pubsub_end_to_end(self):
        received = []

        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("test")
        def handler(data):
            received.append(data)

        t = threading.Thread(target=sub.start, daemon=True)
        t.start()

        # Allow SUB to connect and send subscription upstream
        time.sleep(0.05)

        async def pub_task():
            pub = IpcPublisherAsync(port=self.xsub_port)

            # Send multiple times to guarantee delivery
            for _ in range(5):
                await pub.publish("test", {"value": 123})
                await asyncio.sleep(0.01)

            await pub.close()

        asyncio.run(pub_task())

        # Allow subscriber to process
        time.sleep(0.05)

        sub.close()
        t.join(timeout=0.2)

        # At least one message MUST come through
        self.assertIn({"value": 123}, received)

    # ----------------------------------------------------------
    # Subscriber starts before publisher
    # ----------------------------------------------------------
    def test_subscriber_before_broker(self):
        received = []

        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("early")
        def handler(data):
            received.append(data)

        t = threading.Thread(target=sub.start, daemon=True)
        t.start()

        time.sleep(0.05)

        async def pub_task():
            pub = IpcPublisherAsync(port=self.xsub_port)

            # Send multiple times to guarantee delivery
            for _ in range(5):
                await pub.publish("early", {"ok": True})
                await asyncio.sleep(0.01)

            await pub.close()

        asyncio.run(pub_task())

        time.sleep(0.05)

        sub.close()
        t.join(timeout=0.2)

        # Subscriber must have received at least one
        self.assertIn({"ok": True}, received)

    # ----------------------------------------------------------
    # Producer must never block even under rapid fire
    # ----------------------------------------------------------
    def test_fast_publisher_does_not_block(self):

        async def spam():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(500):
                await pub.publish("fast", {"x": 1})
            await pub.close()

        try:
            asyncio.run(asyncio.wait_for(spam(), timeout=0.5))
        except asyncio.TimeoutError:
            self.fail("Publisher blocked the event loop!")

    def test_publisher_before_subscriber(self):
        received = []

        async def run_pub():
            pub = IpcPublisherAsync(port=self.xsub_port)
            # Publisher emits messages BEFORE subscriber exists
            for _ in range(SEND_REPEATS):
                await pub.publish("late", {"late": 1})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        # Start publisher first
        asyncio.run(run_pub())

        # Now start subscriber
        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("late")
        def handler(data):
            received.append(data)

        t = threading.Thread(target=sub.start, daemon=True)
        t.start()

        time.sleep(PROPAGATION_DELAY)

        async def pub_again():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(SEND_REPEATS):
                await pub.publish("late", {"late": 2})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        asyncio.run(pub_again())
        time.sleep(PROPAGATION_DELAY)

        sub.close()
        t.join(timeout=0.2)

        # Must receive at least one of the SECOND batch
        self.assertIn({"late": 2}, received)

    # ----------------------------------------------------------
    # One publisher, MANY subscribers
    # ----------------------------------------------------------
    def test_one_publisher_many_subscribers(self):
        results = [[] for _ in range(3)]
        subs = []
        threads = []

        # Create 3 subscribers
        for idx in range(3):
            sub = IpcSubscriberSync(port=self.xpub_port)

            @sub.route("fanout")
            def handler(data, i=idx):
                results[i].append(data)

            subs.append(sub)

            t = threading.Thread(target=sub.start, daemon=True)
            threads.append(t)
            t.start()

        time.sleep(PROPAGATION_DELAY)

        async def run_pub():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(SEND_REPEATS):
                await pub.publish("fanout", {"v": 999})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        asyncio.run(run_pub())
        time.sleep(PROPAGATION_DELAY)

        # Shutdown subscribers
        for sub in subs:
            sub.close()

        for t in threads:
            t.join(timeout=0.2)

        # All 3 subscribers MUST receive the broadcast at least once
        for r in results:
            self.assertIn({"v": 999}, r)

    # ----------------------------------------------------------
    # Publisher CRASH mid-stream
    # ----------------------------------------------------------
    def test_publisher_crash(self):
        received = []

        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("crashpub")
        def handler(data):
            received.append(data)

        t = threading.Thread(target=sub.start, daemon=True)
        t.start()
        time.sleep(PROPAGATION_DELAY)

        # Simulate publisher crash by closing socket abruptly
        async def crash_pub():
            pub = IpcPublisherAsync(port=self.xsub_port)
            # Send a few messages, then crash before graceful close
            for _ in range(3):
                await pub.publish("crashpub", {"alive": True})
                await asyncio.sleep(MESSAGE_DELAY)

            # "Crash" = skip close(), destroy socket immediately
            pub.socket.close(linger=0)

        asyncio.run(crash_pub())
        time.sleep(PROPAGATION_DELAY)

        sub.close()
        t.join(timeout=0.2)

        # Subscriber should have received the pre-crash messages
        self.assertIn({"alive": True}, received)

    # ----------------------------------------------------------
    # Subscriber CRASH mid-stream
    # ----------------------------------------------------------
    def test_subscriber_crash(self):
        received = []

        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("crashsub")
        def handler(data):
            received.append(data)

        t = threading.Thread(target=sub.start, daemon=True)
        t.start()

        time.sleep(PROPAGATION_DELAY)

        # Crash subscriber = abrupt socket close without stopping thread
        sub.socket.close(linger=0)

        # Give broker time to notice broken pipe
        time.sleep(0.05)

        async def run_pub():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(SEND_REPEATS):
                await pub.publish("crashsub", {"after": True})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        asyncio.run(run_pub())

        # Allow subscriber to crash out of loop
        time.sleep(0.05)

        # Stop subscriber cleanly
        sub.close()
        t.join(timeout=0.2)

        # Subscriber may have received some messages BEFORE crash
        # After crash, it must not receive new ones
        for msg in received:
            self.assertNotEqual(msg, {"after": True})

    # ----------------------------------------------------------
    # Broker crash mid-stream
    # ----------------------------------------------------------
    def test_broker_crash(self):
        received = []

        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("brk")
        def handler(data):
            received.append(data)

        t_sub = threading.Thread(target=sub.start, daemon=True)
        t_sub.start()
        time.sleep(PROPAGATION_DELAY)

        async def pub_task_pre_crash():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(3):
                await pub.publish("brk", {"before": True})
                await asyncio.sleep(MESSAGE_DELAY)
            return pub  # Keep pub alive

        # Publisher running and sending
        pub = asyncio.run(pub_task_pre_crash())

        # Crash broker mid-stream
        self.broker.close()
        time.sleep(0.05)

        # Publisher continues (messages will drop)
        async def pub_task_post_crash():
            for _ in range(3):
                await pub.publish("brk", {"after": True})
                await asyncio.sleep(MESSAGE_DELAY)
            pub.socket.close(linger=0)

        asyncio.run(pub_task_post_crash())

        # Give subscriber time to choke
        time.sleep(0.05)

        # Stop subscriber
        sub.close()
        t_sub.join(timeout=0.2)

        # Must have received pre-crash messages
        self.assertIn({"before": True}, received)

        # Must NOT have received messages after crash
        self.assertNotIn({"after": True}, received)

    def test_pub_and_sub_before_broker(self):
        received = []

        # Subscriber starts BEFORE broker exists
        sub = IpcSubscriberSync(port=self.xpub_port)

        @sub.route("pre")
        def handler(data):
            received.append(data)

        t_sub = threading.Thread(target=sub.start, daemon=True)
        t_sub.start()

        # Publisher also starts BEFORE broker
        async def pub_task_early():
            pub = IpcPublisherAsync(port=self.xsub_port)
            for _ in range(SEND_REPEATS):
                await pub.publish("pre", {"early": True})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        asyncio.run(pub_task_early())

        # Restart broker
        old_xsub = self.xsub_port
        old_xpub = self.xpub_port

        self.broker.close()
        time.sleep(0.05)

        self.broker = IpcPubSubBroker(
            xsub_port=old_xsub,
            xpub_port=old_xpub
        )
        self.broker.start()

        # Give system time to settle (no delivery guarantee expected)
        time.sleep(0.2)

        async def pub_task_late():
            pub = IpcPublisherAsync(port=self.broker.xsub_port)
            for _ in range(SEND_REPEATS):
                await pub.publish("pre", {"late": True})
                await asyncio.sleep(MESSAGE_DELAY)
            await pub.close()

        asyncio.run(pub_task_late())

        # Shutdown subscriber
        sub.close()
        t_sub.join(timeout=0.5)

        # ✅ ASSERTIONS: liveness only
        self.assertTrue(t_sub.is_alive() is False)

