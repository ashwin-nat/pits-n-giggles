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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Optional, Set

from lib.f1_types import F1PacketBase, F1PacketType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SessionFrameGate:
    """
    Enforces monotonic ordering and per-frame packet-type uniqueness
    based on (sessionUID, frameIdentifier, packetId).

    Rules:
        • First packet is accepted.
        • New sessionUID resets internal ordering.
        • frameIdentifier == 0 resets ordering.
        • Frame must be monotonic (no backward frames).
        • Only one packet per packet type is allowed per frame.
    """

    __slots__ = (
        "_enabled",
        "_last_session_uid",
        "_last_frame",
        "_seen_packet_types",
        "_last_drop_reason",
    )


    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize the SessionFrameGate.

        Args:
            enabled: If False, all packets are accepted without validation.
        """
        self._enabled: bool = enabled
        self._last_session_uid: Optional[int] = None
        self._last_frame: Optional[int] = None
        self._seen_packet_types: Set[F1PacketType] = set()
        self._last_drop_reason: Optional[str] = None

    def should_accept(self, packet: F1PacketBase) -> bool:
        """
        Determine whether a packet should be accepted.

        Args:
            packet: Parsed telemetry packet.

        Returns:
            True if packet should be processed.
            False if packet should be dropped.
        """

        if not self._enabled:
            return True

        header = packet.m_header
        session_uid = header.m_sessionUID
        frame = header.m_frameIdentifier
        packet_type = header.m_packetId

        self._last_drop_reason = None

        # First packet
        if self._last_session_uid is None:
            self._last_session_uid = session_uid
            self._last_frame = frame
            self._seen_packet_types = set() if frame == 0 else {packet_type}
            return True

        # Session change
        if session_uid != self._last_session_uid:
            self._last_session_uid = session_uid
            self._last_frame = frame
            self._seen_packet_types = set() if frame == 0 else {packet_type}
            return True

        # ---- Special Case: frame == 0 ----
        if frame == 0:
            # Treat as reset / unstable state.
            # Always accept. Do not enforce uniqueness.
            self._last_frame = 0
            self._seen_packet_types = set()
            return True

        # ---- From here on, frame > 0 ----

        # Backward frame
        if self._last_frame is not None and self._last_frame != 0 and frame < self._last_frame:
            self._last_drop_reason = (
                f"Backward frame detected: "
                f"session={session_uid}, frame={frame}, "
                f"last_frame={self._last_frame}"
            )
            return False

        # New forward frame
        if self._last_frame is None or frame > self._last_frame:
            self._last_frame = frame
            self._seen_packet_types = {packet_type}
            return True

        # Same frame → enforce uniqueness
        if packet_type in self._seen_packet_types:
            self._last_drop_reason = (
                f"Duplicate packet type in frame: "
                f"session={session_uid}, frame={frame}, "
                f"packet_type={packet_type}"
            )
            return False

        self._seen_packet_types.add(packet_type)
        return True

    def get_last_drop_reason(self) -> Optional[str]:
        """
        Returns the reason for the most recently dropped packet,
        or None if last packet was accepted.
        """
        return self._last_drop_reason
