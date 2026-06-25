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

"""Shared router/dealer wire-protocol constants.

Single source of truth for the bytes that travel on the wire between the
``IpcRouter`` and its dealer clients. Both the sync (``client.py``) and async
(``async_client.py``) dealers import from here so the protocol can never drift
between the two implementations.

Wire shapes::

    command:  [dest,        reply_flag, topic, payload]   # dealer -> router -> dealer
    reply:    [orig_sender, payload]                       # answer to send()
    ack:      [orig_sender, ACK_SENTINEL]                  # fire() receipt ack
"""

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# reply_flag values on a 4-frame command frame.
_REPLY_REQUIRED = b"\x01"
_NO_REPLY       = b"\x00"

# Single fixed byte marking a fire() receipt ack. A 2-frame message whose second
# frame equals this is an ack; otherwise it is a send() reply (a JSON payload,
# which always begins '{' / '[' / digit / quote, so the two can never collide).
ACK_SENTINEL = b"\x06"
