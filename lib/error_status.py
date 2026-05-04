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
PNG_ERROR_CODE_XPUB_PORT_IN_USE = 104
PNG_ERROR_CODE_XSUB_PORT_IN_USE = 105
PNG_ERROR_CODE_ROUTER_PORT_IN_USE = 106
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

class PngXpubPortInUseError(PngError):
    def __init__(self, err_msg: str = "Port already in use"):
        super().__init__(PNG_ERROR_CODE_XPUB_PORT_IN_USE, err_msg)

class PngXsubPortInUseError(PngError):
    def __init__(self, err_msg: str = "Port already in use"):
        super().__init__(PNG_ERROR_CODE_XSUB_PORT_IN_USE, err_msg)

class PngRouterPortInUseError(PngError):
    def __init__(self, err_msg: str = "Port already in use"):
        super().__init__(PNG_ERROR_CODE_ROUTER_PORT_IN_USE, err_msg)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def is_port_in_use_error(errno: int) -> bool:
    """
    Returns True if the error code indicates that the port is unavailable
    because it is already in use or cannot be bound.

    Platform-specific notes:

    macOS / BSD:
        48  -> EADDRINUSE (Address already in use)

    Linux:
        98  -> EADDRINUSE (Address already in use)

    Windows:
        10048 -> WSAEADDRINUSE (Address already in use)

        10013 -> WSAEACCES (Permission denied)
                 ⚠️ Important:
                 On Windows, this can ALSO occur when another process has bound
                 the port with exclusive access (e.g., SO_EXCLUSIVEADDRUSE).
                 In that case, the OS denies access instead of reporting a
                 typical "address already in use" error.

                 In practice, this often means:
                 "The port is effectively in use by another application."

    Because of this behavior, we treat 10013 as a "port unavailable" error
    for better cross-platform consistency and user experience.
    """
    return errno in {48, 98, 10048, 10013}
