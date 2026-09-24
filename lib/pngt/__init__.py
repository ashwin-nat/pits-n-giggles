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
from .ingest.dto import (
    BaseTelemetrySnapshot,
    IngestCompletedLap,
    IngestDriverExportData,
    IngestLapMetadata,
    TelemetryRecorderConfig,
)
from .ingest.export_adapter import InProgressLapContext, adapt_driver_export
from .ingest.mapper import SensorMapper
from .ingest.recorder import DriverTelemetryRecorder
from .ingest.session_export_manager import (
    DriverExportCandidate,
    SessionExportManager,
    SessionExportScopeConfig,
)
from .mutate import delete_laps, mark_lap_good, rename_session
from .reader import ParsedSession, read_driver_laps, read_lap_telemetry, read_session
from .writer import write_session

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    'BaseTelemetrySnapshot',
    'CompletedLap',
    'CorruptedTelemetryError',
    'DeleteLapsResult',
    'DriverExportCandidate',
    'DriverExportData',
    'DriverNotFoundError',
    'DriverRecord',
    'DriverTelemetryRecorder',
    'IngestCompletedLap',
    'IngestDriverExportData',
    'IngestLapMetadata',
    'InProgressLapContext',
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
    'SensorConfig',
    'SensorMapper',
    'SensorType',
    'SessionBest',
    'SessionExportManager',
    'SessionExportScopeConfig',
    'SessionMetadata',
    'TelemetryRecorderConfig',
    'TrackInfo',
    'UnsupportedFormatError',
    'UnsupportedVersionError',
    'adapt_driver_export',
    'delete_laps',
    'mark_lap_good',
    'read_driver_laps',
    'read_lap_telemetry',
    'read_session',
    'rename_session',
    'write_session',
]
