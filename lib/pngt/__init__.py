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

from .dto import (
    CompletedLap,
    DeleteLapsResult,
    DriverExportData,
    DriverRecord,
    LapMetadata,
    MarkLapGoodResult,
    ParsedDriver,
    ParsedLap,
    ParsedSessionMetadata,
    SensorConfig,
    SensorType,
    SessionBest,
    SessionMetadata,
    TrackInfo,
)
from .exceptions import (
    CorruptedTelemetryError,
    DriverNotFoundError,
    InvalidHeaderError,
    InvalidManifestError,
    MalformedSessionError,
    NotAZipFileError,
    PngtError,
    UnsupportedFormatError,
    UnsupportedVersionError,
)
from .mutate import delete_laps, mark_lap_good, rename_session
from .reader import ParsedSession, read_driver_laps, read_lap_telemetry, read_session
from .recorder import BaseTelemetrySnapshot, DriverTelemetryRecorder, RecordedSensor
from .writer import write_session

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    'BaseTelemetrySnapshot',
    'CompletedLap',
    'CorruptedTelemetryError',
    'DeleteLapsResult',
    'DriverExportData',
    'DriverNotFoundError',
    'DriverRecord',
    'DriverTelemetryRecorder',
    'InvalidHeaderError',
    'InvalidManifestError',
    'LapMetadata',
    'MalformedSessionError',
    'MarkLapGoodResult',
    'NotAZipFileError',
    'ParsedDriver',
    'ParsedLap',
    'ParsedSession',
    'ParsedSessionMetadata',
    'PngtError',
    'RecordedSensor',
    'SensorConfig',
    'SensorType',
    'SessionBest',
    'SessionMetadata',
    'TrackInfo',
    'UnsupportedFormatError',
    'UnsupportedVersionError',
    'delete_laps',
    'mark_lap_good',
    'read_driver_laps',
    'read_lap_telemetry',
    'read_session',
    'rename_session',
    'write_session',
]
