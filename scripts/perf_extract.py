"""CLI tool for extracting perf metrics from the png_perf.db SQLite database.

Modes:
  --list              Print all session IDs and timestamps.
  --latest            Fetch stats JSON for the most recent row (by id DESC).
  --fetch             Fetch stats JSON for a specific session.
    --id N            Fetch by row ID.
    --time "HH:MM"    Fetch the session closest to the given time (today's date assumed).
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, date


def open_db(db_path: str) -> sqlite3.Connection:
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error as e:
        print(f"ERROR: could not open database '{db_path}': {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(con: sqlite3.Connection) -> None:
    rows = con.execute("SELECT id, timestamp FROM perf_sessions ORDER BY timestamp DESC").fetchall()
    if not rows:
        print("No sessions found.")
        return
    print(f"{'ID':>6}  {'Timestamp'}")
    print("-" * 30)
    for row in rows:
        print(f"{row['id']:>6}  {row['timestamp']}")


def cmd_latest(con: sqlite3.Connection) -> None:
    row = con.execute(
        "SELECT stats FROM perf_sessions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        print("ERROR: no sessions in DB", file=sys.stderr)
        sys.exit(1)
    stats = json.loads(row["stats"])
    print(json.dumps(stats, indent=2))


def cmd_fetch(con: sqlite3.Connection, row_id: int | None, time_str: str | None) -> None:
    if row_id is not None:
        row = con.execute(
            "SELECT stats FROM perf_sessions WHERE id = ?", (row_id,)
        ).fetchone()
        if row is None:
            print(f"ERROR: no session with id={row_id}", file=sys.stderr)
            sys.exit(1)
    elif time_str is not None:
        # Parse HH:MM (or HH:MM:SS), assume today's date
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                pass
        else:
            print(f"ERROR: unrecognised time format '{time_str}' — use HH:MM or HH:MM:SS", file=sys.stderr)
            sys.exit(1)

        target = datetime.combine(date.today(), t).isoformat(sep=" ")

        # Find the row whose timestamp is closest to the target
        rows = con.execute("SELECT id, timestamp, stats FROM perf_sessions").fetchall()
        if not rows:
            print("ERROR: no sessions in DB", file=sys.stderr)
            sys.exit(1)

        def _delta(r):
            try:
                return abs((datetime.fromisoformat(r["timestamp"]) - datetime.fromisoformat(target)).total_seconds())
            except ValueError:
                return float("inf")

        row = min(rows, key=_delta)
        print(f"# Closest session: id={row['id']}  timestamp={row['timestamp']}", file=sys.stderr)
    else:
        # Latest by timestamp
        row = con.execute(
            "SELECT stats FROM perf_sessions ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if row is None:
            print("ERROR: no sessions in DB", file=sys.stderr)
            sys.exit(1)

    stats = json.loads(row["stats"])
    print(json.dumps(stats, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract perf metrics from png_perf.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("db", help="Path to the SQLite DB file (e.g. png_perf.db)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List all session IDs and timestamps")
    mode.add_argument("--latest", action="store_true", help="Fetch stats JSON for the most recent row (by id DESC)")
    mode.add_argument("--fetch", action="store_true", help="Fetch stats JSON for a specific session")

    parser.add_argument("--id", type=int, metavar="N", help="Session row ID (use with --fetch)")
    parser.add_argument("--time", metavar="HH:MM", help="Closest session to this time today (use with --fetch)")

    args = parser.parse_args()

    if (args.list or args.latest) and (args.id is not None or args.time is not None):
        parser.error("--id and --time are only valid with --fetch")

    con = open_db(args.db)
    try:
        if args.list:
            cmd_list(con)
        elif args.latest:
            cmd_latest(con)
        else:
            cmd_fetch(con, args.id, args.time)
    finally:
        con.close()


if __name__ == "__main__":
    main()
