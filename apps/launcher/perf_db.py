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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
import sqlite3
from pathlib import Path

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

DB_FILENAME = "png_perf.db"
MAX_SESSIONS = 100

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_db_path(base_dir: Path) -> Path:
    """Return the path to the perf metrics SQLite database file."""
    return base_dir / DB_FILENAME

def save_session_stats(base_dir: Path, stats: dict) -> None:
    """
    Persist per-session perf metrics to the SQLite database.

    Creates the database and table on first use. Enforces a retention
    policy of MAX_SESSIONS rows, dropping the oldest sessions when the
    limit is exceeded.

    Args:
        base_dir (Path): Directory in which the database file is stored.
        stats (dict): Stats dict returned by subsystem get_stats() calls,
                      merged with launcher-level fields (e.g. uptime_seconds).
    """
    db_path = get_db_path(base_dir)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS perf_sessions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL DEFAULT (datetime('now')),
                stats     TEXT    NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO perf_sessions (stats) VALUES (:stats)",
            {"stats": json.dumps(stats)}
        )
        conn.execute(
            """
            DELETE FROM perf_sessions
            WHERE id NOT IN (
                SELECT id FROM perf_sessions ORDER BY id DESC LIMIT :limit
            )
            """,
            {"limit": MAX_SESSIONS}
        )
        conn.commit()
