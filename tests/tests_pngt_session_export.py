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
#
# Tests for apps.backend.state_mgmt_layer.pngt_export.in_export_scope() -- the
# "which drivers get exported" policy. This is app/business logic (not lib/pngt,
# which has no scope concept at all), so its tests live here rather than under
# tests_pngt*.py.

import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.state_mgmt_layer.pngt_export import in_export_scope

# ----------------------------------------------------------------------------------------------------------------------
# in_export_scope() decision table
# ----------------------------------------------------------------------------------------------------------------------

def test_restricted_telemetry_never_in_scope():
    assert in_export_scope(
        is_public=False, is_player=True, is_spectating=False, spectator_mode=True, other_players=True,
    ) is False


def test_own_car_always_in_scope_even_when_other_players_cars_disabled():
    assert in_export_scope(
        is_public=True, is_player=True, is_spectating=False, spectator_mode=False, other_players=False,
    ) is True


@pytest.mark.parametrize("other_players,expected", [(False, False), (True, True)])
def test_other_human_car_respects_other_players(other_players, expected):
    assert in_export_scope(
        is_public=True, is_player=False, is_spectating=False, spectator_mode=False, other_players=other_players,
    ) is expected


@pytest.mark.parametrize("spectator_mode,expected", [(False, False), (True, True)])
def test_spectator_mode_gate_applies_regardless_of_is_player(spectator_mode, expected):
    # No "own car" while spectating, so is_player=True must not bypass the gate.
    assert in_export_scope(
        is_public=True, is_player=True, is_spectating=True, spectator_mode=spectator_mode, other_players=True,
    ) is expected
