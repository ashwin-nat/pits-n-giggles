import re
from datetime import datetime
from statistics import mean, stdev
from pathlib import Path
from collections import defaultdict

# RELATIVE PATH TO LOG
LOG_PATH = Path("png.log")

# ONLY TRACK THESE SOURCES (exact filename:line)
TRACKED_SOURCES = {
    "transport.py:127",
    "task.py:92",
    "input_telemetry.py:87",
}

# Example:
# [2025-12-10T13:18:20.026] [CORE] [INFO] [transport.py:128] Published IPC payload seq=...
LOG_REGEX = re.compile(
    r"\[(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)\].*\[(?P<src>[^:\]]+:\d+)\]"
)

groups = defaultdict(list)

# -------------------- PARSE --------------------

with LOG_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        m = LOG_REGEX.search(line)
        if not m:
            continue

        src = m.group("src")
        if src not in TRACKED_SOURCES:
            continue  # ignore everything else

        ts = datetime.fromisoformat(m.group("ts"))
        groups[src].append(ts)

# -------------------- UTIL --------------------

def compute_intervals(times):
    """Convert timestamps → list of time deltas."""
    return [(t2 - t1).total_seconds() for t1, t2 in zip(times, times[1:])]

# -------------------- REPORT --------------------

print("\n================== PIPELINE TIMING STATS ==================\n")

for src in TRACKED_SOURCES:
    timestamps = groups.get(src, [])

    if len(timestamps) < 2:
        print(f"--- {src} ---")
        print("Not enough samples\n")
        continue

    intervals = compute_intervals(timestamps)

    count = len(timestamps)
    min_dt = min(intervals)
    max_dt = max(intervals)
    avg_dt = mean(intervals)
    sd_dt = stdev(intervals) if len(intervals) > 1 else 0.0
    avg_hz = 1.0 / avg_dt if avg_dt > 0 else 0.0

    # ----- STUTTER -----
    stutter_threshold = avg_dt * 2.0
    stutters = [dt for dt in intervals if dt > stutter_threshold]
    worst_spike_factor = max_dt / avg_dt if avg_dt > 0 else 0.0

    print(f"--- {src} ---")
    print(f"Updates        : {count}")
    print(f"Min interval   : {min_dt * 1000:.3f} ms")
    print(f"Max interval   : {max_dt * 1000:.3f} ms")
    print(f"Avg interval   : {avg_dt * 1000:.3f} ms")
    print(f"Std deviation  : {sd_dt * 1000:.3f} ms")
    print(f"Avg frequency  : {avg_hz:.2f} Hz")
    print(f"Stutter events : {len(stutters)}")
    print(f"Worst spike    : {worst_spike_factor:.2f}× slower than avg\n")

print("===========================================================\n")
