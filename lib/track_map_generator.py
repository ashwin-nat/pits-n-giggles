"""track_map_generator.py — Live SVG track map generation from telemetry data.

Collects world coordinates (PacketMotionData) paired with lap distance
(PacketLapData) during a session. After a full lap is recorded, generates
an SVG polyline matching the game's internal track geometry.

Integration:
    Instantiate in TelemetryHandler, feed via on_motion() and on_lap_data(),
    call generate_if_ready() periodically.
"""

import json
import math
from logging import Logger
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# SVG output constants
_SVG_WIDTH = 1000
_SVG_HEIGHT = 600
_SVG_PADDING = 40
_NUM_BINS = 800

# Game world coords need 90° CCW rotation + horizontal flip
# to match expected track map orientation (confirmed with Bahrain live data).
_ROTATE_DEG = 90.0
_FLIP_X = True


class TrackMapCollector:
    """Collects track geometry points during a live session."""

    __slots__ = (
        "_points",       # list of (lap_distance, world_x, world_z)
        "_track_name",   # TrackID.name for the SVG filename
        "_track_len",    # track length in metres
        "_game_year",    # packet format year (2023, 2024, 2025) for subfolder
        "_generated",    # True once SVG was written for this session
        "_target_dir",   # Path to assets/track-maps/
        "_logger",
        "_last_motion",  # per-car (worldX, worldZ) from most recent motion packet
        "_min_lap",      # minimum lap number to collect (skip formation lap)
    )

    def __init__(self, target_dir: Path, logger: Logger, min_lap: int = 2) -> None:
        self._target_dir = target_dir
        self._logger = logger
        self._min_lap = min_lap
        self.reset()

    def reset(self) -> None:
        """Reset collector for a new session."""
        self._points: List[Tuple[float, float, float]] = []
        self._track_name: Optional[str] = None
        self._track_len: Optional[float] = None
        self._game_year: Optional[int] = None
        self._generated = False
        self._last_motion: List[Tuple[float, float]] = []

    @property
    def is_generated(self) -> bool:
        return self._generated

    def set_track(self, track_name: str, track_length: float, game_year: int) -> None:
        """Set the current track identity. Called when session data arrives."""
        if self._track_name != track_name or self._game_year != game_year:
            self._logger.info("TrackMapCollector: track set to %s (%.0fm, F1 %d)", track_name, track_length, game_year)
            self.reset()
            self._track_name = track_name
            self._track_len = track_length
            self._game_year = game_year

    def on_motion(self, car_motion_data: list) -> None:
        """Buffer world positions from a PacketMotionData.

        Args:
            car_motion_data: list of CarMotionData objects (22 cars).
        """
        self._last_motion = [
            (c.m_worldPositionX, c.m_worldPositionZ) for c in car_motion_data
        ]

    def on_lap_data(self, lap_data_list: list) -> None:
        """Pair buffered motion data with lap distances from PacketLapData.

        Args:
            lap_data_list: list of LapData objects (22 cars).
        """
        if self._generated or not self._last_motion or not self._track_name:
            return

        for car_idx, lap in enumerate(lap_data_list):
            if car_idx >= len(self._last_motion):
                break
            self._try_add_point(car_idx, lap)

    def _try_add_point(self, car_idx: int, lap) -> None:
        """Try to add a single car's position to the collection."""
        # Driver must be actively on track
        ds = lap.m_driverStatus
        ds_val = ds.value if hasattr(ds, "value") else int(ds)
        if ds_val == 0:  # in garage
            return
        if lap.m_pitLaneTimerActive:
            return
        if lap.m_lapDistance <= 0:
            return
        if lap.m_currentLapNum < self._min_lap:
            return

        wx, wz = self._last_motion[car_idx]
        if abs(wx) < 1e-6 and abs(wz) < 1e-6:
            return

        self._points.append((lap.m_lapDistance, wx, wz))

    def generate_if_ready(self) -> Optional[str]:
        """Check if enough data is collected and generate SVG if so.

        Returns:
            The SVG file path if generated, None otherwise.
        """
        if self._generated or not self._track_name or not self._track_len:
            return None

        # Need 100% bin coverage before generating.
        if len(self._points) < _NUM_BINS:
            return None

        # Check bin coverage
        bin_size = self._track_len / _NUM_BINS
        filled_bins = set()
        for dist, _, _ in self._points:
            b = min(int(dist / bin_size), _NUM_BINS - 1)
            filled_bins.add(b)

        coverage = len(filled_bins) / _NUM_BINS
        if coverage < 1.0:
            return None

        # Generate
        self._logger.info(
            "TrackMapCollector: generating SVG for %s (%d points, %.0f%% coverage)",
            self._track_name, len(self._points), coverage * 100
        )

        avg_points = _bin_and_average(self._points, _NUM_BINS, self._track_len)

        # Output directory: assets/track-maps/f1_{game_year}/
        game_dir = self._target_dir / f"f1_{self._game_year}"
        game_dir.mkdir(parents=True, exist_ok=True)

        # Dump raw coords (pre-rotation) for calibration
        json_path = game_dir / f"{self._track_name}.json"
        data = {
            "track_name": self._track_name,
            "game_year": self._game_year,
            "num_bins": _NUM_BINS,
            "points": [[round(x, 4), round(z, 4)] for x, z in avg_points],
        }
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._logger.info("TrackMapCollector: wrote %s (%d raw coords)", json_path, len(avg_points))

        avg_points = _rotate_points(avg_points, _ROTATE_DEG)
        if _FLIP_X:
            avg_points = _flip_x(avg_points)
        svg_points = _world_to_svg(avg_points, _SVG_WIDTH, _SVG_HEIGHT, _SVG_PADDING)

        svg_filename = f"{self._track_name}.svg"
        output_path = game_dir / svg_filename
        _write_svg(svg_points, str(output_path), _SVG_WIDTH, _SVG_HEIGHT)

        self._generated = True
        self._logger.info("TrackMapCollector: wrote %s (%d points)", output_path, len(svg_points))
        return str(output_path)


# ---------------------------------------------------------------------------
# Core geometry functions (shared logic with pcap_to_svg.py)
# ---------------------------------------------------------------------------

def _bin_and_average(
    points: List[Tuple[float, float, float]], num_bins: int,
    track_length: Optional[float] = None,
) -> List[Tuple[float, float]]:
    """Bin (lapDist, x, z) triples by distance and average world coords per bin."""
    if not points:
        return []

    max_dist = track_length if track_length else max(p[0] for p in points)
    bin_size = max_dist / num_bins

    bins: Dict[int, List[float]] = {}
    for dist, wx, wz in points:
        b = min(int(dist / bin_size), num_bins - 1)
        if b in bins:
            bins[b][0] += wx
            bins[b][1] += wz
            bins[b][2] += 1
        else:
            bins[b] = [wx, wz, 1]

    return [(sx / c, sz / c) for _, (sx, sz, c) in sorted(bins.items())]


def _rotate_points(
    points: List[Tuple[float, float]], degrees: float
) -> List[Tuple[float, float]]:
    """Rotate world points around their centroid by degrees CCW."""
    if not points or degrees % 360 == 0:
        return points

    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    cx = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)

    return [
        (
            (x - cx) * cos_a - (z - cz) * sin_a + cx,
            (x - cx) * sin_a + (z - cz) * cos_a + cz,
        )
        for x, z in points
    ]


def _flip_x(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Mirror points horizontally around centroid."""
    if not points:
        return points
    cx = sum(p[0] for p in points) / len(points)
    return [(2 * cx - x, z) for x, z in points]


def _world_to_svg(
    points: List[Tuple[float, float]],
    width: int, height: int, padding: int,
) -> List[Tuple[float, float]]:
    """Transform world X/Z to SVG coordinates preserving aspect ratio."""
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
    scale = min(canvas_w / range_x, canvas_h / range_z)
    off_x = padding + (canvas_w - range_x * scale) / 2
    off_y = padding + (canvas_h - range_z * scale) / 2

    return [
        (round((wx - min_x) * scale + off_x, 3),
         round((max_z - wz) * scale + off_y, 3))
        for wx, wz in points
    ]


def _write_svg(
    svg_points: List[Tuple[float, float]],
    output_path: str,
    width: int, height: int,
) -> None:
    """Write SVG file in the project's standard polyline format."""
    # Close the loop only if endpoints are already close together.
    # A large gap means bins near the start/finish line have no data —
    # closing would create a long diagonal artefact.
    if len(svg_points) >= 2:
        dx = svg_points[-1][0] - svg_points[0][0]
        dy = svg_points[-1][1] - svg_points[0][1]
        if (dx * dx + dy * dy) ** 0.5 < 30.0:
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
