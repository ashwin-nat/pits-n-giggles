#!/usr/bin/env python3
"""regenerate_svgs.py — Regenerate SVG track maps from JSON world coordinates.

Reads the JSON files (containing binned world X/Z points), applies
per-track rotation/flip adjustments, generates SVG polylines, and
recomputes the affine transforms (world→SVG pixel mapping) for all tracks.

Usage:
    python assets/track-maps/regenerate_svgs.py          # regenerate all
    python assets/track-maps/regenerate_svgs.py --dry-run # preview only
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ── Per-track display adjustments ────────────────────────────────────
# rotate_deg: CCW rotation in degrees (applied to world coords before SVG gen)
# flip_x: mirror horizontally (negate X after rotation)
# flip_y: mirror vertically (negate Z after rotation)
#
# Tracks not listed here get no adjustment (0° rotation, no flip).
# Adjust these values so each track matches the canonical F1 broadcast view.
TRACK_ADJUSTMENTS: Dict[str, dict] = {
    # Example: "Singapore": {"rotate_deg": -90, "flip_x": True},
}

# SVG generation parameters (must match the original generation)
SVG_WIDTH   = 1000
SVG_HEIGHT  = 600
SVG_PADDING = 40


def rotate_points(
    points: List[Tuple[float, float]], degrees: float
) -> List[Tuple[float, float]]:
    """Rotate points around their centroid by the given angle (degrees CCW)."""
    if not points or degrees % 360 == 0:
        return list(points)

    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    cx = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)

    rotated = []
    for x, z in points:
        dx, dz = x - cx, z - cz
        rx = dx * cos_a - dz * sin_a + cx
        rz = dx * sin_a + dz * cos_a + cz
        rotated.append((rx, rz))
    return rotated


def flip_points(
    points: List[Tuple[float, float]], flip_x: bool, flip_y: bool
) -> List[Tuple[float, float]]:
    """Mirror points around their centroid."""
    if not flip_x and not flip_y:
        return list(points)

    cx = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)

    result = []
    for x, z in points:
        fx = cx - (x - cx) if flip_x else x
        fz = cz - (z - cz) if flip_y else z
        result.append((fx, fz))
    return result


def world_to_svg(
    points: List[Tuple[float, float]],
    width: int = SVG_WIDTH,
    height: int = SVG_HEIGHT,
    padding: int = SVG_PADDING,
) -> List[Tuple[float, float]]:
    """Transform world X/Z to SVG pixel coordinates (aspect-ratio preserving)."""
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)
    range_x = max_x - min_x or 1.0
    range_z = max_z - min_z or 1.0

    canvas_w = width - 2 * padding
    canvas_h = height - 2 * padding

    scale = min(canvas_w / range_x, canvas_h / range_z)
    off_x = padding + (canvas_w - range_x * scale) / 2
    off_y = padding + (canvas_h - range_z * scale) / 2

    svg_points = []
    for wx, wz in points:
        sx = (wx - min_x) * scale + off_x
        sy = (max_z - wz) * scale + off_y  # Y-flip: world Z up → SVG Y down
        svg_points.append((round(sx, 3), round(sy, 3)))
    return svg_points


def write_svg(
    svg_points: List[Tuple[float, float]],
    output_path: Path,
    width: int = SVG_WIDTH,
    height: int = SVG_HEIGHT,
) -> None:
    """Write SVG file with the standard polyline format."""
    # Close the loop if endpoints are close
    dx = svg_points[-1][0] - svg_points[0][0]
    dy = svg_points[-1][1] - svg_points[0][1]
    gap = (dx * dx + dy * dy) ** 0.5
    pts = list(svg_points)
    if gap < 30.0:
        pts.append(pts[0])

    coords = " ".join(f"{x},{y}" for x, y in pts)
    svg = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">\n'
        f'  <polyline points="{coords}" fill="none" stroke="white" stroke-width="4"\n'
        f'            stroke-linejoin="round" stroke-linecap="round"/>\n'
        f'</svg>\n'
    )
    output_path.write_text(svg, encoding="utf-8")


def compute_affine(
    world_pts: np.ndarray, svg_pts: np.ndarray
) -> Tuple[dict, float, float]:
    """Compute 6 affine coefficients mapping world→SVG pixels.

    Returns (params_dict, avg_error, max_error).
    """
    N = min(len(world_pts), len(svg_pts))
    w = world_pts[:N]
    s = svg_pts[:N]

    ones = np.ones((N, 1))
    W = np.hstack([w, ones])  # [wx, wz, 1]

    px, _, _, _ = np.linalg.lstsq(W, s[:, 0], rcond=None)
    py, _, _, _ = np.linalg.lstsq(W, s[:, 1], rcond=None)

    predicted = W @ np.column_stack([px, py])
    errors = np.sqrt(np.sum((predicted - s) ** 2, axis=1))

    params = {
        "svg_width": SVG_WIDTH,
        "svg_height": SVG_HEIGHT,
        "a": round(float(px[0]), 6),
        "b": round(float(px[1]), 6),
        "c": round(float(px[2]), 3),
        "d": round(float(py[0]), 6),
        "e": round(float(py[1]), 6),
        "f": round(float(py[2]), 3),
        "avg_error_px": round(float(errors.mean()), 3),
        "max_error_px": round(float(errors.max()), 3),
    }
    return params, float(errors.mean()), float(errors.max())


def main():
    parser = argparse.ArgumentParser(description="Regenerate SVG track maps from JSON data.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument(
        "game_folder", nargs="?", default=None,
        help="Game folder to process (e.g. f1_2025). If omitted, processes all f1_* folders."
    )
    args = parser.parse_args()

    track_maps_root = Path(__file__).resolve().parents[2] / "assets" / "track-maps"

    # Find game folders to process
    if args.game_folder:
        game_dirs = [track_maps_root / args.game_folder]
        if not game_dirs[0].is_dir():
            print(f"Error: folder {game_dirs[0]} does not exist.", file=sys.stderr)
            sys.exit(1)
    else:
        game_dirs = sorted(d for d in track_maps_root.iterdir() if d.is_dir() and d.name.startswith("f1_"))

    if not game_dirs:
        print("No f1_* game folders found.", file=sys.stderr)
        sys.exit(1)

    total_regenerated = 0

    for game_dir in game_dirs:
        print(f"\n{'='*60}")
        print(f"  {game_dir.name}")
        print(f"{'='*60}")

        json_files = sorted(game_dir.glob("*.json"))
        # Exclude meta JSONs
        json_files = [f for f in json_files if f.stem not in (
            "track_transforms", "svg_transforms",
        )]

        if not json_files:
            print("  No track JSON files found, skipping.")
            continue

        all_transforms = {}
        regenerated = 0

        for json_path in json_files:
            name = json_path.stem
            svg_path = game_dir / f"{name}.svg"

            # Load world coordinates
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            raw_points = [tuple(p) for p in data["points"]]

            # Apply per-track adjustments
            adj = TRACK_ADJUSTMENTS.get(name, {})
            rot = adj.get("rotate_deg", 0)
            fx = adj.get("flip_x", False)
            fy = adj.get("flip_y", False)
            has_adjustment = rot != 0 or fx or fy

            display_points = raw_points
            if rot:
                display_points = rotate_points(display_points, rot)
            if fx or fy:
                display_points = flip_points(display_points, fx, fy)

            adj_info = " ".join(filter(None, [f"rot={rot}°" if rot else "", "flip_x" if fx else "", "flip_y" if fy else ""]))

            # Generate SVG pixel coordinates
            svg_pixel_pts = world_to_svg(display_points)

            if has_adjustment or not svg_path.exists():
                if args.dry_run:
                    action = "WOULD REGENERATE" if svg_path.exists() else "WOULD CREATE"
                    print(f"  {action} {name}.svg  ({adj_info})")
                else:
                    write_svg(svg_pixel_pts, svg_path)
                    regenerated += 1
                    print(f"  REGEN {name}.svg  ({adj_info or 'no adjustment'})")
            else:
                # SVG exists without adjustment — read existing pixel coords for affine fit
                # (avoids re-computing world→SVG mapping and drifting from the on-disk SVG)
                m = re.search(r'points="([^"]+)"', svg_path.read_text())
                if m:
                    pairs = m.group(1).strip().split()
                    svg_pixel_pts = [
                        tuple(float(v) for v in p.split(",")) for p in pairs[:len(raw_points)]
                    ]
                print(f"  KEEP  {name}.svg  (unchanged)")

            # Compute affine: raw world coords → SVG pixel coords
            world_arr = np.array(raw_points[:len(svg_pixel_pts)])
            svg_arr = np.array(svg_pixel_pts[:len(raw_points)])
            params, _, max_err = compute_affine(world_arr, svg_arr)

            if has_adjustment:
                params["rotate_deg"] = rot
                if fx: params["flip_x"] = True
                if fy: params["flip_y"] = True

            all_transforms[name] = params

            if max_err > 1.0:
                print(f"    WARNING: max error {max_err:.3f}px for {name}")

        # Write svg_transforms.json per game folder
        out_path = game_dir / "svg_transforms.json"
        if not args.dry_run:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_transforms, f, indent=2)
            print(f"\n  Saved {len(all_transforms)} transforms to {out_path}")
            print(f"  Regenerated {regenerated} SVG(s)")
        else:
            print(f"\n  Dry run: would save {len(all_transforms)} transforms")

        total_regenerated += regenerated

        # Summary per folder
        adjusted = [n for n in all_transforms if TRACK_ADJUSTMENTS.get(n)]
        if adjusted:
            print(f"  Tracks with display adjustments: {', '.join(adjusted)}")

    print(f"\nTotal SVGs regenerated across all game folders: {total_regenerated}")


if __name__ == "__main__":
    main()
