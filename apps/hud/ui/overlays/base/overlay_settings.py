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

"""Declarative overlay settings. An overlay lists them in popover_settings(); the popover renders them.

Every value is read through a callable, so the popover can re-read them all after any change.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from dataclasses import dataclass
from typing import Callable, Optional, Union

from lib.config import HudSettings

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class Toggle:
    """A checkbox."""
    label: str
    value: Callable[[], bool]
    on_change: Callable[[bool], None]


@dataclass(frozen=True)
class Slider:
    """An integer slider, with an optional label above it."""
    label: Optional[str]
    lo: int
    hi: int
    unit: str
    value: Callable[[], int]
    on_change: Callable[[int], None]
    enabled: Callable[[], bool] = lambda: True

    @classmethod
    def for_config_field(cls, name: str, label: str, unit: str,
                         value: Callable[[], int], on_change: Callable[[int], None]) -> "Slider":
        """A slider with the range a config field declares."""
        ui = HudSettings.model_fields[name].json_schema_extra["ui"] # pylint: disable=unsubscriptable-object
        return cls(label, ui["min"], ui["max"], unit, value, on_change)


@dataclass(frozen=True)
class Note:
    """A wrapped warning line, shown while visible() is true."""
    text: Callable[[], str]
    visible: Callable[[], bool]


@dataclass(frozen=True)
class Divider:
    """A thin horizontal line between groups."""


OverlaySetting = Union[Toggle, Slider, Note, Divider]
