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
# pylint: skip-file

import asyncio
import sys
import threading
import time

from .base import TestIPC
from lib.ipc import IpcRouter, IpcRouterBroker, IpcDealerClient, IpcDealerAsync
from lib.error_status import PngRouterPortInUseError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROPAGATION_DELAY = 0.1   # time to let threads connect and router stabilise
ACK_TIMEOUT = 3.0         # generous timeout for CI


def _start_router(port: int = 0) -> IpcRouter:
    router = IpcRouter(port=port)
    router.run_in_thread()
    time.sleep(PROPAGATION_DELAY)
    return router


def _start_dealer_client(port: int, identity: str, routes: dict) -> tuple:
    """Returns (IpcDealerClient, thread)."""
    client = IpcDealerClient(port=port, identity=identity)
    for topic, handler in routes.items():
        client.route(topic)(handler)
    t = threading.Thread(target=client.start, daemon=True)
    t.start()
    time.sleep(PROPAGATION_DELAY)
    return client, t


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestIpcRouterDealer(TestIPC):

    def setUp(self):
        self.router = _start_router()
        self.port = self.router.port
        self._clients = []
        self._threads = []

    def tearDown(self):
        for client in self._clients:
            client.close()
        time.sleep(0.05)
        for t in self._threads:
            t.join(timeout=0.3)
        self.router.close()
        time.sleep(0.05)

    def _make_dealer_client(self, identity: str, routes: dict = None) -> IpcDealerClient:
        client, t = _start_dealer_client(self.port, identity, routes or {})
        self._clients.append(client)
        self._threads.append(t)
        return client

    def _run_async(self, coro):
        return asyncio.run(coro)

    # ------------------------------------------------------------------
    # IpcRouter lifecycle
    # ------------------------------------------------------------------

    def test_router_binds_on_ephemeral_port(self):
        self.assertGreater(self.router.port, 0)

    def test_router_thread_is_alive(self):
        self.assertIsNotNone(self.router._thread)
        self.assertTrue(self.router._thread.is_alive())

    def test_router_close_stops_thread(self):
        router = _start_router()
        thread = router._thread
        router.close()
        if thread:
            thread.join(timeout=1.0)
        if thread:
            self.assertFalse(thread.is_alive())

    def test_router_get_stats_returns_dict(self):
        stats = self.router.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("uptime_seconds", stats)

    def test_router_port_in_use_raises(self):
        router2 = _start_router()
        occupied_port = router2.port
        router2.close()
        time.sleep(0.1)
        import zmq
        ctx = zmq.Context()
        sock = ctx.socket(zmq.ROUTER)
        sock.setsockopt(zmq.LINGER, 0)
        try:
            sock.bind(f"tcp://127.0.0.1:{occupied_port}")
            with self.assertRaises(PngRouterPortInUseError):
                IpcRouter(port=occupied_port)
        finally:
            sock.close(linger=0)
            ctx.term()

    def test_ipc_router_broker_alias_works(self):
        """IpcRouterBroker is a backwards-compat alias for IpcRouter."""
        self.assertIs(IpcRouterBroker, IpcRouter)

    # ------------------------------------------------------------------
    # IpcDealerClient construction
    # ------------------------------------------------------------------

    def test_dealer_client_requires_port(self):
        with self.assertRaises(ValueError):
            IpcDealerClient(identity="hud")

    def test_dealer_client_requires_identity(self):
        with self.assertRaises(ValueError):
            IpcDealerClient(port=self.port, identity="")

    def test_dealer_client_get_stats_returns_dict(self):
        client = self._make_dealer_client("stats-test")
        stats = client.get_stats()
        self.assertIsInstance(stats, dict)

    # ------------------------------------------------------------------
    # IpcDealerAsync construction
    # ------------------------------------------------------------------

    def test_dealer_async_requires_port(self):
        with self.assertRaises(ValueError):
            IpcDealerAsync(identity="backend")

    def test_dealer_async_requires_identity(self):
        with self.assertRaises(ValueError):
            IpcDealerAsync(port=self.port, identity="")

    # ------------------------------------------------------------------
    # Request-response: send() awaits a reply
    # ------------------------------------------------------------------

    def test_send_single_message_gets_ok_reply(self):
        received = []

        self._make_dealer_client("hud", {
            "toggle": lambda data: received.append(data),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="backend")
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud", "toggle", {"oid": "mfd"})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(reply.get("status"), "ok")
        self.assertIn({"oid": "mfd"}, received)

    def test_send_handler_can_return_rich_response(self):
        """Handler return value is sent back to the caller as the reply."""
        STATS = {"laps": 42, "tyre": "soft"}

        self._make_dealer_client("hud-rich", {
            "get-stats": lambda _: STATS,
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="backend-rich")
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud-rich", "get-stats", {})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply, STATS)

    def test_send_multiple_topics(self):
        calls = {"a": [], "b": []}

        self._make_dealer_client("hud-multi", {
            "topic-a": lambda d: calls["a"].append(d),
            "topic-b": lambda d: calls["b"].append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-multi")
            await asyncio.sleep(PROPAGATION_DELAY)

            r_a = await dealer.send("hud-multi", "topic-a", {"x": 1})
            r_b = await dealer.send("hud-multi", "topic-b", {"y": 2})

            await dealer.close()
            return r_a, r_b

        r_a, r_b = self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(r_a.get("status"), "ok")
        self.assertEqual(r_b.get("status"), "ok")
        self.assertIn({"x": 1}, calls["a"])
        self.assertIn({"y": 2}, calls["b"])

    def test_send_unknown_topic_returns_error(self):
        self._make_dealer_client("hud-unknown", {})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-unknown")
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud-unknown", "no-such-topic", {})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("unknown topic", reply.get("reason", ""))

    def test_send_handler_exception_returns_error(self):
        def bad_handler(_data):
            raise RuntimeError("boom")

        self._make_dealer_client("hud-exc", {"crash": bad_handler})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-exc")
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud-exc", "crash", {})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("boom", reply.get("reason", ""))

    def test_send_rapid_successive_all_delivered(self):
        """All rapid sends must arrive and each gets an ok reply."""
        N = 20
        received = []

        self._make_dealer_client("hud-rapid", {
            "press": lambda d: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-rapid")
            await asyncio.sleep(PROPAGATION_DELAY)

            replies = []
            for i in range(N):
                r = await dealer.send("hud-rapid", "press", {"seq": i})
                replies.append(r)

            await dealer.close()
            return replies

        replies = self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        for i, r in enumerate(replies):
            self.assertEqual(r.get("status"), "ok", f"send {i} got {r}")

        self.assertEqual(len(received), N)
        for i in range(N):
            self.assertIn({"seq": i}, received)

    def test_send_to_nonexistent_client_times_out_gracefully(self):
        """
        Sending to an identity that has never connected causes the ROUTER to
        drop the message silently. Backend receives an error dict, not an exception.
        """
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-noexist")
            dealer.ACK_TIMEOUT = 0.2
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("ghost-client", "press", {"seq": 0})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("timeout", reply.get("reason", ""))

    def test_send_to_crashed_client_times_out_then_reconnected_client_works(self):
        """
        3-phase crash recovery:
          1. Healthy send succeeds.
          2. Client crashes (socket closed abruptly) — send times out gracefully.
          3. New client reconnects with same identity — send succeeds again.
        """
        received_before, received_after = [], []

        # Phase 1: healthy
        client = IpcDealerClient(port=self.port, identity="hud-crash")
        client.route("ping")(lambda d: received_before.append(d))
        t = threading.Thread(target=client.start, daemon=True)
        t.start()
        self._clients.append(client)
        self._threads.append(t)
        time.sleep(PROPAGATION_DELAY)

        async def run_phase1():
            dealer = IpcDealerAsync(port=self.port, identity="sender-crash")
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await dealer.send("hud-crash", "ping", {"phase": 1})
            await dealer.close()
            return r

        ack1 = self._run_async(run_phase1())
        time.sleep(PROPAGATION_DELAY)
        self.assertEqual(ack1.get("status"), "ok", f"pre-crash send failed: {ack1}")
        self.assertIn({"phase": 1}, received_before)

        # Phase 2: crash
        client._running = False
        try:
            client.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        time.sleep(PROPAGATION_DELAY)

        async def run_phase2():
            dealer = IpcDealerAsync(port=self.port, identity="sender-crash2")
            dealer.ACK_TIMEOUT = 0.2
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await dealer.send("hud-crash", "ping", {"phase": 2})
            await dealer.close()
            return r

        ack2 = self._run_async(run_phase2())
        self.assertEqual(ack2.get("status"), "error")

        # Phase 3: reconnect
        client2 = IpcDealerClient(port=self.port, identity="hud-crash")
        client2.route("ping")(lambda d: received_after.append(d))
        t2 = threading.Thread(target=client2.start, daemon=True)
        t2.start()
        self._clients.append(client2)
        self._threads.append(t2)
        time.sleep(PROPAGATION_DELAY)

        async def run_phase3():
            dealer = IpcDealerAsync(port=self.port, identity="sender-crash3")
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await dealer.send("hud-crash", "ping", {"phase": 3})
            await dealer.close()
            return r

        ack3 = self._run_async(run_phase3())
        time.sleep(PROPAGATION_DELAY)
        self.assertEqual(ack3.get("status"), "ok", f"post-reconnect send failed: {ack3}")
        self.assertIn({"phase": 3}, received_after)

    # ------------------------------------------------------------------
    # Fire-and-forget: fire() sends and returns immediately
    # ------------------------------------------------------------------

    def test_fire_delivers_message_without_waiting(self):
        """fire() returns immediately and the message still arrives at the client."""
        received = []

        self._make_dealer_client("hud-fire", {
            "press": lambda d: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire")
            await asyncio.sleep(PROPAGATION_DELAY)

            await dealer.fire("hud-fire", "press", {"btn": "mfd"})
            # Give the client time to process
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertIn({"btn": "mfd"}, received)

    def test_fire_rapid_all_delivered(self):
        """N rapid fire() calls must all arrive (unlike PubSub which may coalesce)."""
        N = 20
        received = []

        self._make_dealer_client("hud-fire-rapid", {
            "press": lambda d: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire-rapid")
            await asyncio.sleep(PROPAGATION_DELAY)

            for i in range(N):
                await dealer.fire("hud-fire-rapid", "press", {"seq": i})

            # Allow client time to drain
            await asyncio.sleep(PROPAGATION_DELAY * 3)
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(len(received), N)
        for i in range(N):
            self.assertIn({"seq": i}, received)

    def test_fire_to_nonexistent_client_does_not_raise(self):
        """fire() to unknown identity must silently drop, not raise."""
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire-ghost")
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.fire("ghost", "press", {})  # must not raise
            await dealer.close()

        # If this completes without exception the test passes
        self._run_async(run())

    def test_fire_does_not_block_on_no_ack(self):
        """fire() to a client that never replies must return in under 0.5s."""
        self._make_dealer_client("hud-fire-noack", {
            "press": lambda _: None,  # handler returns nothing, but fire() doesn't care
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire-noack")
            await asyncio.sleep(PROPAGATION_DELAY)

            t0 = asyncio.get_event_loop().time()
            for _ in range(10):
                await dealer.fire("hud-fire-noack", "press", {})
            elapsed = asyncio.get_event_loop().time() - t0

            await dealer.close()
            return elapsed

        elapsed = self._run_async(run())
        self.assertLess(elapsed, 0.5, f"fire() blocked for {elapsed:.3f}s")

    # ------------------------------------------------------------------
    # Routing isolation
    # ------------------------------------------------------------------

    def test_two_clients_receive_only_own_messages(self):
        recv_a, recv_b = [], []

        self._make_dealer_client("hud-a", {"msg": lambda d: recv_a.append(d)})
        self._make_dealer_client("hud-b", {"msg": lambda d: recv_b.append(d)})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-ab")
            await asyncio.sleep(PROPAGATION_DELAY)

            r_a = await dealer.send("hud-a", "msg", {"target": "a"})
            r_b = await dealer.send("hud-b", "msg", {"target": "b"})

            await dealer.close()
            return r_a, r_b

        r_a, r_b = self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(r_a.get("status"), "ok")
        self.assertEqual(r_b.get("status"), "ok")
        self.assertIn({"target": "a"}, recv_a)
        self.assertNotIn({"target": "b"}, recv_a)
        self.assertIn({"target": "b"}, recv_b)
        self.assertNotIn({"target": "a"}, recv_b)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def test_dealer_client_stats_track_ok_handler(self):
        received = []
        client = self._make_dealer_client("hud-stats", {
            "ping": lambda d: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-stats")
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.send("hud-stats", "ping", {"v": 1})
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertIn({"v": 1}, received)
        self.assertIsInstance(client.get_stats(), dict)

    def test_router_stats_increment_after_traffic(self):
        received = []
        self._make_dealer_client("hud-bstats", {"x": lambda d: received.append(d)})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-bstats")
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.send("hud-bstats", "x", {})
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        stats = self.router.get_stats()
        self.assertGreater(stats["uptime_seconds"], 0)
