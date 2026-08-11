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

from .io.ini import load_config_from_ini, save_config_to_ini
from .io.json import load_config_from_json, save_config_to_json
from .io.migration import load_config_migrated, maybe_migrate_legacy_hud_layout
from .schema.capture import CaptureSettings
from .schema.display import AutoOpenDashboardMode, DisplaySettings
from .schema.forwarding import ForwardingSettings
from .schema.https import HttpsSettings
from .schema.hud.hud import (HudSettings, MfdTyreWearRateType,
                             OverlaysFuelEstimationMode, OverlaysSpeedUnit,
                             WeatherMFDUIType)
from .schema.hud.layout import OverlayId, OverlayPosition
from .schema.hud.mfd import MfdPageId, MfdPageSettings, MfdSettings
from .schema.hud.timing_tower import (TimingTowerColId, TimingTowerColOptions,
                                      TimingTowerColSettings)
from .schema.network import NetworkSettings
from .schema.pit_time_loss import PitTimeLossF1, PitTimeLossF2
from .schema.png import PngSettings
from .schema.prediction import HarvestPowerSmoothing, PredictionSettings
from .schema.privacy import PrivacySettings
from .schema.stream_overlay import StreamOverlaySettings
from .types.file_path_str import FilePathStr

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    'CaptureSettings',
    'AutoOpenDashboardMode',
    'DisplaySettings',
    'ForwardingSettings',
    'NetworkSettings',
    'PitTimeLossF1',
    'PitTimeLossF2',
    'PngSettings',
    'PredictionSettings',
    'HarvestPowerSmoothing',
    'PrivacySettings',
    'StreamOverlaySettings',
    'HttpsSettings',
    'HudSettings',
    'MfdPageId',
    'MfdSettings',
    'MfdPageSettings',
    'TimingTowerColId',
    'TimingTowerColOptions',
    'TimingTowerColSettings',
    'WeatherMFDUIType',
    'MfdTyreWearRateType',
    'OverlaysSpeedUnit',
    'OverlaysFuelEstimationMode',

    'FilePathStr',

    'load_config_from_ini',
    'save_config_to_ini',

    'load_config_from_json',
    'save_config_to_json',

    'load_config_migrated',
    'maybe_migrate_legacy_hud_layout',

    'OverlayPosition',

    'OverlayId',
]
