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

import pytest

from lib.f1_types import F1PacketType, PacketHeader

# ----------------------------------------------------------------------------------------------------------------------


def _make_header(major: int, minor: int) -> PacketHeader:
    """Build a header whose only interesting fields are the game version ones."""
    return PacketHeader.from_values(
        packet_format=2026,
        game_year=25,
        game_major_version=major,
        game_minor_version=minor,
        packet_version=1,
        packet_type=F1PacketType.MOTION,
        session_uid=1234567890,
        session_time=12.5,
        frame_identifier=100,
        overall_frame_identifier=100,
        player_car_index=0,
        secondary_player_car_index=255,
    )


class TestPacketHeaderGameVersion:
    """game_version joins the two version bytes the game sends into the "X.Y" string
    users see."""

    @pytest.mark.parametrize("major, minor, expected", [
        (1, 0, "1.0"),
        (1, 25, "1.25"),
        (25, 4, "25.4"),
        (0, 0, "0.0"),
        (255, 255, "255.255"),
    ])
    def test_formats_major_dot_minor(self, major, minor, expected):
        assert _make_header(major, minor).game_version == expected

    def test_minor_is_not_zero_padded(self):
        # 1.5 is a different version from 1.05 - the raw byte must not be padded
        assert _make_header(1, 5).game_version == "1.5"

    def test_survives_a_serialisation_round_trip(self):
        header = _make_header(1, 25)
        assert PacketHeader(header.to_bytes()).game_version == header.game_version

    def test_reflects_the_parsed_bytes(self):
        # The property reads the unpacked fields, so parsing raw bytes must feed it too
        header = PacketHeader(_make_header(3, 17).to_bytes())
        assert header.m_gameMajorVersion == 3
        assert header.m_gameMinorVersion == 17
        assert header.game_version == "3.17"
