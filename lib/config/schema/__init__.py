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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from .capture import CaptureSettings
from .display import DisplaySettings
from .forwarding import ForwardingSettings
from .https import HttpsSettings
from .hud import (INPUT_TELEMETRY_OVERLAY_ID, LAP_TIMER_OVERLAY_ID,
                  MFD_OVERLAY_ID, TIMING_TOWER_OVERLAY_ID,
                  TRACK_MAP_OVERLAY_ID, TRACK_RADAR_OVERLAY_ID, HudSettings,
                  MfdPageSettings, MfdSettings, OverlayPosition,
                  TimingTowerColOptions)
from .mcp_cfg import McpSettings
from .network import NetworkSettings
from .pit_time_loss_f1 import PitTimeLossF1
from .pit_time_loss_f2 import PitTimeLossF2
from .png import PngSettings
from .privacy import PrivacySettings
from .stream_overlay import StreamOverlaySettings
from .subsys_ctrl import SubSysCtrl

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    'CaptureSettings',
    'DisplaySettings',
    'ForwardingSettings',
    'HttpsSettings',
    'HudSettings',
    'MfdSettings',
    'MfdPageSettings',
    'TimingTowerColOptions',
    'OverlayPosition',
    'McpSettings',
    'NetworkSettings',
    'PitTimeLossF1',
    'PitTimeLossF2',
    'PngSettings',
    'PrivacySettings',
    'StreamOverlaySettings',
    'SubSysCtrl',

    'INPUT_TELEMETRY_OVERLAY_ID',
    'LAP_TIMER_OVERLAY_ID',
    'MFD_OVERLAY_ID',
    'TIMING_TOWER_OVERLAY_ID',
    'TRACK_MAP_OVERLAY_ID',
    'TRACK_RADAR_OVERLAY_ID',
]
