# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

import os
import sys
import random
from typing import Optional

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.tests_base import F1TelemetryUnitTestsBase
from lib.f1_types import PacketHeader, F1PacketType

# ----------------------------------------------------------------------------------------------------------------------


class F1TypesTest(F1TelemetryUnitTestsBase):
    """
    Base class for F1 telemetry types parser unit tests
    """

    @staticmethod
    def getRandomHeader(packet_type: F1PacketType, game_year: int, num_players: Optional[int] = 20) -> PacketHeader:
        """Generate a random packet header object.

        Args:
            packet_type (F1PacketType): Packet type
            game_year (int): Game year
            num_players (Optional[int], optional): Number of players. Defaults to 20.

        Returns:
            PacketHeader: Random packet header object
        """

        return PacketHeader.from_values(
            packet_format=2000+game_year,
            game_year=game_year,
            game_major_version=random.getrandbits(8),
            game_minor_version=random.getrandbits(8),
            packet_version=random.getrandbits(8),
            packet_type=packet_type,
            session_uid=random.getrandbits(64),
            session_time=F1TypesTest.getRandomFloat(),
            frame_identifier=random.getrandbits(32),
            overall_frame_identifier=random.getrandbits(32),
            player_car_index=random.randint(0, num_players),
            secondary_player_car_index=255
        )

    @staticmethod
    def getRandomFloat() -> float:
        """Generate a random 4-byte float

        Returns:
            float: Random 4-byte float
        """
        # return struct.unpack('f', struct.pack('f', random.uniform(-3.4e38, 3.4e38)))[0]
        return random.uniform(0.0, 255.0)

    @staticmethod
    def getRandomBool() -> bool:
        """Generate a random boolean

        Returns:
            bool: Random boolean
        """
        return random.choice([True, False])

    @staticmethod
    def getRandomUserName(max_length: Optional[int] = 47) -> str:
        """
        Generates a random username

        Args:
            max_length (Optional[int], optional): The maximum length of the username. Defaults to 47.

        Returns:
            str: The random username
        """

        funky_chars = [
            '😀', '😎', '🚀', '🌟', '🎉', '🍀', '✨', '💥', '🎶', '⚡',
            'ç', 'é', 'â', 'ê', 'î', 'ô', 'û', 'æ', 'œ', 'ß', 'ñ', 'ø', 'å', 'ƒ', 'Ω', 'π', 'ψ', 'Δ', 'θ', 'λ'
        ]

        # Create a random username
        username = ''
        while len(username.encode('utf-8')) < max_length:
            char = random.choice(funky_chars)
            if len((username + char).encode('utf-8')) < max_length:
                username += char
            else:
                break

        return username
