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
from lib.ipc import IpcRouter, IpcDealerClient, IpcDealerAsync
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

    def test_dealer_client_get_stats_returns_dict(self):
        client = self._make_dealer_client("stats-test")
        stats = client.get_stats()
        self.assertIsInstance(stats, dict)

    # ------------------------------------------------------------------
    # Request-response: send() awaits a reply
    # ------------------------------------------------------------------

    def test_send_single_message_gets_ok_reply(self):
        received = []

        self._make_dealer_client("hud", {
            "toggle": lambda data, _sender: received.append(data),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="backend")
            asyncio.create_task(dealer.start())
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
            "get-stats": lambda _, _sender: STATS,
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="backend-rich")
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud-rich", "get-stats", {})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply, STATS)

    def test_send_multiple_topics(self):
        calls = {"a": [], "b": []}

        self._make_dealer_client("hud-multi", {
            "topic-a": lambda d, _sender: calls["a"].append(d),
            "topic-b": lambda d, _sender: calls["b"].append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-multi")
            asyncio.create_task(dealer.start())
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
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await dealer.send("hud-unknown", "no-such-topic", {})
            await dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("unknown topic", reply.get("reason", ""))

    def test_send_handler_exception_returns_error(self):
        def bad_handler(_data, _sender):
            raise RuntimeError("boom")

        self._make_dealer_client("hud-exc", {"crash": bad_handler})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-exc")
            asyncio.create_task(dealer.start())
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
            "press": lambda d, _sender: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-rapid")
            asyncio.create_task(dealer.start())
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
            asyncio.create_task(dealer.start())
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
        client.route("ping")(lambda d, _sender: received_before.append(d))
        t = threading.Thread(target=client.start, daemon=True)
        t.start()
        self._clients.append(client)
        self._threads.append(t)
        time.sleep(PROPAGATION_DELAY)

        async def run_phase1():
            dealer = IpcDealerAsync(port=self.port, identity="sender-crash")
            asyncio.create_task(dealer.start())
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
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await dealer.send("hud-crash", "ping", {"phase": 2})
            await dealer.close()
            return r

        ack2 = self._run_async(run_phase2())
        self.assertEqual(ack2.get("status"), "error")

        # Phase 3: reconnect
        client2 = IpcDealerClient(port=self.port, identity="hud-crash")
        client2.route("ping")(lambda d, _sender: received_after.append(d))
        t2 = threading.Thread(target=client2.start, daemon=True)
        t2.start()
        self._clients.append(client2)
        self._threads.append(t2)
        time.sleep(PROPAGATION_DELAY)

        async def run_phase3():
            dealer = IpcDealerAsync(port=self.port, identity="sender-crash3")
            asyncio.create_task(dealer.start())
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
            "press": lambda d, _sender: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire")
            asyncio.create_task(dealer.start())
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
            "press": lambda d, _sender: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire-rapid")
            asyncio.create_task(dealer.start())
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
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.fire("ghost", "press", {})  # must not raise
            await dealer.close()

        # If this completes without exception the test passes
        self._run_async(run())

    def test_fire_does_not_block_on_no_ack(self):
        """fire() to a client that never replies must return in under 0.5s."""
        self._make_dealer_client("hud-fire-noack", {
            "press": lambda _, _sender: None,  # handler returns nothing, but fire() doesn't care
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-fire-noack")
            asyncio.create_task(dealer.start())
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

        self._make_dealer_client("hud-a", {"msg": lambda d, _sender: recv_a.append(d)})
        self._make_dealer_client("hud-b", {"msg": lambda d, _sender: recv_b.append(d)})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-ab")
            asyncio.create_task(dealer.start())
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
            "ping": lambda d, _sender: received.append(d),
        })

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-stats")
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.send("hud-stats", "ping", {"v": 1})
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertIn({"v": 1}, received)
        self.assertIsInstance(client.get_stats(), dict)

    def test_router_stats_increment_after_traffic(self):
        received = []
        self._make_dealer_client("hud-bstats", {"x": lambda d, _sender: received.append(d)})

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-bstats")
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            await dealer.send("hud-bstats", "x", {})
            await dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        stats = self.router.get_stats()
        self.assertGreater(stats["uptime_seconds"], 0)

    # ------------------------------------------------------------------
    # IpcDealerAsync inbound routing — async dealer as receiver
    # ------------------------------------------------------------------

    def test_async_dealer_receives_fire_from_async_sender(self):
        """fire() from one async dealer reaches the registered handler on another."""
        received = []

        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-fire")

            @receiver.route("press")
            def on_press(data, _sender):
                received.append(data)

            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-fire")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            await sender.fire("async-recv-fire", "press", {"btn": "mfd"})
            # Give the recv loop time to dispatch
            await asyncio.sleep(PROPAGATION_DELAY)

            await sender.close()
            await receiver.close()

        self._run_async(run())
        self.assertIn({"btn": "mfd"}, received)

    def test_async_dealer_receives_send_and_replies_with_dict(self):
        """send() to an async dealer receiver gets the handler's dict reply."""
        STATS = {"laps": 7, "tyre": "hard"}

        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-send")

            @receiver.route("get-stats")
            def on_get_stats(_data, _sender):
                return STATS

            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-send")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await sender.send("async-recv-send", "get-stats", {})

            await sender.close()
            await receiver.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply, STATS)

    def test_async_dealer_send_replies_with_ok_when_handler_returns_none(self):
        """Handler returning None (or non-dict) yields a default ok reply."""
        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-none")

            @receiver.route("ack")
            def on_ack(_data, _sender):
                return None

            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-none")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await sender.send("async-recv-none", "ack", {})

            await sender.close()
            await receiver.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "ok")

    def test_async_dealer_supports_async_handler(self):
        """Coroutine handlers are awaited and their return value sent back."""
        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-coro")

            @receiver.route("slow")
            async def on_slow(data, _sender):
                await asyncio.sleep(0.01)
                return {"echo": data, "via": "coro"}

            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-coro")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await sender.send("async-recv-coro", "slow", {"x": 1})

            await sender.close()
            await receiver.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("via"), "coro")
        self.assertEqual(reply.get("echo"), {"x": 1})

    def test_async_dealer_unknown_topic_sends_error_reply(self):
        """Sending to a registered identity but unknown topic returns an error dict."""
        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-unknown")
            # No routes registered.
            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-unknown")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await sender.send("async-recv-unknown", "no-such-topic", {})

            await sender.close()
            await receiver.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("unknown topic", reply.get("reason", ""))

    def test_async_dealer_handler_exception_sends_error_reply(self):
        """A raising handler must return an error reply, not crash the loop."""
        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-exc")

            @receiver.route("crash")
            def boom(_data, _sender):
                raise RuntimeError("kaboom")

            asyncio.create_task(receiver.start())

            sender = IpcDealerAsync(port=self.port, identity="async-send-exc")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await sender.send("async-recv-exc", "crash", {})

            # Recv loop should still be alive after an exception — try again.
            @receiver.route("ok")
            def on_ok(_data, _sender):
                return {"status": "ok", "after": "crash"}

            reply2 = await sender.send("async-recv-exc", "ok", {})

            await sender.close()
            await receiver.close()
            return reply, reply2

        reply, reply2 = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("kaboom", reply.get("reason", ""))
        self.assertEqual(reply2.get("after"), "crash")

    def test_async_dealer_invalid_json_payload_sends_error_reply(self):
        """A malformed inbound payload yields an error reply, no crash."""
        import zmq as _zmq

        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-recv-badjson")

            @receiver.route("anything")
            def on_anything(_data, _sender):
                return {"status": "ok"}

            asyncio.create_task(receiver.start())

            # Send raw garbage bytes as payload using a hand-rolled DEALER.
            ctx = _zmq.asyncio.Context()
            raw = ctx.socket(_zmq.DEALER)
            raw.setsockopt(_zmq.LINGER, 0)
            raw.setsockopt(_zmq.IDENTITY, b"async-send-badjson")
            raw.connect(f"tcp://127.0.0.1:{self.port}")
            await asyncio.sleep(PROPAGATION_DELAY)

            await raw.send_multipart([
                b"async-recv-badjson", b"\x01", b"anything", b"not-json{{{",
            ])
            try:
                frames = await asyncio.wait_for(
                    raw.recv_multipart(), timeout=ACK_TIMEOUT
                )
            finally:
                raw.close(linger=0)
                ctx.term()

            await receiver.close()
            return frames

        frames = self._run_async(run())
        import orjson as _orjson
        reply = _orjson.loads(frames[-1])
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("invalid", reply.get("reason", ""))

    def test_async_dealer_send_and_receive_interleaved(self):
        """Async dealer simultaneously serves inbound and issues outbound sends."""
        sync_received = []
        bridge_received = []

        # Sync client that the bridge will send to.
        self._make_dealer_client("sync-peer", {
            "from-bridge": lambda d, _sender: sync_received.append(d),
        })

        async def run():
            bridge = IpcDealerAsync(port=self.port, identity="bridge")

            @bridge.route("from-other")
            def on_from_other(data, _sender):
                bridge_received.append(data)
                return {"status": "ok", "ack": data}

            asyncio.create_task(bridge.start())

            other = IpcDealerAsync(port=self.port, identity="other")
            asyncio.create_task(other.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            # Other sends to bridge while bridge sends to sync — interleaved.
            other_task = asyncio.create_task(
                other.send("bridge", "from-other", {"n": 1})
            )
            bridge_reply = await bridge.send("sync-peer", "from-bridge", {"n": 2})
            other_reply = await other_task

            await other.close()
            await bridge.close()
            return bridge_reply, other_reply

        bridge_reply, other_reply = self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(bridge_reply.get("status"), "ok")
        self.assertEqual(other_reply.get("ack"), {"n": 1})
        self.assertIn({"n": 1}, bridge_received)
        self.assertIn({"n": 2}, sync_received)

    def test_async_dealer_close_cancels_recv_loop(self):
        """close() cleanly cancels the background recv task."""
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="async-close-loop")

            @dealer.route("noop")
            def noop(_data, _sender):
                return None

            asyncio.create_task(dealer.start())
            await asyncio.sleep(0)  # yield so start() sets _recv_task
            self.assertIsNotNone(dealer._recv_task)
            self.assertFalse(dealer._recv_task.done())

            await dealer.close()
            return dealer

        dealer = self._run_async(run())
        self.assertIsNone(dealer._recv_task)

    def test_async_dealer_close_while_send_in_flight_unblocks(self):
        """close() while awaiting a reply must not hang — send() returns error."""
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="async-close-inflight")
            dealer.ACK_TIMEOUT = 5.0  # we want close() to be the unblocker, not timeout
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            send_task = asyncio.create_task(
                dealer.send("ghost-no-receiver", "press", {"x": 1})
            )
            # Let the send actually post and start awaiting the reply.
            await asyncio.sleep(0.05)

            # Close while the send is awaiting.
            close_task = asyncio.create_task(dealer.close())

            reply = await asyncio.wait_for(send_task, timeout=2.0)
            await close_task
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")

    def test_async_dealer_send_requires_start(self):
        """send() raises AssertionError if start() has not been called."""
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="sender-no-start")
            await asyncio.sleep(PROPAGATION_DELAY)
            with self.assertRaises(AssertionError):
                await dealer.send("ghost", "ping", {"v": 99})
            await dealer.close()

        self._run_async(run())

    def test_async_dealer_fire_requires_start(self):
        """fire() raises AssertionError if start() has not been called."""
        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="fire-no-start")
            with self.assertRaises(AssertionError):
                await dealer.fire("ghost", "ping", {})
            await dealer.close()

        self._run_async(run())

    # ------------------------------------------------------------------
    # IpcDealerClient outbound fire() / send()
    # ------------------------------------------------------------------

    def test_dealer_client_fire_delivers_to_async_receiver(self):
        """IpcDealerClient.fire() reaches an IpcDealerAsync that has called start()."""
        received = []

        async def run():
            receiver = IpcDealerAsync(port=self.port, identity="async-fire-recv")

            @receiver.route("press")
            def on_press(data, _sender):
                received.append(data)

            asyncio.create_task(receiver.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            client = self._make_dealer_client("sync-fire-send", {})
            time.sleep(PROPAGATION_DELAY)

            client.fire("async-fire-recv", "press", {"btn": "x"})
            await asyncio.sleep(PROPAGATION_DELAY)

            await receiver.close()

        self._run_async(run())
        self.assertIn({"btn": "x"}, received)

    def test_dealer_client_fire_delivers_to_sync_receiver(self):
        """IpcDealerClient.fire() reaches another IpcDealerClient receiver."""
        received = []

        receiver = self._make_dealer_client("sync-recv-fire", {
            "ping": lambda d, _sender: received.append(d),
        })
        sender = self._make_dealer_client("sync-send-fire", {})
        time.sleep(PROPAGATION_DELAY)

        sender.fire("sync-recv-fire", "ping", {"v": 42})
        time.sleep(PROPAGATION_DELAY * 3)

        self.assertIn({"v": 42}, received)

    def test_dealer_client_send_gets_reply_from_async_dealer(self):
        """IpcDealerClient.send() → IpcDealerAsync handler returns dict → sync caller gets it."""
        STATS = {"laps": 5, "tyre": "medium"}

        # Run the async receiver in a background event loop so sync send() can be called
        # from the test thread without deadlocking the event loop.
        loop = asyncio.new_event_loop()
        stop_event = threading.Event()
        receiver_holder = []

        async def async_main():
            receiver = IpcDealerAsync(port=self.port, identity="async-send-reply")

            @receiver.route("get-stats")
            def on_get_stats(_data, _sender):
                return STATS

            asyncio.ensure_future(receiver.start())
            receiver_holder.append(receiver)
            # Wait until the test signals us to stop.
            while not stop_event.is_set():
                await asyncio.sleep(0.05)
            await receiver.close()

        loop_thread = threading.Thread(target=loop.run_until_complete, args=(async_main(),), daemon=True)
        loop_thread.start()
        time.sleep(PROPAGATION_DELAY)

        client = self._make_dealer_client("sync-send-rpc", {})
        time.sleep(PROPAGATION_DELAY)

        reply = client.send("async-send-reply", "get-stats", {})

        stop_event.set()
        loop_thread.join(timeout=2.0)
        loop.close()

        self.assertEqual(reply, STATS)

    def test_dealer_client_send_gets_reply_from_sync_receiver(self):
        """IpcDealerClient.send() → IpcDealerClient handler returns dict → caller gets it."""
        receiver = self._make_dealer_client("sync-recv-rpc", {
            "echo": lambda d, _sender: {"echoed": d},
        })
        sender = self._make_dealer_client("sync-send-rpc2", {})
        time.sleep(PROPAGATION_DELAY)

        reply = sender.send("sync-recv-rpc", "echo", {"x": 7})
        self.assertEqual(reply.get("echoed"), {"x": 7})

    def test_dealer_client_send_requires_start(self):
        """IpcDealerClient.send() raises AssertionError if start() has not been called."""
        client = IpcDealerClient(port=self.port, identity="sync-send-no-start")
        with self.assertRaises(AssertionError):
            client.send("ghost", "ping", {})
        client.close()

    def test_dealer_client_fire_requires_start(self):
        """IpcDealerClient.fire() raises AssertionError if start() has not been called."""
        client = IpcDealerClient(port=self.port, identity="sync-fire-no-start")
        with self.assertRaises(AssertionError):
            client.fire("ghost", "ping", {})
        client.close()

    def test_dealer_client_send_timeout_on_no_receiver(self):
        """IpcDealerClient.send() to a non-existent identity returns error dict, no hang."""
        sender = self._make_dealer_client("sync-timeout-sender", {})
        time.sleep(PROPAGATION_DELAY)

        reply = sender.send("ghost-identity", "press", {}, timeout=0.2)
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("timeout", reply.get("reason", ""))

    def test_dealer_client_send_unknown_topic_returns_error(self):
        """Sending an unregistered topic to a sync receiver returns an error reply."""
        receiver = self._make_dealer_client("sync-recv-unknown2", {})
        sender = self._make_dealer_client("sync-send-unknown2", {})
        time.sleep(PROPAGATION_DELAY)

        reply = sender.send("sync-recv-unknown2", "no-such-topic", {})
        self.assertEqual(reply.get("status"), "error")
        self.assertIn("unknown topic", reply.get("reason", ""))

    def test_dealer_client_send_does_not_block_inbound_receive(self):
        """
        While one thread calls send(), the loop must still process inbound commands.
        Verify by having an inbound fire arrive during an outbound send.
        """
        inbound_received = []

        # This receiver also handles inbound messages from someone else.
        receiver = self._make_dealer_client("sync-bidir-loop", {
            "inbound": lambda d, _sender: inbound_received.append(d),
            "echo": lambda d, _sender: {"echoed": d},
        })
        sender = self._make_dealer_client("sync-bidir-sender", {})
        # A third party that fires at the receiver while the send is in-flight.
        third = self._make_dealer_client("sync-bidir-third", {})
        time.sleep(PROPAGATION_DELAY)

        # Fire the inbound message first (it'll sit in the DEALER socket queue).
        third.fire("sync-bidir-loop", "inbound", {"from": "third"})
        time.sleep(0.02)

        # Now do a send — the loop must deliver the inbound fire AND the reply.
        reply = sender.send("sync-bidir-loop", "echo", {"x": 1})
        time.sleep(PROPAGATION_DELAY)

        self.assertEqual(reply.get("echoed"), {"x": 1})
        self.assertIn({"from": "third"}, inbound_received)

    def test_dealer_client_concurrent_fire_calls_all_delivered(self):
        """N concurrent fire() calls from multiple threads all arrive."""
        N = 20
        received = []
        receiver = self._make_dealer_client("sync-concurrent-recv", {
            "press": lambda d, _sender: received.append(d),
        })
        sender = self._make_dealer_client("sync-concurrent-send", {})
        time.sleep(PROPAGATION_DELAY)

        threads = []
        for i in range(N):
            t = threading.Thread(target=sender.fire, args=("sync-concurrent-recv", "press", {"seq": i}))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(PROPAGATION_DELAY * 3)
        self.assertEqual(len(received), N)
        for i in range(N):
            self.assertIn({"seq": i}, received)

    # ------------------------------------------------------------------
    # Bidirectional exchange: sync ↔ async, both sides send and receive
    # ------------------------------------------------------------------

    def test_bidir_sync_sends_async_replies(self):
        """Sync client calls send() → async dealer handles it → reply received."""
        loop = asyncio.new_event_loop()
        stop_event = threading.Event()

        async def async_main():
            async_dealer = IpcDealerAsync(port=self.port, identity="bidir-async-a")

            @async_dealer.route("query")
            def on_query(data, _sender):
                return {"answer": data.get("q", "") + "-response"}

            asyncio.ensure_future(async_dealer.start())
            while not stop_event.is_set():
                await asyncio.sleep(0.05)
            await async_dealer.close()

        loop_thread = threading.Thread(target=loop.run_until_complete, args=(async_main(),), daemon=True)
        loop_thread.start()
        time.sleep(PROPAGATION_DELAY)

        sync_client = self._make_dealer_client("bidir-sync-a", {})
        time.sleep(PROPAGATION_DELAY)

        reply = sync_client.send("bidir-async-a", "query", {"q": "hello"})

        stop_event.set()
        loop_thread.join(timeout=2.0)
        loop.close()

        self.assertEqual(reply.get("answer"), "hello-response")

    def test_bidir_async_sends_sync_replies(self):
        """Async dealer calls send() → sync client handles it → reply received."""
        sync_client = self._make_dealer_client("bidir-sync-b", {
            "ping": lambda d, _sender: {"pong": d.get("n", 0) * 2},
        })

        async def run():
            async_dealer = IpcDealerAsync(port=self.port, identity="bidir-async-b")
            asyncio.create_task(async_dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            reply = await async_dealer.send("bidir-sync-b", "ping", {"n": 21})
            await async_dealer.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("pong"), 42)

    def test_bidir_fire_both_directions(self):
        """Both sides fire a message to each other; both arrive."""
        sync_received = []
        async_received = []

        sync_client = self._make_dealer_client("bidir-fire-sync", {
            "from-async": lambda d, _sender: sync_received.append(d),
        })

        async def run():
            async_dealer = IpcDealerAsync(port=self.port, identity="bidir-fire-async")

            @async_dealer.route("from-sync")
            def on_from_sync(data, _sender):
                async_received.append(data)

            asyncio.create_task(async_dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            sync_client.fire("bidir-fire-async", "from-sync", {"dir": "s→a"})
            await async_dealer.fire("bidir-fire-sync", "from-async", {"dir": "a→s"})
            await asyncio.sleep(PROPAGATION_DELAY * 2)

            await async_dealer.close()

        self._run_async(run())
        time.sleep(PROPAGATION_DELAY)

        self.assertIn({"dir": "s→a"}, async_received)
        self.assertIn({"dir": "a→s"}, sync_received)

    def test_bidir_simultaneous_exchange(self):
        """Both sides send to each other in parallel; all replies correct."""
        async def run():
            async_dealer = IpcDealerAsync(port=self.port, identity="bidir-sim-async")

            @async_dealer.route("async-echo")
            def on_async_echo(data, _sender):
                return {"async_got": data}

            asyncio.create_task(async_dealer.start())

            sync_client = self._make_dealer_client("bidir-sim-sync", {
                "sync-echo": lambda d, _sender: {"sync_got": d},
            })
            await asyncio.sleep(PROPAGATION_DELAY)
            time.sleep(PROPAGATION_DELAY)

            # Run both sends concurrently using a thread for the blocking sync send.
            sync_reply_holder = []

            def do_sync_send():
                sync_reply_holder.append(
                    sync_client.send("bidir-sim-async", "async-echo", {"from": "sync"})
                )

            t = threading.Thread(target=do_sync_send)
            t.start()

            async_reply = await async_dealer.send("bidir-sim-sync", "sync-echo", {"from": "async"})
            t.join(timeout=5.0)

            await async_dealer.close()
            return async_reply, sync_reply_holder[0] if sync_reply_holder else None

        async_reply, sync_reply = self._run_async(run())
        self.assertEqual(async_reply.get("sync_got"), {"from": "async"})
        self.assertIsNotNone(sync_reply)
        self.assertEqual(sync_reply.get("async_got"), {"from": "sync"})

    def test_bidir_rapid_back_and_forth(self):
        """N sequential send/reply cycles between sync and async complete correctly."""
        N = 10

        sync_client = self._make_dealer_client("bidir-rapid-sync", {
            "increment": lambda d, _sender: {"n": d["n"] + 1},
        })

        async def run():
            async_dealer = IpcDealerAsync(port=self.port, identity="bidir-rapid-async")

            @async_dealer.route("double")
            def on_double(data, _sender):
                return {"n": data["n"] * 2}

            asyncio.create_task(async_dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            time.sleep(PROPAGATION_DELAY)

            results = []
            for i in range(N):
                # Async → sync
                r1 = await async_dealer.send("bidir-rapid-sync", "increment", {"n": i})
                results.append(("async→sync", i, r1))
                # Sync → async (from a thread to avoid blocking the event loop)
                loop = asyncio.get_event_loop()
                r2 = await loop.run_in_executor(
                    None, sync_client.send, "bidir-rapid-async", "double", {"n": i}
                )
                results.append(("sync→async", i, r2))

            await async_dealer.close()
            return results

        results = self._run_async(run())
        self.assertEqual(len(results), N * 2)
        for direction, i, reply in results:
            if direction == "async→sync":
                self.assertEqual(reply.get("n"), i + 1, f"increment({i}) failed: {reply}")
            else:
                self.assertEqual(reply.get("n"), i * 2, f"double({i}) failed: {reply}")

    # ------------------------------------------------------------------
    # Startup order tests
    # ------------------------------------------------------------------

    def test_dealer_connects_before_router(self):
        """Sync client started before router; first send() succeeds once router is up."""
        # Grab a free port by letting a temporary router bind and immediately close.
        tmp_router = IpcRouter(port=0)
        free_port = tmp_router.port
        tmp_router.close()
        time.sleep(0.2)  # give OS time to release the port

        # Start client pointing at that port before any router is bound there.
        client = IpcDealerClient(port=free_port, identity="early-client")
        client.route("pong")(lambda _, _sender: {"pong": True})
        t = threading.Thread(target=client.start, daemon=True)
        t.start()
        self._clients.append(client)
        self._threads.append(t)

        # Now bind the router — ZMQ will reconnect the client automatically.
        router2 = IpcRouter(port=free_port)
        router2.run_in_thread()
        time.sleep(0.5)  # ZMQ reconnect typically completes within 100-300ms

        async def run():
            sender = IpcDealerAsync(port=free_port, identity="late-sender")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            reply = await sender.send("early-client", "pong", {})
            await sender.close()
            return reply

        reply = self._run_async(run())
        router2.close()
        self.assertEqual(reply.get("pong"), True)

    def test_router_starts_after_both_dealers(self):
        """Both dealers started before the router; messages flow once router is up."""
        tmp_router = IpcRouter(port=0)
        free_port = tmp_router.port
        tmp_router.close()
        time.sleep(0.2)  # give OS time to release the port reliably

        client_a = IpcDealerClient(port=free_port, identity="pre-a")
        client_a.route("hi")(lambda d, _sender: {"got": d})
        ta = threading.Thread(target=client_a.start, daemon=True)
        ta.start()
        self._clients.append(client_a)
        self._threads.append(ta)

        client_b = IpcDealerClient(port=free_port, identity="pre-b")
        client_b.route("hi")(lambda d, _sender: {"got": d})
        tb = threading.Thread(target=client_b.start, daemon=True)
        tb.start()
        self._clients.append(client_b)
        self._threads.append(tb)

        # Start the router after both clients are already "connected" (ZMQ will buffer).
        router2 = IpcRouter(port=free_port)
        router2.run_in_thread()

        # Retry until the route is live (ZMQ reconnect + router learning both identities
        # can take 100–500 ms under load; a fixed sleep is flaky on slow CI runners).
        deadline = time.monotonic() + 5.0
        reply = {"status": "error", "reason": "not started"}
        while time.monotonic() < deadline:
            reply = client_a.send("pre-b", "hi", {"n": 1}, timeout=0.5)
            if reply.get("got") is not None:
                break
            time.sleep(0.1)
        router2.close()
        self.assertEqual(reply.get("got"), {"n": 1})

    def test_dealer_reconnects_after_router_restart(self):
        """Router closed and restarted on same port; dealer reconnects automatically."""
        client = self._make_dealer_client("reconnect-client", {
            "echo": lambda d, _sender: {"echoed": d},
        })
        time.sleep(PROPAGATION_DELAY)

        # First send works.
        async def run1():
            sender = IpcDealerAsync(port=self.port, identity="reconnect-sender1")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await sender.send("reconnect-client", "echo", {"phase": 1})
            await sender.close()
            return r

        r1 = self._run_async(run1())
        self.assertEqual(r1.get("echoed"), {"phase": 1})

        # Restart router on the same port.
        old_port = self.port
        self.router.close()
        time.sleep(0.1)
        self.router = IpcRouter(port=old_port)
        self.router.run_in_thread()
        time.sleep(PROPAGATION_DELAY)

        async def run2():
            sender = IpcDealerAsync(port=old_port, identity="reconnect-sender2")
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await sender.send("reconnect-client", "echo", {"phase": 2})
            await sender.close()
            return r

        r2 = self._run_async(run2())
        self.assertEqual(r2.get("echoed"), {"phase": 2})

    # ------------------------------------------------------------------
    # Crash / recovery tests
    # ------------------------------------------------------------------

    def test_sync_dealer_crash_send_returns_error(self):
        """Async dealer sends to a crashed sync client → send() times out, no exception."""
        client = IpcDealerClient(port=self.port, identity="crash-sync-client")
        client.route("noop")(lambda d, _sender: None)
        t = threading.Thread(target=client.start, daemon=True)
        t.start()
        self._clients.append(client)
        self._threads.append(t)
        time.sleep(PROPAGATION_DELAY)

        # Crash the client.
        client._running = False
        try:
            client.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        time.sleep(0.05)

        async def run():
            sender = IpcDealerAsync(port=self.port, identity="crash-async-sender")
            sender.ACK_TIMEOUT = 0.3
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            reply = await sender.send("crash-sync-client", "noop", {})
            await sender.close()
            return reply

        reply = self._run_async(run())
        self.assertEqual(reply.get("status"), "error")

    def test_async_dealer_crash_send_returns_error(self):
        """Sync client sends to a crashed async dealer → send() times out, no exception.

        Note: this test intentionally simulates an unclean crash (socket closed without
        ctx.term()), so a ResourceWarning about an unclosed ZMQ context is expected.
        """
        async def setup():
            dealer = IpcDealerAsync(port=self.port, identity="crash-async-dealer")

            @dealer.route("noop")
            def noop(_d, _sender):
                return None

            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            # Crash it.
            if dealer._recv_task:
                dealer._recv_task.cancel()
            dealer.socket.close(linger=0)

        self._run_async(setup())
        time.sleep(0.05)

        client = self._make_dealer_client("crash-sync-sender", {})
        time.sleep(PROPAGATION_DELAY)

        reply = client.send("crash-async-dealer", "noop", {}, timeout=0.3)
        self.assertEqual(reply.get("status"), "error")

    def test_sync_dealer_crash_and_reconnect(self):
        """Sync client crashes and reconnects with same identity; next send() succeeds."""
        # Phase 1: healthy.
        client1 = IpcDealerClient(port=self.port, identity="resilient-sync")
        client1.route("echo")(lambda d, _sender: {"echoed": d})
        t1 = threading.Thread(target=client1.start, daemon=True)
        t1.start()
        self._clients.append(client1)
        self._threads.append(t1)
        time.sleep(PROPAGATION_DELAY)

        async def run_send(identity, data, timeout=ACK_TIMEOUT):
            sender = IpcDealerAsync(port=self.port, identity=identity)
            sender.ACK_TIMEOUT = timeout
            asyncio.create_task(sender.start())
            await asyncio.sleep(PROPAGATION_DELAY)
            r = await sender.send("resilient-sync", "echo", data)
            await sender.close()
            return r

        r1 = self._run_async(run_send("resilient-sndr-1", {"phase": 1}))
        self.assertEqual(r1.get("echoed"), {"phase": 1})

        # Phase 2: crash.
        client1._running = False
        try:
            client1.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        time.sleep(0.05)

        r2 = self._run_async(run_send("resilient-sndr-2", {"phase": 2}, timeout=0.3))
        self.assertEqual(r2.get("status"), "error")

        # Phase 3: new client reconnects with same identity.
        client2 = IpcDealerClient(port=self.port, identity="resilient-sync")
        client2.route("echo")(lambda d, _sender: {"echoed": d})
        t2 = threading.Thread(target=client2.start, daemon=True)
        t2.start()
        self._clients.append(client2)
        self._threads.append(t2)
        time.sleep(PROPAGATION_DELAY)

        r3 = self._run_async(run_send("resilient-sndr-3", {"phase": 3}))
        self.assertEqual(r3.get("echoed"), {"phase": 3})

    def test_async_dealer_late_reply_after_timeout_does_not_corrupt_next_send(self):
        """
        Scenario: sender times out waiting for reply, late reply arrives after timeout,
        then a subsequent send() to a healthy handler completes successfully.

        Verifies that the stale reply is silently dropped (tracked as unexpected_reply)
        and does not corrupt the pending-reply state for the next call.
        """
        # A slow handler that replies after a configurable delay.
        slow_reply_delay = [0.0]  # mutable so inner func can read updated value

        slow_client = IpcDealerClient(port=self.port, identity="slow-responder")

        def slow_handler(data, _sender):
            time.sleep(slow_reply_delay[0])
            return {"echoed": data}

        slow_client.route("echo")(slow_handler)
        t = threading.Thread(target=slow_client.start, daemon=True)
        t.start()
        self._clients.append(slow_client)
        self._threads.append(t)
        time.sleep(PROPAGATION_DELAY)

        async def run():
            dealer = IpcDealerAsync(port=self.port, identity="late-reply-sender")
            asyncio.create_task(dealer.start())
            await asyncio.sleep(PROPAGATION_DELAY)

            # Phase 1: send with a very short timeout; handler will reply late.
            slow_reply_delay[0] = 0.5
            dealer.ACK_TIMEOUT = 0.1
            r1 = await dealer.send("slow-responder", "echo", {"phase": 1})
            self.assertEqual(r1.get("status"), "error")  # timed out

            # Wait for the late reply to arrive and be dropped.
            await asyncio.sleep(0.6)

            # Phase 2: now use a generous timeout; handler replies promptly.
            slow_reply_delay[0] = 0.0
            dealer.ACK_TIMEOUT = ACK_TIMEOUT
            r2 = await dealer.send("slow-responder", "echo", {"phase": 2})

            stats = dealer.get_stats()
            await dealer.close()
            return r1, r2, stats

        r1, r2, stats = self._run_async(run())
        self.assertEqual(r1.get("status"), "error")
        self.assertEqual(r2.get("echoed"), {"phase": 2})
        # Late reply from phase 1 was dropped, not mistaken for phase 2's reply.
        self.assertGreaterEqual(
            stats.get("__DROP__", {}).get("unexpected_reply", {}).get("count", 0), 1
        )
