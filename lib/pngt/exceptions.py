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

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngtError(Exception):
    """Base exception for all .pngt format errors."""

class NotAZipFileError(PngtError):
    """Raised when the given path is not a valid ZIP archive (magic bytes mismatch)."""
    def __init__(self, path):
        super().__init__(f"Not a valid ZIP file: {path}")

class InvalidHeaderError(PngtError):
    """Raised when header.json is missing, unparsable, or missing required keys."""
    def __init__(self, path, reason):
        super().__init__(f"Invalid header.json in {path}: {reason}")

class InvalidManifestError(PngtError):
    """Raised when manifest.json (the sensor registry) is missing, unparsable, or a
    sensor entry is missing required keys."""
    def __init__(self, path, reason):
        super().__init__(f"Invalid manifest.json in {path}: {reason}")

class UnsupportedFormatError(PngtError):
    """Raised when manifest.json's 'format' field is not 'pngt'."""
    def __init__(self, path, actual_format):
        super().__init__(f"Unsupported format {actual_format!r} in {path} (expected 'pngt')")

class UnsupportedVersionError(PngtError):
    """Raised when manifest.json's 'version' field is not a supported version."""
    def __init__(self, path, actual_version, expected_version):
        super().__init__(
            f"Unsupported pngt version {actual_version!r} in {path} (expected {expected_version!r})"
        )

class MalformedSessionError(PngtError):
    """Raised when session.json, drivers.json, or laps.json is corrupt or missing required fields."""
    def __init__(self, path, reason):
        super().__init__(f"Malformed session data in {path}: {reason}")

class DriverNotFoundError(PngtError):
    """Raised when telemetry for a driver_index/lap_number cannot be found in the archive."""
    def __init__(self, path, driver_index):
        super().__init__(f"No telemetry found for driver_index {driver_index} in {path}")
