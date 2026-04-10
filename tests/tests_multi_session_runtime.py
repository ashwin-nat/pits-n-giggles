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
import os
import sys
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from apps.backend.intf_layer.telemetry_ui_tasks import frontEndMessageTask, webClientUpdateTask
from lib.inter_task_communicator import AsyncInterTaskCommunicator, ITCMessage


class _DummyPayload:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def toJSON(self):
        return {"session": self._session_id}


class _DummyFrontendServer:
    def __init__(self) -> None:
        self.sent = []
        self.m_logger = type("LoggerStub", (), {"debug": lambda *args, **kwargs: None})()

    async def send_to_clients_of_type(self, event, data, client_type):
        self.sent.append((event, data, str(client_type)))


class _DummyWebUpdateServer:
    def __init__(self):
        self.events = []

    def is_any_client_interested_in_event(self, _event: str) -> bool:
        return True

    async def send_to_clients_interested_in_event(self, event, data):
        self.events.append((event, data))


class _PeriodicDataStub:
    def __init__(self, session_state):
        self._session_state = session_state

    def toJSON(self):
        return {"session": self._session_state.session_id, "kind": "periodic"}


class _OverlayDataStub:
    def __init__(self, session_state):
        self._session_state = session_state

    def toJSON(self, _with_sample_data):
        return {"session": self._session_state.session_id, "kind": "overlay"}


class _SessionStub:
    def __init__(self, session_id: str):
        self.session_id = session_id


class TestMultiSessionIsolation(F1TelemetryUnitTestsBase):

    async def test_frontend_queue_names_are_session_local(self):
        itc = AsyncInterTaskCommunicator()
        shutdown_event = asyncio.Event()
        server_a = _DummyFrontendServer()
        server_b = _DummyFrontendServer()

        task_a = asyncio.create_task(frontEndMessageTask(server_a, shutdown_event, "frontend-update:session-a"))
        task_b = asyncio.create_task(frontEndMessageTask(server_b, shutdown_event, "frontend-update:session-b"))

        await itc.send(
            "frontend-update:session-a",
            ITCMessage(
                m_message_type=ITCMessage.MessageType.CUSTOM_MARKER,
                m_message=_DummyPayload("session-a"),
            ),
        )
        await itc.send(
            "frontend-update:session-b",
            ITCMessage(
                m_message_type=ITCMessage.MessageType.CUSTOM_MARKER,
                m_message=_DummyPayload("session-b"),
            ),
        )

        await asyncio.sleep(0.05)
        shutdown_event.set()
        await itc.unblock_receivers()
        await asyncio.gather(task_a, task_b)

        self.assertEqual(len(server_a.sent), 1)
        self.assertEqual(len(server_b.sent), 1)
        self.assertEqual(server_a.sent[0][1]["message"]["session"], "session-a")
        self.assertEqual(server_b.sent[0][1]["message"]["session"], "session-b")

    async def test_web_updates_use_their_own_session_state(self):
        server_a = _DummyWebUpdateServer()
        server_b = _DummyWebUpdateServer()
        state_a = _SessionStub("session-a")
        state_b = _SessionStub("session-b")

        with patch("apps.backend.intf_layer.telemetry_ui_tasks.PeriodicUpdateData", _PeriodicDataStub), \
             patch("apps.backend.intf_layer.telemetry_ui_tasks.StreamOverlayData", _OverlayDataStub):
            await webClientUpdateTask(server_a, state_a, False)
            await webClientUpdateTask(server_b, state_b, False)

        self.assertEqual(server_a.events[0][1]["session"], "session-a")
        self.assertEqual(server_a.events[1][1]["session"], "session-a")
        self.assertEqual(server_b.events[0][1]["session"], "session-b")
        self.assertEqual(server_b.events[1][1]["session"], "session-b")
