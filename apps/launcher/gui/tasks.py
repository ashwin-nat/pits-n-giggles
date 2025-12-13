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

from typing import TYPE_CHECKING

from PySide6.QtCore import QRunnable

from apps.hud.common import serialise_data
from apps.launcher.subsystems import PngAppMgrBase
from lib.config import PngSettings
from lib.version import (get_newer_stable_releases, get_releases_info,
                         is_update_available)
from lib.ipc import IpcPubSubBroker

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class StopSubsystemTask(QRunnable):
    def __init__(self, subsystem: PngAppMgrBase, reason: str):
        super().__init__()
        self.subsystem = subsystem
        self.reason = reason

    def run(self):
        self.subsystem.stop(self.reason)

class StopBrokerTask(QRunnable):
    def __init__(self, broker: IpcPubSubBroker):
        super().__init__()
        self.broker = broker

    def run(self):
        self.broker.close()

class SettingsChangeTask(QRunnable):
    def __init__(self, subsystem: PngAppMgrBase, new_settings: PngSettings):
        super().__init__()
        self.subsystem = subsystem
        self.new_settings = new_settings

    def run(self):
        if self.subsystem.on_settings_change(self.new_settings):
            self.subsystem.restart("Settings changed")

class UpdateCheckTask(QRunnable):
    def __init__(self, main_window: "PngLauncherWindow", curr_ver: str):
        super().__init__()
        self.version = curr_ver
        self.main_window = main_window

    def run(self):
        try:
            releases = get_releases_info()
            if is_update_available(self.version, releases):
                newer_versions = get_newer_stable_releases(self.version, releases)
                assert newer_versions
                self.main_window.update_data.emit(serialise_data(newer_versions))

        except Exception as e: # pylint: disable=broad-except
            self.main_window.error_log(f"Failed to check for updates - {e}")
