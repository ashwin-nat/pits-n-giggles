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

"""Shared error text for the reqrep servers' reserved callback slots.

IpcServerAsync and IpcServerSync have no common base, so the wording lives here rather than
being written out six times.
"""

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def reserved_slot_error(server_name: str, slot: str, purpose: str, instead: str) -> ValueError:
    """Build the error raised when a reserved callback slot is registered twice.

    The `instead` clause is the point of the message. Someone registering a second shutdown
    callback almost always wants "run my code on shutdown", and the answer to that is the
    subsystem hook the base already calls - not another launcher command. Naming the wrong
    alternative would send them off to build a second, unrelated thing.

    Args:
        server_name (str): The server's name, so the message names the offending subsystem
        slot (str): Slot being registered, e.g. "shutdown"
        purpose (str): What the parent uses it for, e.g. "the parent's shutdown handshake"
        instead (str): The hook the caller almost certainly wanted, and what it does

    Returns:
        ValueError: The error to raise
    """

    return ValueError(
        f"{server_name}: a {slot} callback is already registered. This is a single slot "
        f"reserved for {purpose}, filled by lib/subsystem before setup() runs, so a second "
        f"registration would silently discard the base's and break that contract. "
        f"DO THIS INSTEAD: {instead} "
        f'(if you actually meant to add an unrelated launcher command, use .on("<command-name>")).')
