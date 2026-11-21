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


# -------------------------------------- SEGMENT DATA (zones, corners, brake boards) -----------------------------------

import struct

from lib.track_segments_classifier import (BrakeBoardInfo, ComplexCornerSegmentInfo, CornerSegmentInfo,
                                           StraightSegmentInfo, SubCornerInfo)
from lib.track_segments_classifier.classifier import TrackSegmentsClassifier

from apps.dev_tools.extract_track_data import (attach_boards, board_objects, corner_report, extract_zones,
                                               game_corners, group_boards, knot_mapper, parse_bxml,
                                               parse_maintrack_knots, seed_sub_corners, update_segment_file)


def _el(tag: str, attrs: dict = None, *children: bytes, text: str = "") -> bytes:
    """One BXML element: header, name and attributes, optional text node, children, end marker."""
    attrs = attrs or {}
    body = tag.encode() + b"\0" + b"".join(k.encode() + b"\0" + v.encode() + b"\0" for k, v in attrs.items())
    out = struct.pack("<HBBH", 4 + len(body), 0, 0, len(attrs)) + body
    if text:
        out += struct.pack("<HBBH", 4 + len(text) + 1, 1, 0, 0) + text.encode() + b"\0"
    return out + b"".join(children) + struct.pack("<HBBH", 4, 5, 0, 0)


def _bxml(root: bytes) -> bytes:
    return b"\x01BXML" + root


def _markup(*elements: tuple) -> bytes:
    """A .trackmarkup with (name, start, end, spline, attribute type, {property: value}) elements."""
    items = []
    for name, start, end, spline, kind, props in elements:
        properties = _el("Properties", None, *[_el("Property", {"Type": k, "Value": v}) for k, v in props.items()])
        attribute = _el("Attribute", {"Type": kind}, properties)
        items.append(_el("MarkupElement", {"Name": name, "Start": str(start), "End": str(end), "SplineName": spline},
                         _el("Attributes", None, attribute)))
    return _bxml(_el("TrackspaceMarkup", {"Version": "ts_data_v3.002"}, _el("MarkupList", None, *items)))


# Knots 10, 90, 100, 100, 100 m apart: uneven on purpose, so a plain lap fraction would be wrong
_KNOTS = np.array([[0.0, 0.0], [10.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
_SQUARE = np.array([[0.0, 0.0], [1000.0, 0.0], [1000.0, 1000.0], [0.0, 1000.0]])


def _pkg(instances: list) -> bytes:
    """A minimal !pkg layer. `instances` is [(name, 16-float matrix, [refs])]."""
    strings, sdata = {}, bytearray()

    def string(text: str) -> int:
        if text not in strings:
            strings[text] = len(sdata)
            sdata.append(len(text.encode()))
            sdata.extend(text.encode())
        return strings[text]

    for key in ("instances", "name", "transform", "refs"):
        string(key)
    for name, _, refs in instances:
        string(name)
        for ref in refs:
            string(ref)
    mats = b"".join(struct.pack("<16f", *m) for _, m, _ in instances)
    out = bytearray(b"!pkg" + bytes(4) + bytes(4))
    vca = len(out)
    out += b"!vca" + struct.pack("<I", 2) + bytes(8)
    sbi = len(out)
    out += b"!sbi" + bytes(4) + sdata
    mat4 = len(out)
    out += b"!arr" + b"mat4" + struct.pack("<II", len(instances), 64) + mats
    struct.pack_into("<II", out, vca + 8, sbi, mat4)

    def put(blob: bytes) -> int:
        offset = len(out)
        out.extend(blob)
        return (0x80 << 24) | offset

    def dict_obj(entries: list) -> int:
        return put(b"!idi" + struct.pack("<I", len(entries)) + b"".join(struct.pack("<III", k, v, 0) for k, v in entries))

    def list_obj(values: list) -> int:
        return put(b"!ili" + struct.pack("<I", len(values)) + b"".join(struct.pack("<I", v) for v in values))

    insts = []
    for i, (name, _, refs) in enumerate(instances):
        ref_list = list_obj([string(r) for r in refs])
        insts.append(dict_obj([(string("name"), string(name)), (string("transform"), (1 << 24) | i),
                               (string("refs"), ref_list)]))
    root = dict_obj([(string("instances"), list_obj(insts))])
    struct.pack_into("<I", out, 8, root & 0xFFFFFF)
    return bytes(out)


def _matrix(x: float, z: float) -> tuple:
    return (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, 0.0, z, 1)


@allure.story("BXML parser")
@allure.title("parse_bxml builds the tree with attributes, text and children")
def test_parse_bxml_tree():
    """A root with an attribute, a text child and two nested elements.

    Expected: tags, attributes, text and child order all survive."""
    root = parse_bxml(_bxml(_el("Root", {"Version": "1"}, _el("Corner", None, text="7"), _el("Other", {"a": "b"}))))
    assert (root.tag, root.attrs) == ("Root", {"Version": "1"})
    assert [c.tag for c in root.children] == ["Corner", "Other"]
    assert root.find("Corner").text == "7"
    assert root.find("Other").attrs == {"a": "b"}
    assert root.find("Missing") is None


@allure.story("BXML parser")
@allure.title("parse_bxml ignores a stray node after the root")
def test_parse_bxml_ignores_trailing_node():
    """Game blobs end with a node outside the root.

    Expected: the first element stays the root."""
    root = parse_bxml(_bxml(_el("Root") + _el("Stray")))
    assert root.tag == "Root"


@allure.story("BXML parser")
@allure.title("parse_bxml rejects a blob without the BXML header")
def test_parse_bxml_rejects_other_data():
    with pytest.raises(AssertionError):
        parse_bxml(b"not bxml")


@allure.story("Lap distance mapping")
@allure.title("Knots are mapped by index, not by plain lap fraction")
@pytest.mark.parametrize("frac, expected", [(0.0, 0), (0.2, 100), (0.4, 1000), (0.8, 3000), (1.2, 100), (-0.8, 100)])
def test_knot_mapper_uneven_knots(frac, expected):
    """Five knots 10, 90, 100, 100 and 100 m apart on a 4000 m lap.

    Expected: fraction 0.4 is knot 2, at 1000 m (a plain fraction gives 1600), 0.8 is knot 4, and fractions wrap."""
    assert knot_mapper(_KNOTS, 4000)(frac) == expected


@allure.story("Lap distance mapping")
@allure.title("Knots are read from the maintrack spline only")
def test_parse_maintrack_knots_stops_at_next_spline():
    """A spline blob with knots for maintrack and for another spline after it.

    Expected: only maintrack's knots, as (x, z) pairs."""
    def knot(x, y, z):
        return b"Knot\0position\0" + f"{x},{y},{z}".encode() + b"\0"

    blob = b"x\0maintrack\0" + knot(1, 9, 2) + knot(3, 9, 4) + b"TrackSpaceSpline\0" + knot(5, 9, 6)
    assert parse_maintrack_knots(blob).tolist() == [[1.0, 2.0], [3.0, 4.0]]


@allure.story("Zones")
@allure.title("Markup becomes speed trap, DRS, overtake and active aero zones")
def test_extract_zones():
    """A markup with a speed trap, one DRS zone with two activations, an overtake zone, two aero zones
    (one crossing the line) and a pit-spline aero zone, on a 4000 m lap.

    Expected: pit-spline elements are ignored, activations sorted, aero sorted by mode and start."""
    props = lambda **kw: {k: str(v) for k, v in kw.items()}
    markup = _parse(_markup(
        ("speed_trap", 0.2, 0.25, "maintrack", "spd_trp", {}),
        ("drs_detection_1", 0.4, 0.41, "maintrack", "drs_det", props(ID=1)),
        ("drs_activation_1b", 0.8, 0.9, "maintrack", "drs_act", props(ID=1)),
        ("drs_activation_1a", 0.2, 0.4, "maintrack", "drs_act", props(ID=1)),
        ("ers_override_detection_1", 0.4, 0.41, "maintrack", "ers_over_det", props(ID=1)),
        ("ers_override_activation_1", 0.2, 0.25, "maintrack", "ers_over_act", props(ID=1)),
        ("x_mode_2", 0.8, 0.2, "maintrack", "x_mode", props(ID=2, type="Partial")),
        ("x_mode_1", 0.2, 0.4, "maintrack", "x_mode", props(ID=1, type="Full")),
        ("x_mode_1_pit", 0.5, 0.6, "pit_1", "x_mode", props(ID=1, type="Full")),
    ))
    zones = extract_zones(markup, knot_mapper(_KNOTS, 4000))
    assert zones == {
        "speed_trap_m": 100,
        "drs_zones": [{"id": 1, "detection_m": 1000,
                       "activation": [{"start_m": 100, "end_m": 1000}, {"start_m": 3000, "end_m": 3500}]}],
        "overtake_zones": [{"id": 1, "detection_m": 1000, "activation_m": 100}],
        "active_aero_zones": [{"mode": "full", "start_m": 100, "end_m": 1000},
                              {"mode": "partial", "start_m": 3000, "end_m": 100}],
    }


@allure.story("Zones")
@allure.title("A zone missing its detection or activation point is dropped")
def test_extract_zones_drops_incomplete_zones():
    """A DRS zone with activation but no detection, and an overtake zone with detection but no activation.

    Expected: neither is written, since the schema requires both points. No speed trap gives no key."""
    markup = _parse(_markup(
        ("drs_activation_1", 0.2, 0.4, "maintrack", "drs_act", {"ID": "1"}),
        ("ers_override_detection_1", 0.4, 0.41, "maintrack", "ers_over_det", {"ID": "1"}),
    ))
    assert extract_zones(markup, knot_mapper(_KNOTS, 4000)) == {
        "drs_zones": [], "overtake_zones": [], "active_aero_zones": []}


def _parse(blob: bytes):
    return parse_bxml(blob)


@allure.story("Brake boards")
@allure.title("Board distance is read from {source}")
@pytest.mark.parametrize("source, name, refs, expected", [
    ("the sponsor material context", "dynamic_sponsor_brake_a",
     ["x.emb?context=sp_150_white_sp_aramco&v=1"], 150),
    ("the object name", "mza_brakeboard_left_200_a002", [], 200),
    ("a pole name", "spa_dressing_brakemarker_pole100_l", [], 100),
    ("nothing, for an unnumbered sponsor sign", "dynamic_sponsor_brake_c", ["x.emb?context=sp_drs_white&v=1"], None),
])
def test_board_objects_distance(source, name, refs, expected):
    """One brake object in a synthetic !pkg layer at world (12, 34).

    Expected: the labelled distance from the right place, None where it cannot be resolved, and the
    object's x and z."""
    (obj,) = board_objects(_pkg([(f"layer$tree${name}", _matrix(12.0, 34.0), refs)]))
    assert (obj["name"], obj["dist"], obj["x"], obj["z"]) == (f"{name}", expected, 12.0, 34.0)


@allure.story("Brake boards")
@allure.title("Layers without brake objects, and non-brake instances, give no boards")
def test_board_objects_ignores_other_objects():
    """A layer with a tree and a layer with no 'brake' text at all.

    Expected: no boards from either."""
    assert board_objects(_pkg([("layer$tree_a", _matrix(0, 0), [])])) == []
    assert board_objects(b"no markers in here") == []


def _obj(x, z, dist, name="b"):
    return {"name": name, "dist": dist, "x": x, "z": z}


@allure.story("Brake boards")
@allure.title("Boards are projected onto the lap and left and right boards merge")
def test_group_boards():
    """Boards along the first side of a 4000 m square: a 100 m pair on both sides, a 50 m board on one side,
    a duplicate position, a 75 m board (not a schema distance), an unresolved one and one 50 m off the road.

    Expected: a `both` entry and a `right` entry, sorted by lap distance, and nothing else."""
    objects = [_obj(100, 5, 100), _obj(100, -5, 100), _obj(150, 5, 50), _obj(150, 5, 50),
               _obj(200, 5, 75), _obj(250, 5, None), _obj(300, 50, 50)]
    assert group_boards(objects, _SQUARE, 4000) == [
        {"distance_m": 100, "at_m": 100.0, "side": "both"},
        {"distance_m": 50, "at_m": 150.0, "side": "right"},
    ]


def _board(at, dist=100):
    return BrakeBoardInfo(distance_m=dist, at_m=at, side="both")


def _layout():
    return (
        CornerSegmentInfo(name="One", start_m=100, end_m=200, corner_number=1,
                          brake_boards=(_board(99),)),
        ComplexCornerSegmentInfo(start_m=1000, end_m=1200, corner_numbers=(2, 3), corners=(
            SubCornerInfo(corner_number=2, start_m=1000, end_m=1100),
            SubCornerInfo(corner_number=3, start_m=1100, end_m=1200))),
        StraightSegmentInfo(name="Back", start_m=1200, end_m=2000),
    )


@allure.story("Brake boards")
@allure.title("Boards attach to the corner they warn about")
def test_attach_boards():
    """Three boards on a 2000 m lap: one just before the line (wraps to corner 1), one before the complex
    corner, and one 700 m before it. Corner 1 held an old board.

    Expected: the old board is replaced, the first two land on corner 1 and sub-corner 2, the far one
    on sub-corner 2 with a note."""
    segments, notes = attach_boards(_layout(), [_board(1950), _board(300), _board(900)], 2000)
    corner, complex_corner, _ = segments
    assert [b.at_m for b in corner.brake_boards] == [1950]
    assert [b.at_m for b in complex_corner.corners[0].brake_boards] == [300, 900]
    assert complex_corner.corners[1].brake_boards == ()
    assert len(notes) == 1 and "300" in notes[0]


@allure.story("Brake boards")
@allure.title("Replacing boards revalidates the segments")
def test_attach_boards_rejects_a_board_outside_the_lap_later():
    """A board beyond track_length passes attach_boards, which only places it.

    Expected: the classifier refuses the track, so such a file is never written."""
    segments, _ = attach_boards(_layout(), [_board(2500)], 2000)
    with pytest.raises(ValueError, match="must be in"):
        TrackSegmentsClassifier(circuit_name="t", circuit_number=1, track_length=2000, sectors={"s1": 600, "s2": 1300},
                                segments=segments, use_cache=False, schema_version=2)


@allure.story("Corners")
@allure.title("Game corners come from the taprogram of the source year")
def test_game_corners():
    """A taprogram with two corners for the current year, one with a messy number, and one for another year.

    Expected: points scaled by track length, sorted and rounded; the other year ignored."""
    def corner(number, *points):
        return _el("Corner", None, *[_el("Apex", None, _el("Position", {"progressDelta": str(p)})) for p in points],
                   text=number)

    tap = parse_bxml(_bxml(_el("CornerData", None,
                               _el(f"practice_programmes_{SOURCE_YEAR}", None, corner(" 1 \r\n  ", 0.5, 0.25), corner("2", 0.75)),
                               _el("practice_programmes_0", None, corner("9", 0.1)))))
    assert game_corners(tap, 1000) == {1: [250.0, 500.0], 2: [750.0]}


@allure.story("Corners")
@allure.title("Sub-corners split {case}")
@pytest.mark.parametrize("case, numbers, game, expected", [
    ("midway between the neighbours' game points", (1, 2), {1: [200, 300], 2: [600, 700]}, [(1, 0, 450), (2, 450, 1000)]),
    ("evenly when a corner has no game points", (1, 2, 3), {1: [100], 2: []}, [(1, 0, 333), (2, 333, 667), (3, 667, 1000)]),
    ("evenly when the midpoint would not increase", (1, 2), {1: [0, 0], 2: [0, 0]}, [(1, 0, 500), (2, 500, 1000)]),
])
def test_seed_sub_corners(case, numbers, game, expected):
    """A complex corner over 0 to 1000 m.

    Expected: ranges that tile the segment, from the game points where they are usable."""
    segment = ComplexCornerSegmentInfo(start_m=0, end_m=1000, corner_numbers=numbers)
    assert [(c.corner_number, c.start_m, c.end_m) for c in seed_sub_corners(segment, game)] == expected


@allure.story("Corners")
@allure.title("The corner report flags {case}")
@pytest.mark.parametrize("case, game, expected", [
    ("nothing when the file agrees", {1: [150.0], 2: [1050.0], 3: [1150.0]}, []),
    ("a corner the file lacks", {1: [150.0], 2: [1050.0], 3: [1150.0], 4: [1500.0]}, ["game only [4]"]),
    ("a corner only the file has", {1: [150.0], 2: [1050.0]}, ["file only [3]"]),
    ("points outside the same-numbered segment", {1: [500.0], 2: [1050.0], 3: [1150.0]}, ["corner 1 points 500-500"]),
])
def test_corner_report(case, game, expected):
    """Corners 1 (100 to 200 m) and a complex corner 2, 3 (1000 to 1200 m) against game points.

    Expected: one note per difference, none when they agree."""
    notes = corner_report(_layout(), game)
    assert len(notes) == len(expected)
    assert all(want in note for want, note in zip(expected, notes))


# --- update_segment_file ---------------------------------------------------------------------------------------------

_V1_FILE = {
    "circuit_name": "Test", "circuit_number": 99, "track_length": 2000,
    "segments": [
        {"type": "corner", "start_m": 100, "end_m": 200, "name": "One", "corner_number": 1},
        {"type": "complex_corner", "start_m": 1000, "end_m": 1200, "corner_numbers": [2, 3]},
        {"type": "straight", "start_m": 1200, "end_m": 2000, "name": "Back"},
    ],
    "sectors": {"s1": 600, "s2": 1300},
}


@pytest.fixture
def game_files(monkeypatch):
    """Synthetic game data for circuit 99: a square lap, a speed trap and DRS zone, corners 1 to 3 and a board."""
    markup = _markup(
        ("speed_trap", 0.25, 0.3, "maintrack", "spd_trp", {}),
        ("drs_detection_1", 0.5, 0.51, "maintrack", "drs_det", {"ID": "1"}),
        ("drs_activation_1", 0.75, 0.9, "maintrack", "drs_act", {"ID": "1"}),
    )
    corner = lambda n, p: _el("Corner", None, _el("Apex", None, _el("Position", {"progressDelta": str(p)})), text=str(n))
    taprogram = _bxml(_el("CornerData", None, _el(f"practice_programmes_{SOURCE_YEAR}", None,
                                                 corner(1, 0.075), corner(2, 0.52), corner(3, 0.58))))
    blobs = {".trackmarkup": markup, ".taprogram": taprogram, ".trackspacespline": b""}
    monkeypatch.setattr(extract_track_data, "read_erp_resource", lambda _, suffix: blobs[suffix])
    monkeypatch.setattr(extract_track_data, "parse_maintrack_knots", lambda _: _SQUARE / 10)
    monkeypatch.setattr(extract_track_data, "layout_boards",
                        lambda *_: [BrakeBoardInfo(distance_m=100, at_m=980, side="both")])


def _write(tmp_path, data: dict, newline: str = "\r\n", final: bool = True):
    path = tmp_path / "Test.json"
    path.write_bytes((json.dumps(data, indent=2).replace("\n", newline) + (newline if final else "")).encode())
    return path


@allure.story("Updating segment files")
@allure.title("--update writes zones, sub-corners and boards into a v1 file")
def test_update_segment_file(tmp_path, game_files):
    """A v1 file for a 2000 m square lap, with synthetic game data.

    Expected: schema_version 2 first, zones before segments, sub-corners seeded from the game points,
    the board on sub-corner 2, existing fields unchanged, and a clean run reports nothing."""
    path = _write(tmp_path, _V1_FILE)
    assert update_segment_file(path, tmp_path, "test") == []
    out = json.loads(path.read_text())
    assert list(out) == ["schema_version", "circuit_name", "circuit_number", "track_length", "speed_trap_m",
                         "drs_zones", "overtake_zones", "active_aero_zones", "segments", "sectors"]
    assert out["speed_trap_m"] == 500
    assert out["drs_zones"] == [{"id": 1, "detection_m": 1000, "activation": [{"start_m": 1500, "end_m": 1800}]}]
    complex_corner = out["segments"][1]
    assert [(c["corner_number"], c["start_m"], c["end_m"]) for c in complex_corner["corners"]] == \
        [(2, 1000, 1100), (3, 1100, 1200)]
    assert complex_corner["corners"][0]["brake_boards"] == [{"distance_m": 100, "at_m": 980, "side": "both"}]
    assert out["segments"][0] == _V1_FILE["segments"][0] and out["sectors"] == _V1_FILE["sectors"]


@allure.story("Updating segment files")
@allure.title("A second --update changes nothing")
@pytest.mark.parametrize("newline, final", [("\r\n", True), ("\n", False)])
def test_update_segment_file_is_idempotent(tmp_path, game_files, newline, final):
    """The same file updated twice, with CRLF and a trailing newline, and with LF and none.

    Expected: identical bytes after the second run, with the file's own line endings and trailing newline kept."""
    path = _write(tmp_path, _V1_FILE, newline, final)
    update_segment_file(path, tmp_path, "test")
    first = path.read_bytes()
    update_segment_file(path, tmp_path, "test")
    assert path.read_bytes() == first
    text = first.decode()
    assert ("\r\n" in text) == (newline == "\r\n") and text.endswith(newline) == final


@allure.story("Updating segment files")
@allure.title("Existing sub-corners are kept and only their boards are rewritten")
def test_update_segment_file_keeps_existing_sub_corners(tmp_path, game_files):
    """A file whose complex corner already has hand-set sub-corners at 1000 to 1050 and 1050 to 1200.

    Expected: the ranges stay, since `corners` is only seeded when missing; the board moves to sub-corner 2."""
    data = json.loads(json.dumps(_V1_FILE))
    data["segments"][1]["corners"] = [{"corner_number": 2, "start_m": 1000, "end_m": 1050},
                                      {"corner_number": 3, "start_m": 1050, "end_m": 1200}]
    path = _write(tmp_path, data)
    update_segment_file(path, tmp_path, "test")
    corners = json.loads(path.read_text())["segments"][1]["corners"]
    assert [(c["start_m"], c["end_m"]) for c in corners] == [(1000, 1050), (1050, 1200)]


@allure.story("Updating segment files")
@allure.title("A file that would fail validation is left untouched")
def test_update_segment_file_refuses_invalid_result(tmp_path, game_files, monkeypatch):
    """Zones extracted beyond the track length.

    Expected: the file is byte-identical afterwards and the report says it was not written."""
    monkeypatch.setattr(extract_track_data, "extract_zones", lambda *_: {"speed_trap_m": 5000})
    path = _write(tmp_path, _V1_FILE)
    before = path.read_bytes()
    notes = update_segment_file(path, tmp_path, "test")
    assert path.read_bytes() == before
    assert any("NOT WRITTEN" in note for note in notes)


def _label_board(at, dist):
    return BrakeBoardInfo(distance_m=dist, at_m=at, side="both")


@allure.story("Brake boards")
@allure.title("A board counting down into {where} belongs to it")
@pytest.mark.parametrize("where, at, dist, corner, sub", [
    ("the corner it stands in", 120, 50, 0, None),
    ("a complex corner's first sub-corner", 1000, 50, 1, 0),
    ("a complex corner, on its first sub-corner even when the spot is in a later one", 1040, 100, 1, 0),
])
def test_attach_boards_by_the_spot_it_counts_down_to(where, at, dist, corner, sub):
    """A board whose label points to a spot inside a corner or a complex corner.

    Expected: the board is on that corner, or on the first sub-corner of that complex corner."""
    segments, _ = attach_boards(_layout(), [_label_board(at, dist)], 2000)
    holder = segments[corner] if sub is None else segments[corner].corners[sub]
    assert [b.at_m for b in holder.brake_boards] == [at]


@allure.story("Brake boards")
@allure.title("A board standing in the previous corner still belongs to the one it counts down to")
def test_attach_boards_in_the_tail_of_the_previous_corner():
    """A 200 m board at 1898.8 m inside a long corner (1480 to 1965 m) and corner 10 starting at 1965 m, as at Monaco.

    Expected: the board is on the second corner, since 1898.8 + 200 lands inside it, with no note."""
    segments = (CornerSegmentInfo(name="A", start_m=1480, end_m=1965, corner_number=9),
                CornerSegmentInfo(name="B", start_m=1965, end_m=2130, corner_number=10))
    result, notes = attach_boards(segments, [_label_board(1898.8, 200)], 3300)
    assert result[0].brake_boards == () and [b.at_m for b in result[1].brake_boards] == [1898.8]
    assert notes == []


@allure.story("Brake boards")
@allure.title("A board on a straight goes to the next corner, a long corner keeps its own")
def test_attach_boards_straight_and_long_corner():
    """Baku turn 1 (115 to 415 m) and turn 2 (500 m). A 50 m board at 267.5 m points at 317.5 m, inside turn 1.
    A 100 m board at 300 m points at 400 m, still inside turn 1. A 100 m board at 450 m points at 550 m.

    Expected: the first two are on turn 1 and the third on turn 2."""
    segments = (CornerSegmentInfo(name="T1", start_m=115, end_m=415, corner_number=1),
                CornerSegmentInfo(name="T2", start_m=500, end_m=600, corner_number=2))
    result, _ = attach_boards(segments, [_label_board(267.5, 50), _label_board(300, 100), _label_board(450, 100)], 2000)
    assert [b.at_m for b in result[0].brake_boards] == [267.5, 300]
    assert [b.at_m for b in result[1].brake_boards] == [450]
