#!/usr/bin/env python3
"""pcap_to_svg.py — Generate SVG track maps from F1 game pcap files.

Extracts world coordinates from PacketMotionData and lap distance from
PacketLapData to produce accurate SVG polylines matching the game's
internal track geometry.

Usage:
    python apps/dev_tools/pcap_to_svg.py test_data/f1_24_mp_spectator_bahrain.f1pcap -o Sakhir_Bahrain.svg
    python apps/dev_tools/pcap_to_svg.py test_data/f1_25_sp_aus_5lap_1stop.f1pcap -o Melbourne.svg

Output is written to assets/track-maps/f1_<game_year>/ (auto-detected from pcap).
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# Add project root to sys.path so lib/ imports work
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))

from lib.f1_types.header import F1PacketType, PacketHeader
from lib.f1_types.packet_0_car_motion_data import PacketMotionData
from lib.f1_types.packet_2_lap_data import PacketLapData
from lib.packet_cap import F1PacketCapture


class TrackPoint(NamedTuple):
    lap_distance: float
    world_x: float
    world_z: float


def extract_game_year(pcap_path: str) -> int:
    """Read the game year from the first valid packet header.

    Returns:
        Full game year (e.g. 2025), or 0 if unreadable.
    """
    pcap = F1PacketCapture(file_name=pcap_path)
    header_len = PacketHeader.PACKET_LEN
    for _, raw in pcap.getPackets():
        if len(raw) < header_len:
            continue
        try:
            header = PacketHeader(raw[:header_len])
            year = header.m_gameYear
            return 2000 + year if year < 100 else year
        except Exception:
            continue
    return 0


def extract_track_points(pcap_path: str, min_lap: int = 2) -> List[TrackPoint]:
    """Extract (lapDistance, worldX, worldZ) tuples from a pcap file.

    Args:
        pcap_path: Path to the .f1pcap file.
        min_lap: Minimum lap number to include (2 = skip formation lap).

    Returns:
        List of TrackPoint with on-track positions sorted by lap_distance.
    """
    pcap = F1PacketCapture(file_name=pcap_path)
    header_len = PacketHeader.PACKET_LEN
    total = pcap.getNumPackets()

    # Collect motion and lap data per frame
    motion_frames: Dict[int, List[Tuple[float, float]]] = {}
    lap_frames: Dict[int, "PacketLapData"] = {}

    for idx, (_, raw) in enumerate(pcap.getPackets()):
        if idx % 5000 == 0:
            print(f"\r  Parsing packet {idx}/{total}...", end="", flush=True)

        if len(raw) < header_len:
            continue

        try:
            header = PacketHeader(raw[:header_len])
        except Exception:
            continue

        payload = raw[header_len:]
        fid = header.m_frameIdentifier

        if header.m_packetId == F1PacketType.MOTION:
            try:
                pkt = PacketMotionData(header, payload)
            except Exception:
                continue
            motion_frames[fid] = [
                (c.m_worldPositionX, c.m_worldPositionZ)
                for c in pkt.m_carMotionData
            ]

        elif header.m_packetId == F1PacketType.LAP_DATA:
            try:
                pkt = PacketLapData(header, payload)
            except Exception:
                continue
            lap_frames[fid] = pkt

    print(f"\r  Parsed {total} packets: {len(motion_frames)} motion frames, "
          f"{len(lap_frames)} lap-data frames.")

    # Combine matching frames
    points: List[TrackPoint] = []
    for fid, motion in motion_frames.items():
        lap_pkt = lap_frames.get(fid)
        if lap_pkt is None:
            continue

        for car_idx, lap in enumerate(lap_pkt.m_lapData):
            if car_idx >= len(motion):
                break

            # Driver must be on track (not in garage)
            ds = lap.m_driverStatus
            ds_val = ds.value if hasattr(ds, "value") else int(ds)
            if ds_val == 0:
                continue

            # Not in pit lane
            if lap.m_pitLaneTimerActive:
                continue

            # Positive lap distance only
            if lap.m_lapDistance <= 0:
                continue

            # Skip formation lap
            if lap.m_currentLapNum < min_lap:
                continue

            wx, wz = motion[car_idx]
            # Skip zero/invalid coords
            if wx == 0.0 and wz == 0.0:
                continue

            points.append(TrackPoint(lap.m_lapDistance, wx, wz))

    print(f"  Collected {len(points)} valid track points.")
    return points


def bin_and_average(
    points: List[TrackPoint], num_bins: int = 800,
    track_length: Optional[float] = None,
) -> List[Tuple[float, float]]:
    """Bin points by lap distance and average world coordinates per bin.

    Returns:
        List of (world_x, world_z) tuples in lap-distance order.
    """
    if not points:
        return []

    max_dist = track_length if track_length else max(p.lap_distance for p in points)
    bin_size = max_dist / num_bins

    # Accumulate sums per bin: {bin_idx: (sum_x, sum_z, count)}
    bins: Dict[int, List[float]] = {}
    for p in points:
        b = min(int(p.lap_distance / bin_size), num_bins - 1)
        if b in bins:
            bins[b][0] += p.world_x
            bins[b][1] += p.world_z
            bins[b][2] += 1
        else:
            bins[b] = [p.world_x, p.world_z, 1]

    result = []
    for i in sorted(bins.keys()):
        sx, sz, c = bins[i]
        result.append((sx / c, sz / c))

    filled = len(result)
    coverage = filled / num_bins * 100
    print(f"  Binned into {filled}/{num_bins} bins ({coverage:.1f}% coverage).")
    return result


def rotate_points(
    points: List[Tuple[float, float]], degrees: float
) -> List[Tuple[float, float]]:
    """Rotate world points around their centroid by the given angle (degrees CCW)."""
    if not points or degrees % 360 == 0:
        return points

    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    # Rotate around centroid to keep track centered
    cx = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)

    rotated = []
    for x, z in points:
        dx, dz = x - cx, z - cz
        rx = dx * cos_a - dz * sin_a + cx
        rz = dx * sin_a + dz * cos_a + cz
        rotated.append((rx, rz))
    return rotated


def world_to_svg(
    points: List[Tuple[float, float]],
    width: int = 1000,
    height: int = 600,
    padding: int = 40,
    fill: bool = False,
) -> List[Tuple[float, float]]:
    """Transform world X/Z to SVG coordinates.

    Args:
        fill: If True, stretch independently on X/Y to fill the canvas
              (matches legacy MultiViewer SVG style). If False, preserve
              aspect ratio (geometrically correct).
    """
    if not points:
        return []

    xs = [p[0] for p in points]
    zs = [p[1] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)
    range_x = max_x - min_x or 1.0
    range_z = max_z - min_z or 1.0

    canvas_w = width - 2 * padding
    canvas_h = height - 2 * padding

    if fill:
        scale_x = canvas_w / range_x
        scale_y = canvas_h / range_z
        off_x = padding
        off_y = padding
    else:
        scale_x = scale_y = min(canvas_w / range_x, canvas_h / range_z)
        off_x = padding + (canvas_w - range_x * scale_x) / 2
        off_y = padding + (canvas_h - range_z * scale_y) / 2

    svg_points = []
    for wx, wz in points:
        sx = (wx - min_x) * scale_x + off_x
        sy = (max_z - wz) * scale_y + off_y  # Y-flip: world Z up → SVG Y down
        svg_points.append((round(sx, 3), round(sy, 3)))

    return svg_points


def write_svg(
    svg_points: List[Tuple[float, float]],
    output_path: str,
    width: int = 1000,
    height: int = 600,
) -> None:
    """Write SVG file in the project's standard polyline format."""
    if len(svg_points) < 2:
        print("Error: too few points for a polyline.", file=sys.stderr)
        sys.exit(1)

    # Close the loop only if endpoints are already close together.
    # A large gap means bins near the start/finish line have no data —
    # closing would create a long diagonal artefact.
    dx = svg_points[-1][0] - svg_points[0][0]
    dy = svg_points[-1][1] - svg_points[0][1]
    gap = (dx * dx + dy * dy) ** 0.5
    if gap < 30.0:
        svg_points.append(svg_points[0])

    coords = " ".join(f"{x},{y}" for x, y in svg_points)

    svg = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">\n'
        f'  <polyline points="{coords}" fill="none" stroke="white" stroke-width="4"\n'
        f'            stroke-linejoin="round" stroke-linecap="round"/>\n'
        f'</svg>\n'
    )

    Path(output_path).write_text(svg, encoding="utf-8")
    print(f"  Written: {output_path} ({len(svg_points)} points, {len(svg)} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SVG track maps from F1 pcap files."
    )
    parser.add_argument("pcap", help="Path to .f1pcap file")
    parser.add_argument("-o", "--output", help="Output SVG filename (written to track-maps/)")
    parser.add_argument(
        "--min-lap", type=int, default=2,
        help="Minimum lap number to include (default: 2, skips formation lap)"
    )
    parser.add_argument(
        "--bins", type=int, default=800,
        help="Number of distance bins for averaging (default: 800)"
    )
    parser.add_argument("--width", type=int, default=1000, help="SVG width (default: 1000)")
    parser.add_argument("--height", type=int, default=600, help="SVG height (default: 600)")
    parser.add_argument("--padding", type=int, default=40, help="SVG padding (default: 40)")
    parser.add_argument(
        "--fill", action="store_true",
        help="Stretch to fill canvas (non-uniform, matches old MultiViewer style)"
    )
    parser.add_argument(
        "--rotate", type=float, default=0,
        help="Rotate track CCW by degrees (e.g. 90 to fix rightward rotation)"
    )
    parser.add_argument(
        "--flip-x", action="store_true",
        help="Mirror track horizontally"
    )
    parser.add_argument(
        "--flip-y", action="store_true",
        help="Mirror track vertically"
    )
    parser.add_argument(
        "--track-length", type=float, default=None,
        help="Track length in metres (uses max lapDistance if omitted)"
    )
    parser.add_argument(
        "--dump-coords", action="store_true",
        help="Export raw binned world coordinates as JSON (before rotation/flip)"
    )

    args = parser.parse_args()

    pcap_path = args.pcap
    if not Path(pcap_path).exists():
        print(f"Error: file not found: {pcap_path}", file=sys.stderr)
        sys.exit(1)

    # Detect game year from pcap header
    game_year = extract_game_year(pcap_path)
    if game_year == 0:
        print("Error: could not detect game year from pcap.", file=sys.stderr)
        sys.exit(1)
    print(f"Detected game year: F1 {game_year}")

    # Output path: game-year-aware subfolder (e.g. assets/track-maps/f1_2025/)
    svg_dir = Path(__file__).resolve().parents[2] / "assets" / "track-maps" / f"f1_{game_year}"
    svg_dir.mkdir(parents=True, exist_ok=True)
    if args.output:
        output_path = str(svg_dir / args.output)
    else:
        output_path = str(svg_dir / f"{Path(pcap_path).stem}.svg")

    print(f"pcap:   {pcap_path}")
    print(f"output: {output_path}")
    print()

    print("[1/4] Extracting track points...")
    points = extract_track_points(pcap_path, min_lap=args.min_lap)
    if not points:
        print("Error: no valid track points found. Try --min-lap 1", file=sys.stderr)
        sys.exit(1)

    print(f"[2/4] Binning into {args.bins} segments...")
    avg_points = bin_and_average(points, num_bins=args.bins, track_length=args.track_length)

    if args.dump_coords:
        json_path = str(Path(output_path).with_suffix(".json"))
        data = {
            "track_name": Path(output_path).stem,
            "num_bins": args.bins,
            "points": [[round(x, 4), round(z, 4)] for x, z in avg_points],
        }
        Path(json_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"  Dumped {len(avg_points)} raw coords to {json_path}")

    if args.rotate:
        print(f"[2b]  Rotating {args.rotate}° CCW...")
        avg_points = rotate_points(avg_points, args.rotate)

    if args.flip_x or args.flip_y:
        cx = sum(p[0] for p in avg_points) / len(avg_points)
        cy = sum(p[1] for p in avg_points) / len(avg_points)
        flipped = []
        for x, y in avg_points:
            fx = 2 * cx - x if args.flip_x else x
            fy = 2 * cy - y if args.flip_y else y
            flipped.append((fx, fy))
        avg_points = flipped
        flags = []
        if args.flip_x: flags.append("X")
        if args.flip_y: flags.append("Y")
        print(f"[2c]  Flipped {'+'.join(flags)}")

    print("[3/4] Transforming to SVG coordinates...")
    svg_points = world_to_svg(avg_points, args.width, args.height, args.padding, args.fill)

    print("[4/4] Writing SVG...")
    write_svg(svg_points, output_path, args.width, args.height)

    print("\nDone.")


if __name__ == "__main__":
    main()
