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

"""Send management IPC commands to a subsystem that the launcher is running.

Usage:
    poetry run python -m apps.dev_tools.ipc_injector --port <port> <payload.json>

The payload file is JSON, holding one message:

    {"cmd": "set-overlays-opacity", "args": {"opacity": 50}}

or a list of messages, sent in order:

    [
        {"cmd": "__ping__"},
        {"cmd": "next-page"}
    ]

"cmd" (str, required) is __ping__, __get_stats__ or a name the subsystem registers with mgmt.on().
"args" (object, optional, default {}) takes whatever keys that command's handler reads.

__shutdown__ and __terminate__ need --force. __heartbeat__ is always refused.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import json
import sys

from lib.ipc import IpcClientSync

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def main() -> int:
    """Send the message(s) in a JSON file to a subsystem's management IPC port.

    Returns:
        int: 0 if every reply has status "success", else 1
    """
    parser = argparse.ArgumentParser(description="Send management IPC commands to a running subsystem")
    parser.add_argument("file", help='JSON file: {"cmd": str, "args": dict} or a list of those')
    parser.add_argument("--port", required=True, type=int, help="Subsystem's management IPC port")
    parser.add_argument("--timeout", type=float, default=5.0, help="Reply timeout in seconds (default: 5)")
    parser.add_argument("--force", action="store_true", help="Allow __shutdown__ and __terminate__")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8-sig") as f:
        payload = json.load(f)
    messages = payload if isinstance(payload, list) else [payload]

    # Heartbeats would mask a real launcher failure, so --force does not unlock them
    blocked = {"__heartbeat__"} if args.force else {"__heartbeat__", "__shutdown__", "__terminate__"}
    # Validate the whole list first so a bad entry doesn't leave it half sent
    for msg in messages:
        if not isinstance(msg, dict) or not isinstance(msg.get("cmd"), str):
            print(f'Invalid message, expected an object with a string "cmd": {msg}', file=sys.stderr)
            return 1
        if msg["cmd"] in blocked:
            print(f"Refusing to send {msg['cmd']}", file=sys.stderr)
            return 1

    all_ok = True
    for msg in messages:
        # A REQ socket can't send again after a timeout, hence one client per message
        client = IpcClientSync(args.port, timeout_ms=int(args.timeout * 1000))
        try:
            reply = client.request(msg["cmd"], msg.get("args"))
        finally:
            client.close()
        print(json.dumps(reply, ensure_ascii=True), flush=True)
        all_ok = all_ok and reply.get("status") == "success"

    return 0 if all_ok else 1

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
