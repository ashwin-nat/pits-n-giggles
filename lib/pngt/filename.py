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

from datetime import datetime

from .dto import SessionMetadata

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def suggest_filename(session: SessionMetadata) -> str:
    """Suggests a cosmetic default filename, e.g.
    'spa-francorchamps-race-2024-06-01-1432.pngt'. Purely cosmetic per the format
    spec — write_session's dest_path is always explicit and required; this is a
    separate, composable helper, never invoked implicitly by write_session."""
    dt = datetime.fromisoformat(session.timestamp.replace("Z", "+00:00"))
    return f"{session.track.id}-{session.session_type}-{dt.strftime('%Y-%m-%d-%H%M')}.pngt"
