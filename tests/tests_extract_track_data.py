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
# pylint: skip-file

import json
import os
import sys

import allure
import numpy as np
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.f1_types import TrackID
from apps.dev_tools import extract_track_data
from apps.dev_tools.extract_track_data import (FOLDER_ALIASES, FORMAT_VERSION,
                                               SOURCE_YEAR,
                                               OUT_DIR, build_geometry,
                                               circuit_for_folder,
                                               json_lengths, midpoint_length,
                                               parse_gates)

pytestmark = [allure.epic("Track data"), allure.feature("Geometry extractor")]


def _gate(name: str, x: float, z: float, left: float = 5.0, right: float = -5.0) -> dict:
    """A gate at (x, 0, z) with its normal along +x."""
    return {"name": name, "position": (x, 0.0, z), "normal": (1.0, 0.0, 0.0),
            "wp": {"left_white_line": left, "right_white_line": right}}


def _square_loop(side: float = 100.0, step: float = 10.0) -> list:
    """Gates around a square, all with +x normals (edges are only used for the length here)."""
    pts = []
    for i in range(int(side / step)):
        pts.append((i * step, 0.0))
    for i in range(int(side / step)):
        pts.append((side, i * step))
    for i in range(int(side / step)):
        pts.append((side - i * step, side))
    for i in range(int(side / step)):
        pts.append((0.0, side - i * step))
    return [_gate(f"ai_gate_{i}", x, z) for i, (x, z) in enumerate(pts)]


@allure.story("Layout lookup")
@allure.title("Every shipped circuit is a TrackID")
@allure.description("Each circuit_number in assets/track-segments has a TrackID member, so a game folder can map to it. "
                    "TrackID has more members than any one install (e.g. Portimao), which is fine.")
def test_shipped_circuits_are_track_ids():
    assert set(json_lengths()) <= set(TrackID.lowercase_names().values())


@allure.story("Layout lookup")
@allure.title("Folder alias {folder} points at a real TrackID name")
@allure.description("An alias that no longer names a TrackID member would silently skip that track.")
@pytest.mark.parametrize("folder", sorted(FOLDER_ALIASES))
def test_aliases_resolve(folder):
    assert circuit_for_folder(folder) is not None


@allure.story("Layout lookup")
@allure.title("Non-track folders do not resolve")
@allure.description("Folders like frontend are not tracks and are skipped.")
def test_non_track_folder_is_none():
    assert circuit_for_folder("frontend") is None


@allure.story("Gates")
@allure.title("Pit gates are dropped and gate order is kept")
@allure.description("build_geometry keeps only track gates, in file order.")
def test_build_geometry_drops_pit_gates():
    gates = _square_loop()
    gates.insert(3, _gate("ai_gate_pit_lane_1", 999.0, 999.0))
    edges, frac = build_geometry(gates)
    assert len(edges) == len(frac) == 40
    assert 999.0 not in edges


@allure.story("Lap fraction")
@allure.title("Lap fraction starts at 0, rises monotonically and stays below 1")
@allure.description("Gate 0 is the start/finish line, so frac[0] is 0 and the last gate is before the line.")
def test_lap_fraction_is_monotonic_in_zero_one():
    _, frac = build_geometry(_square_loop())
    assert frac[0] == 0.0
    assert np.all(np.diff(frac) > 0)
    assert frac[-1] < 1.0


@allure.story("Lap fraction")
@allure.title("Lap fraction follows the midpoint line, not gate positions")
@allure.description("Gates wide of the midpoint must not skew frac: with the midpoint offset, length is unchanged.")
def test_midpoint_length_of_square_loop():
    edges, _ = build_geometry(_square_loop(100.0, 10.0))
    assert midpoint_length(edges) == pytest.approx(400.0, rel=1e-4)


@allure.story("Gates")
@allure.title("Tokenizer reads gate name, position, normal and white-line lengths")
@allure.description("parse_gates recovers one gate from the BXML token stream.")
def test_parse_gates_reads_tokens():
    toks = ["gate", "id", "0", "name", "ai_gate_0",
            "position", "x", "1.5", "y", "2.5", "z", "3.5",
            "normal", "x", "1", "y", "0", "z", "0",
            "waypoint", "id", "7", "type", "left_white_line", "length", "4.25"]
    blob = b"".join(t.encode() + b"\x00" for t in toks)
    (g,) = parse_gates(blob)
    assert g["name"] == "ai_gate_0"
    assert g["position"] == (1.5, 2.5, 3.5)
    assert g["normal"] == (1.0, 0.0, 0.0)
    assert g["wp"] == {"left_white_line": 4.25}


@allure.story("Shipped files")
@allure.title("Geometry files on disk match the shipped circuits")
@allure.description("assets/track-data holds exactly one c<n>.npz per circuit in assets/track-segments: none missing, none extra.")
def test_geometry_files_match_layout_table():
    on_disk = {int(p.stem[1:]) for p in OUT_DIR.glob("c*.npz")}
    assert on_disk == set(json_lengths())


@allure.story("Shipped files")
@allure.title("Geometry file for circuit {circuit} is well formed")
@allure.description("Each file has edges (N, 6), frac (N,) of the same N, the current format version, the source game year, and frac in [0, 1).")
@pytest.mark.parametrize("circuit", sorted(json_lengths()))
def test_geometry_file_contents(circuit):
    with np.load(OUT_DIR / f"c{circuit}.npz") as f:
        edges, frac, version = f["edges"], f["frac"], int(f["version"])
        source_year = int(f["source_year"])
    assert version == FORMAT_VERSION
    assert source_year == SOURCE_YEAR
    assert edges.ndim == 2 and edges.shape[1] == 6
    assert len(frac) == len(edges)
    assert frac[0] == 0.0 and np.all(np.diff(frac) > 0) and frac[-1] < 1.0


@allure.story("Shipped files")
@allure.title("Partial extraction leaves other layouts alone, full run clears stale files")
@allure.description("Passing --layout writes only those files; a default run removes files that are not in the table.")
def test_output_dir_handling(tmp_path, monkeypatch):
    monkeypatch.setattr(extract_track_data, "OUT_DIR", tmp_path)
    monkeypatch.setattr(extract_track_data, "read_aispline", lambda _: b"")
    monkeypatch.setattr(extract_track_data, "parse_gates", lambda _: _square_loop())
    monkeypatch.setattr(extract_track_data, "game_layouts", lambda _: ["monza=11"])
    (tmp_path / "c99.npz").write_bytes(b"stale")
    monkeypatch.setattr("sys.argv", ["x", "--game-dir", str(tmp_path), "--layout", "melbourne=0"])
    extract_track_data.main()
    assert sorted(p.name for p in tmp_path.glob("*.npz")) == ["c0.npz", "c99.npz"]
    monkeypatch.setattr("sys.argv", ["x", "--game-dir", str(tmp_path)])
    extract_track_data.main()
    assert sorted(p.name for p in tmp_path.glob("*.npz")) == ["c11.npz"]
