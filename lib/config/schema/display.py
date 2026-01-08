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

from typing import Any, ClassVar, Dict

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class DisplaySettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    disable_browser_autoload: bool = Field(
        default=False,
        description="Disable automatic opening of the web page in the browser",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )

    refresh_interval: int = Field(
        default=200,
        gt=0,
        description="Web dashboard / Text overlays refresh interval (ms)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )

    local_telemetry_rate: int = Field(
        default=5,
        gt=0,
        description="Low frequency telemetry send rate (used for table based overlays) (Hz)",
        json_schema_extra={
            "ui": {
                "type" : "radio_buttons",
                "options": [5, 10, 25, 60],
                "visible": True,
                "ext_info": [
                    'Not recommended to go super high, as it will increase the CPU load. '
                    '5 Hz is good enough for most cases'
                ]
            }
        }
    )
    telemetry_rate: int = Field(
        default=30,
        gt=0,
        description="Internal telemetry send rate (Hz)",
        json_schema_extra={
            "ui": {
                "type" : "radio_buttons",
                "options": [30, 60],
                "visible": True,
                "ext_info": [
                    '30 Hz is good enough for most cases. '
                    'Use 60 Hz if you want even higher accuracy in input and track radar overlays'
                ]
            }
        }
    )
    realtime_overlay_fps: int = Field(
        default=60,
        gt=0,
        description="Realtime overlay FPS",
        json_schema_extra={
            "ui": {
                "type" : "radio_buttons",
                "options": [30, 60, 90],
                "visible": True,
                "ext_info": [
                    'Uses GPU. Higher FPS will cause more GPU load.'
                ]
            }
        }
    )
    use_cpu_acceleration: bool = Field(
        default=False,
        description="Use CPU acceleration for overlays",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info" : [
                    "Forces CPU-based rendering for compatibility with older GPU's.\n"
                    "May reduce visual quality and increase CPU usage."
                ]
            }
        }
    )

    @property
    def hud_refresh_interval(self) -> int:
        # hz to ms
        return 1000 // self.realtime_overlay_fps

    @property
    def realtime_overlay_update_interval_ms(self) -> int:
        # fps to ms
        return 1000 // self.realtime_overlay_fps

    @property
    def local_telemetry_interval_ms(self) -> int:
        # hz to ms
        return 1000 // self.local_telemetry_rate
