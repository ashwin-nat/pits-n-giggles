import re
import sys
from collections import Counter

FRAME_RE = re.compile(r"frameId=(\d+)")

def analyse_log(file_path: str):
    frames = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            m = FRAME_RE.search(line)
            if m:
                frames.append(int(m.group(1)))

    if not frames:
        print("No frames found.")
        return

    total = len(frames)
    unique_frames = len(set(frames))
    min_frame = min(frames)
    max_frame = max(frames)

    duplicates = Counter(frames)
    duplicate_frames = {k: v for k, v in duplicates.items() if v > 1}

    out_of_order = []
    gaps = []
    missing_frames = []

    prev = frames[0]

    for current in frames[1:]:
        if current < prev:
            out_of_order.append((prev, current))

        elif current > prev + 1:
            gap_range = (prev + 1, current - 1)
            gaps.append(gap_range)
            missing_frames.extend(range(prev + 1, current))

        prev = current

    print("=== Frame Analysis ===")
    print(f"Total packets:              {total}")
    print(f"Unique frames:              {unique_frames}")
    print(f"Min frameId:                {min_frame}")
    print(f"Max frameId:                {max_frame}")
    print(f"Duplicate frame IDs:        {len(duplicate_frames)}")
    print(f"Out-of-order transitions:   {len(out_of_order)}")
    print(f"Gaps detected:              {len(gaps)}")
    print(f"Total missing frame count:  {len(missing_frames)}")

    print("\n--- Top 10 Most Duplicated Frames ---")
    for frame, count in sorted(duplicate_frames.items(), key=lambda x: -x[1])[:10]:
        print(f"frameId={frame} → {count} times")

    print("\n--- Out Of Order ---")
    for prev, current in out_of_order:
        print(f"{prev} → {current}")

    print("\n--- Gaps ---")
    for start, end in gaps:
        print(f"Missing range: {start} → {end}")

    print("\n--- Missing Frames ---")
    print(missing_frames)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python frame_id_analysis.py <logfile>")
        sys.exit(1)

    analyse_log(sys.argv[1])
