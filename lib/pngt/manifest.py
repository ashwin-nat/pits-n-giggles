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

import json
import zipfile
from pathlib import Path

from .exceptions import (InvalidHeaderError, NotAZipFileError,
                         UnsupportedFormatError, UnsupportedVersionError)

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

HEADER_FORMAT = "pngt"
HEADER_VERSION = 1
HEADER_ENTRY = "header.json"
SENSOR_MANIFEST_ENTRY = "manifest.json"
ZIP_MAGIC = b"PK\x03\x04"

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def validate_pngt_zip(path: Path | str) -> zipfile.ZipFile:
    """Validates a .pngt file per the format spec's mandatory open sequence: sniff
    ZIP magic bytes, open as a ZipFile, read header.json, assert format then
    version. Returns the open ZipFile positioned for further reads by the caller —
    the caller is responsible for closing it.

    Raises NotAZipFileError / InvalidHeaderError / UnsupportedFormatError /
    UnsupportedVersionError.
    """
    path = Path(path)

    with open(path, "rb") as f:
        magic = f.read(4)
    if magic != ZIP_MAGIC:
        raise NotAZipFileError(path)

    zf = zipfile.ZipFile(path)  # pylint: disable=consider-using-with
    try:
        raw = zf.read(HEADER_ENTRY)
    except KeyError as exc:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is missing") from exc

    try:
        header = json.loads(raw)
    except json.JSONDecodeError as exc:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is not valid JSON: {exc}") from exc

    if not isinstance(header, dict) or "format" not in header or "version" not in header:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is missing required keys 'format'/'version'")

    actual_format = header["format"]
    if actual_format != HEADER_FORMAT:
        zf.close()
        raise UnsupportedFormatError(path, actual_format)

    actual_version = header["version"]
    if actual_version != HEADER_VERSION:
        zf.close()
        raise UnsupportedVersionError(path, actual_version, HEADER_VERSION)

    return zf
