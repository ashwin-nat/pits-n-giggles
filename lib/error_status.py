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


# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

PNG_ERROR_CODE_HTTP_PORT_IN_USE = 100
PNG_LOST_CONN_TO_PARENT = 101
PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE = 102
PNG_ERROR_CODE_UNSUPPORTED_OS = 103
PNG_ERROR_CODE_UNKNOWN = 999

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngError(Exception):
    def __init__(self, exit_code: int, message: str = ""):
        self.exit_code = exit_code
        super().__init__(f"exiting with code {exit_code}: {message}")

class PngHttpPortInUseError(PngError):
    def __init__(self):
        super().__init__(PNG_ERROR_CODE_HTTP_PORT_IN_USE, "Port already in use")

class PngTelemetryPortInUseError(PngError):
    def __init__(self):
        super().__init__(PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE, "Port already in use")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def is_port_in_use_error(errno: int) -> bool:
    # errno 48: EADDRINUSE on macOS/BSD
    # errno 98: EADDRINUSE on Linux
    # errno 10048: WSAEADDRINUSE on Windows
    return errno in {48, 98, 10048}
