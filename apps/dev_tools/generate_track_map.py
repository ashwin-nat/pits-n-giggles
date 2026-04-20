#!/usr/bin/env python3
"""generate_track_map.py — Dev tool to generate SVG track maps from live game data.

Listens on a UDP port for F1 telemetry, collects world coordinates from
Motion + LapData packets, and generates an SVG track map + JSON coordinate
dump once a full lap of data is recorded.

The generated files are placed into:
    assets/track-maps/f1_{game_year}/{TrackName}.svg
    assets/track-maps/f1_{game_year}/{TrackName}.json

After generation, run regenerate_svgs.py on the game folder to recompute
the svg_transforms.json with the correct affine coefficients.

Usage:
    python -m apps.dev_tools.generate_track_map                 # default port 20777
    python -m apps.dev_tools.generate_track_map --port 20778    # custom port
    python -m apps.dev_tools.generate_track_map --game-year 2024  # override game year

Workflow:
    1. Start this tool
    2. Start the F1 game, load a track
    3. Drive at least one full lap (formation lap is skipped)
    4. SVG is generated automatically, tool exits
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# pylint: disable=wrong-import-position
from lib.f1_types import F1PacketType
from lib.track_map_generator import TrackMapCollector
from lib.telemetry_manager import AsyncF1TelemetryManager
# pylint: enable=wrong-import-position


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("generate_track_map")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    return logger


async def run(port: int, game_year_override: int | None, logger: logging.Logger) -> None:
    track_maps_dir = Path(__file__).resolve().parents[2] / "assets" / "track-maps"
    collector = TrackMapCollector(target_dir=track_maps_dir, logger=logger)

    manager = AsyncF1TelemetryManager(port_number=port, logger=logger)

    generated_count = 0
    detected_game_year: int | None = None

    @manager.on_packet(F1PacketType.SESSION)
    async def on_session(packet) -> None:
        nonlocal detected_game_year
        if packet.m_trackId is not None and packet.m_trackLength:
            game_year = game_year_override or packet.m_header.m_packetFormat
            detected_game_year = game_year
            collector.set_track(packet.m_trackId.name, packet.m_trackLength, game_year)

    @manager.on_packet(F1PacketType.MOTION)
    async def on_motion(packet) -> None:
        collector.on_motion(packet.m_carMotionData)

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def on_lap(packet) -> None:
        nonlocal generated_count
        collector.on_lap_data(packet.m_lapData)
        result = collector.generate_if_ready()
        if result:
            generated_count += 1
            logger.info("Track map generated: %s", result)
            logger.info("(%d track(s) done — load next track or Ctrl+C to stop)", generated_count)

    logger.info("Listening on UDP port %d — start the game and drive a lap...", port)
    if game_year_override:
        logger.info("Game year override: F1 %d", game_year_override)

    try:
        await manager.run()
    except KeyboardInterrupt:
        pass

    if generated_count:
        logger.info("%d track map(s) generated.", generated_count)
    else:
        logger.warning("Tool stopped before a track map could be generated.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SVG track maps from live F1 telemetry data."
    )
    parser.add_argument("--port", type=int, default=20777, help="UDP port (default: 20777)")
    parser.add_argument(
        "--game-year", type=int, default=None,
        help="Override game year (e.g. 2024). Auto-detected from UDP header if omitted."
    )
    args = parser.parse_args()

    logger = _setup_logger()

    try:
        asyncio.run(run(args.port, args.game_year, logger))
    except KeyboardInterrupt:
        logger.info("Stopped.")


if __name__ == "__main__":
    main()
