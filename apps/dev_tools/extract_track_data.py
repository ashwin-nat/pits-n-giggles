"""Extract track geometry (white-line edges) from an F1 25 install into assets/track-data/c<circuit>.npz.

usage: poetry run python -m apps.dev_tools.extract_track_data --game-dir "E:\\...\\F1 25" [--layout monza=11 ...]

With --update, the geometry is left alone and the segment files in assets/track-segments get the speed trap,
DRS, overtake and active aero zones, seeded sub-corners and brake boards. Zones and boards are rewritten on
every run; `corners` is only created where missing. A file that fails validation is not written.

With no --layout, every folder under <game>/2025_asset_groups/environment_package/tracks that maps to a
TrackID is extracted. Each --layout is "<game track folder>=<circuit number>" and replaces that default.

One compressed file per layout, so a single layout can be re-extracted alone. A run over the default full
table clears the folder first, so dropped layouts leave no stale file. A length report compares each
layout's midpoint lap length with track_length in assets/track-segments/*.json.
"""
import argparse
import copy
import json
import re
import struct
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import numpy as np
import zstandard

from lib.f1_types import TrackID
from lib.track_segments_classifier.classifier import TrackSegmentsClassifier

TRACKS_SUBDIR = Path("2025_asset_groups") / "environment_package" / "tracks"
SOURCE_YEAR = 25  # F1 game year the data comes from; matches the 2025_asset_groups folder above
OUT_DIR = Path(__file__).resolve().parents[2] / "assets" / "track-data"
FORMAT_VERSION = 1  # keep in step with GEOMETRY_VERSION in apps/lap-analyzer/src/lib/trackGeometry.ts

SEGMENTS_DIR = Path(__file__).resolve().parents[2] / "assets" / "track-segments"
LENGTH_TOLERANCE = 0.01

# Game folders whose name differs from the lowercased TrackID member name.
FOLDER_ALIASES = {"bahrain": "sakhir_bahrain", "baku": "baku_azerbaijan", "spa_francorchamps": "spa"}

_TOKEN = re.compile(rb"[\x20-\x7e]{1,200}\x00")
_ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def iter_erp_resources(erp_path: Path, suffix: str) -> Iterator[Tuple[str, bytes]]:
    """Yield (name, decompressed bytes) for each resource ending with `suffix` in an ERP v3 archive."""
    with open(erp_path, "rb") as f:
        hdr = f.read(0x38)
        assert hdr[:4] == b"ERPK", f"{erp_path} is not an ERP archive"
        ver = struct.unpack_from("<i", hdr, 4)[0]
        info_off, _, data_off = struct.unpack_from("<QQQ", hdr, 0x10)
        f.seek(info_off)
        num, _ = struct.unpack("<ii", f.read(8))
        for _ in range(num):
            f.read(4)
            nlen = struct.unpack("<H", f.read(2))[0]
            name = f.read(nlen).rstrip(b"\0").decode("latin1")
            f.read(16 + 4)
            if ver >= 4:
                f.read(2)
            frags = []
            for _ in range(f.read(1)[0]):
                f.read(4)
                off, size = struct.unpack("<QQ", f.read(16))
                f.read(4)
                f.read(1)
                packed = struct.unpack("<Q", f.read(8))[0]
                frags.append((off, size, packed))
            f.read(16)
            if name.endswith(suffix):
                table_pos = f.tell()
                off, size, packed = frags[0]
                f.seek(data_off + off)
                raw = f.read(packed)
                if raw[:4] == _ZSTD_MAGIC:
                    raw = zstandard.ZstdDecompressor().decompress(raw, max_output_size=size)
                f.seek(table_pos)
                yield name, raw


def read_erp_resource(erp_path: Path, suffix: str) -> bytes:
    """Return the first resource ending with `suffix` from an ERP v3 archive."""
    for _, raw in iter_erp_resources(erp_path, suffix):
        return raw
    raise ValueError(f"no {suffix} resource in {erp_path}")


def read_aispline(erp_path: Path) -> bytes:
    """Return the decompressed .aispline blob from an ERP v3 archive."""
    return read_erp_resource(erp_path, ".aispline")


class BxmlNode:
    """One BXML element: tag, attributes, text and children."""
    __slots__ = ("tag", "attrs", "text", "children")

    def __init__(self, tag: str, attrs: Dict[str, str]):
        self.tag = tag
        self.attrs = attrs
        self.text = ""
        self.children: List["BxmlNode"] = []

    def find(self, tag: str) -> Optional["BxmlNode"]:
        return next((c for c in self.children if c.tag == tag), None)

    def findall(self, tag: str) -> List["BxmlNode"]:
        return [c for c in self.children if c.tag == tag]


def parse_bxml(data: bytes) -> BxmlNode:
    """Parse a BXML blob into a tree. Nodes are int16 length, type (0 element, 1 text, 5 end), pad, int16 attrs."""
    assert data[:5] == b"\x01BXML", "not a BXML blob"
    pos, stack, root = 5, [], None
    while pos < len(data):
        length, kind, _, nattr = struct.unpack_from("<HBBH", data, pos)
        parts = data[pos + 6:pos + 2 + length].split(b"\0")
        pos += 2 + length
        if kind == 5:
            stack.pop()
        elif kind == 1:
            stack[-1].text = parts[0].decode("latin1")
        else:
            strs = [p.decode("latin1") for p in parts]
            node = BxmlNode(strs[0], dict(zip(strs[1:1 + 2 * nattr:2], strs[2:2 + 2 * nattr:2])))
            if stack:
                stack[-1].children.append(node)
            elif root is None:
                root = node
            stack.append(node)
    assert root is not None
    return root


def parse_gates(data: bytes) -> List[Dict[str, Any]]:
    """Gates with name, position, normal and waypoint lengths, in file order."""
    t = [m.group(0)[:-1].decode("latin1") for m in _TOKEN.finditer(data)]
    gates: List[Dict[str, Any]] = []
    cur: Dict[str, Any] = {"wp": {}}  # scratch until the first gate
    i, n = 0, len(t)
    while i < n:
        w = t[i]
        if w == "gate" and i + 2 < n and t[i + 1] == "id":
            cur = {"wp": {}}
            gates.append(cur)
            i += 3
        elif w == "name" and "name" not in cur and t[i + 1].startswith("ai_gate"):
            cur["name"] = t[i + 1]
            i += 2
        elif w in {"position", "normal"} and w not in cur and t[i + 1] == "x":
            cur[w] = (float(t[i + 2]), float(t[i + 4]), float(t[i + 6]))
            i += 7
        elif w == "waypoint" and t[i + 1] == "id" and t[i + 3] == "type" and t[i + 5] == "length":
            cur["wp"][t[i + 4]] = float(t[i + 6])
            i += 7
        else:
            i += 1
    return gates


def build_geometry(gates: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
    """(edges (N, 6) left xyz + right xyz, lap fraction (N,)) from track gates.

    The fraction is arc length along the midpoint of the white lines; gate 0 is the start/finish line.
    """
    keys = ("left_white_line", "right_white_line")
    gates = [g for g in gates
             if "pit" not in g.get("name", "") and "position" in g and "normal" in g
             and all(k in g["wp"] for k in keys)]
    pos = np.array([g["position"] for g in gates])
    nrm = np.array([g["normal"] for g in gates])
    left = pos + nrm * np.array([g["wp"][keys[0]] for g in gates])[:, None]
    right = pos + nrm * np.array([g["wp"][keys[1]] for g in gates])[:, None]
    mid = (left + right) / 2
    seg = np.linalg.norm(np.diff(np.vstack([mid, mid[:1]])[:, [0, 2]], axis=0), axis=1)
    frac = np.concatenate([[0.0], np.cumsum(seg)[:-1]]) / seg.sum()
    return np.hstack([left, right]).astype(np.float32), frac.astype(np.float32)


def midpoint_length(edges: np.ndarray) -> float:
    """Closed-loop length in metres of the midpoint between the white lines."""
    mid = (edges[:, :3] + edges[:, 3:]) / 2
    return float(np.linalg.norm(np.diff(np.vstack([mid, mid[:1]])[:, [0, 2]], axis=0), axis=1).sum())


_KNOT = re.compile(rb"Knot\0position\0([^\0]+)\0")


def parse_maintrack_knots(data: bytes) -> np.ndarray:
    """(N, 2) x, z of the `maintrack` spline knots from a .trackspacespline blob."""
    start = data.find(b"maintrack\0")
    end = data.find(b"TrackSpaceSpline\0", start)
    body = data[start:end if end > 0 else len(data)]
    return np.array([[float(v) for v in m.group(1).split(b",")] for m in _KNOT.finditer(body)])[:, [0, 2]]


def knot_mapper(knots: np.ndarray, track_length: float) -> Callable[[float], float]:
    """Markup position (fraction of the knot count, wrapping) -> lap distance in metres.

    Knots are unevenly spaced, so a plain lap fraction is wrong by over 100 m on some tracks.
    """
    closed = np.vstack([knots, knots[:1]])
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))])
    index = np.arange(len(arc))
    return lambda frac: round(float(np.interp((frac % 1.0) * len(knots), index, arc) / arc[-1] * track_length), 1)


def extract_zones(markup: BxmlNode, to_m: Callable[[float], float]) -> Dict[str, Any]:
    """Speed trap, DRS, overtake and active aero fields from a parsed .trackmarkup, main track only."""
    drs: Dict[int, Dict[str, Any]] = {}
    overtake: Dict[int, Dict[str, Any]] = {}
    aero: List[Dict[str, Any]] = []
    trap: Optional[float] = None
    for el in markup.find("MarkupList").findall("MarkupElement"):
        if el.attrs.get("SplineName") != "maintrack":
            continue
        start, end = to_m(float(el.attrs["Start"])), to_m(float(el.attrs["End"]))
        if el.attrs.get("Name") == "speed_trap":
            trap = start
        for attr in (el.find("Attributes") or BxmlNode("", {})).findall("Attribute"):
            props = {p.attrs["Type"]: p.attrs["Value"] for p in (attr.find("Properties") or BxmlNode("", {})).findall("Property")}
            kind, ident = attr.attrs.get("Type"), int(float(props.get("ID", 0)))
            if kind == "drs_det":
                drs.setdefault(ident, {"activation": []})["detection_m"] = start
            elif kind == "drs_act":
                drs.setdefault(ident, {"activation": []})["activation"].append({"start_m": start, "end_m": end})
            elif kind == "ers_over_det":
                overtake.setdefault(ident, {})["detection_m"] = start
            elif kind == "ers_over_act":
                overtake.setdefault(ident, {})["activation_m"] = start
            elif kind == "x_mode":
                aero.append({"mode": props.get("type", "").lower(), "start_m": start, "end_m": end})
    out: Dict[str, Any] = {} if trap is None else {"speed_trap_m": trap}
    out |= {
        "drs_zones": [{"id": i, "detection_m": z["detection_m"],
                       "activation": sorted(z["activation"], key=lambda a: a["start_m"])}
                      for i, z in sorted(drs.items()) if "detection_m" in z and z["activation"]],
        "overtake_zones": [{"id": i, **z} for i, z in sorted(overtake.items())
                           if "detection_m" in z and "activation_m" in z],
        "active_aero_zones": sorted(aero, key=lambda a: (a["mode"], a["start_m"])),
    }
    return out


class PkgReader:
    """Minimal `!pkg` layer reader: dictionaries, lists, strings, floats and 4x4 matrices."""

    def __init__(self, data: bytes):
        self.data = data
        self.chunks: List[Tuple[Any, ...]] = []
        vca = data.find(b"!vca")
        count = struct.unpack_from("<I", data, vca + 4)[0]
        for i in range(count):
            off = struct.unpack_from("<I", data, vca + 8 + 4 * i)[0] & 0xFFFFFF
            if data[off:off + 4] == b"!sbi":
                self.chunks.append(("str", off + 8))
            else:
                _, elem_size = struct.unpack_from("<II", data, off + 8)
                self.chunks.append((data[off + 4:off + 8].decode("latin1"), off + 16, elem_size))
        self.root = struct.unpack_from("<I", data, 8)[0] & 0xFFFFFF

    def _string(self, off: int) -> str:
        base = next(c for c in self.chunks if c[0] == "str")[1]
        n = self.data[base + off]
        return self.data[base + off + 1:base + off + 1 + n].decode("latin1")

    def _value(self, v: int, depth: int) -> Any:
        hi, lo = v >> 24, v & 0xFFFFFF
        if hi == 0x80:
            return self.obj(lo, depth + 1)
        if hi >= len(self.chunks):
            return None
        kind, base, *rest = self.chunks[hi]
        if kind == "str":
            return self._string(lo)
        pos = base + lo * rest[0]
        if kind == "mat4":
            return ("mat4", struct.unpack_from("<16f", self.data, pos))
        if kind == "fp32":
            return struct.unpack_from("<f", self.data, pos)[0]
        return None

    def obj(self, off: int, depth: int = 0) -> Any:
        """The dict (`!idi`) or list (`!ili`) at `off`, or None for any other tag."""
        tag = self.data[off:off + 4]
        if depth > 12:
            return None
        count = struct.unpack_from("<I", self.data, off + 4)[0] & 0xFFFFFF
        if tag == b"!idi":
            return {self._string(k): self._value(v, depth)
                    for k, v, _ in (struct.unpack_from("<III", self.data, off + 8 + 12 * i) for i in range(count))}
        if tag == b"!ili":
            return [self._value(struct.unpack_from("<I", self.data, off + 8 + 4 * i)[0], depth) for i in range(count)]
        return None


def _walk(node: Any) -> Iterator[Any]:
    """Every value nested in dicts and lists, depth first."""
    yield node
    if isinstance(node, dict):
        node = list(node.values())
    if isinstance(node, list):
        for child in node:
            yield from _walk(child)


_CONTEXT = re.compile(r"context=([^&]+)")
_SPONSOR_DIST = re.compile(r"sp_(\d{2,3})_")
_NAME_DIST = re.compile(r"(?:pole|_)(\d{2,3})(?:[lr]?_|$)")
BOARD_DISTANCES = (50, 100, 150, 200, 250, 300)


def board_objects(layer: bytes) -> List[Dict[str, Any]]:
    """Brake board objects in a .layer blob: name, labelled distance (None if unresolved), world x and z."""
    if b"brake" not in layer.lower():
        return []
    pkg = PkgReader(layer)
    out = []
    for inst in (pkg.obj(pkg.root) or {}).get("instances") or []:
        name = inst.get("name") if isinstance(inst, dict) else None
        if not isinstance(name, str) or "brake" not in name.lower():
            continue
        mat = next((v["transform"][1] for v in _walk(inst)
                    if isinstance(v, dict) and isinstance(v.get("transform"), tuple)), None)
        if mat is None:
            continue
        short = name.split("$")[-1]
        refs = [s for s in _walk(inst) if isinstance(s, str) and ".emb" in s]
        dist = next((int(m.group(1)) for r in refs for c in _CONTEXT.findall(r)
                     if (m := _SPONSOR_DIST.match(c))), None)
        if dist is None and "sponsor" not in short and (m := _NAME_DIST.search(short)):
            dist = int(m.group(1))
        out.append({"name": short, "dist": dist, "x": mat[12], "z": mat[14]})
    return out


def project_to_track(x: float, z: float, knots: np.ndarray, track_length: float) -> Tuple[float, float]:
    """(lap distance, signed lateral offset in metres) of a world point against the maintrack knots."""
    closed = np.vstack([knots, knots[:1]])
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))])
    start, vec = closed[:-1], np.diff(closed, axis=0)
    p = np.array([x, z])
    t = np.clip(((p - start) * vec).sum(1) / (vec * vec).sum(1), 0, 1)
    dist = ((start + t[:, None] * vec - p) ** 2).sum(1)
    i = int(np.argmin(dist))
    side = np.sign(vec[i, 0] * (z - start[i, 1]) - vec[i, 1] * (x - start[i, 0]))
    return float((arc[i] + t[i] * np.linalg.norm(vec[i])) / arc[-1] * track_length), float(np.sqrt(dist[i]) * side)


def group_boards(objects: List[Dict[str, Any]], knots: np.ndarray, track_length: float) -> List[Dict[str, Any]]:
    """Brake boards as schema entries, sorted by lap distance. Left and right boards at one spot merge to `both`."""
    seen, points = set(), []
    for obj in objects:
        key = (round(obj["x"]), round(obj["z"]))
        if obj["dist"] not in BOARD_DISTANCES or key in seen:
            continue
        seen.add(key)
        at, lateral = project_to_track(obj["x"], obj["z"], knots, track_length)
        if abs(lateral) < 40:
            points.append((obj["dist"], at, "left" if lateral < 0 else "right"))
    groups: List[Dict[str, Any]] = []
    for dist, at, side in sorted(points):
        for g in groups:
            if g["distance_m"] == dist and abs(g["at"][0] - at) < 12:
                g["at"].append(at)
                g["sides"].add(side)
                break
        else:
            groups.append({"distance_m": dist, "at": [at], "sides": {side}})
    return [{"distance_m": g["distance_m"], "at_m": round(float(np.mean(g["at"])), 1),
             "side": "both" if len(g["sides"]) == 2 else next(iter(g["sides"]))}
            for g in sorted(groups, key=lambda g: g["at"][0])]


def layout_boards(wep_dir: Path, folder: str, knots: np.ndarray, track_length: float) -> List[Dict[str, Any]]:
    """Brake boards for one layout from its common and f1 archives.

    The other eras (classic, f1_26, f2, myteam, story) give the same boards on all 28 layouts.
    """
    objects: List[Dict[str, Any]] = []
    for archive in ("common", "f1"):
        for _, layer in iter_erp_resources(wep_dir / f"{folder}_{archive}.erp", ".layer"):
            objects += board_objects(layer)
    return group_boards(objects, knots, track_length)


def attach_boards(segments: List[Dict[str, Any]], boards: List[Dict[str, Any]], track_length: float) -> List[str]:
    """Set `brake_boards` on the corner each board warns about, replacing any there. Returns notes for odd boards.

    A board belongs to the first corner or sub-corner that starts within 150 m behind it and ends after it.
    Complex corners must already hold their `corners`.
    """
    targets = [c for s in segments for c in (s.get("corners") or [s] if s["type"] != "straight" else [])]
    for t in targets:
        t.pop("brake_boards", None)
    targets.sort(key=lambda t: t["start_m"])
    notes = []
    for b in boards:
        target = next((t for t in targets if t["start_m"] >= b["at_m"] - 150 and t["end_m"] > b["at_m"]), None)
        target = target or (targets[0] if targets else None)
        if target is None:
            continue
        gap = (target["start_m"] - b["at_m"]) % track_length
        if 450 < gap < track_length - 200:
            notes.append(f"{b['distance_m']} m board at {b['at_m']} m is {gap:.0f} m before its corner")
        target.setdefault("brake_boards", []).append(b)
    return notes


def game_corners(taprogram: BxmlNode, track_length: float) -> Dict[int, List[float]]:
    """Corner number -> sorted lap distances of its points, from the .taprogram.

    These are rough positions, not apexes. Positions are a plain lap fraction, unlike markup.
    """
    program = taprogram.find(f"practice_programmes_{SOURCE_YEAR}")
    out: Dict[int, List[float]] = {}
    for corner in (program.findall("Corner") if program else []):
        points = [float(pos.attrs["progressDelta"]) * track_length
                  for apex in corner.findall("Apex") for pos in apex.findall("Position")]
        out[int(corner.text.strip())] = sorted(round(p, 1) for p in points)
    return out


def seed_sub_corners(segment: Dict[str, Any], game: Dict[int, List[float]]) -> List[Dict[str, Any]]:
    """Sub-corner ranges tiling a complex corner, split midway between neighbouring corners' game points.

    Falls back to an even split where a corner has no points or the midpoints would not increase.
    """
    start, end, numbers = segment["start_m"], segment["end_m"], segment["corner_numbers"]
    even = [round(start + (end - start) * k / len(numbers)) for k in range(1, len(numbers))]
    cuts = []
    for k in range(len(numbers) - 1):
        a, b = game.get(numbers[k]), game.get(numbers[k + 1])
        cuts.append(round((a[-1] + b[0]) / 2) if a and b else even[k])
    if not all(lo < hi for lo, hi in zip([start] + cuts, cuts + [end])):
        cuts = even
    edges = [start] + cuts + [end]
    return [{"corner_number": n, "start_m": edges[k], "end_m": edges[k + 1]} for k, n in enumerate(numbers)]


def corner_report(segments: List[Dict[str, Any]], game: Dict[int, List[float]]) -> List[str]:
    """Differences between the game's corners and a segment file's: missing numbers and misplaced points."""
    ours: Dict[int, Dict[str, Any]] = {}
    for seg in segments:
        for number in seg.get("corner_numbers", [seg["corner_number"]] if "corner_number" in seg else []):
            ours[number] = seg
    notes = []
    if set(game) != set(ours):
        notes.append(f"corner numbers differ: game only {sorted(set(game) - set(ours))}, "
                     f"file only {sorted(set(ours) - set(game))}")
    for number, points in sorted(game.items()):
        seg = ours.get(number)
        if seg and points and not any(seg["start_m"] <= p < seg["end_m"] for p in points):
            notes.append(f"corner {number} points {points[0]:.0f}-{points[-1]:.0f} m outside "
                         f"{seg['start_m']}-{seg['end_m']} m")
    return notes


ZONE_FIELDS = ("speed_trap_m", "drs_zones", "overtake_zones", "active_aero_zones")


def _whole_numbers(value: Any) -> Any:
    """Floats that are whole become ints, so the files do not churn on `3055.0` vs `3055`."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _whole_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_whole_numbers(v) for v in value]
    return value


def merge_track_data(data: Dict[str, Any], zones: Dict[str, Any], game: Dict[int, List[float]],
                     boards: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """A schema v2 copy of a segment file with the extractor-owned fields rewritten, plus notes on odd boards.

    Zones and brake boards are replaced. `corners` is only created where a complex corner has none.
    """
    segments = copy.deepcopy(data["segments"])
    for seg in segments:
        if seg["type"] == "complex_corner" and not seg.get("corners"):
            seg["corners"] = seed_sub_corners(seg, game)
    notes = attach_boards(segments, boards, data["track_length"])
    out: Dict[str, Any] = {"schema_version": 2}
    for key, value in data.items():
        if key == "schema_version" or key in ZONE_FIELDS:
            continue
        if key == "segments":
            out.update(zones)
            value = segments
        out[key] = value
    return _whole_numbers(out), notes


def update_segment_file(path: Path, wep_dir: Path, folder: str) -> List[str]:
    """Rewrite one segment file from the game data. Returns report lines; the file is untouched if it fails validation."""
    raw = path.read_bytes().decode("utf-8")
    data = json.loads(raw)
    length = float(data["track_length"])
    common = wep_dir / f"{folder}_common.erp"
    knots = parse_maintrack_knots(read_erp_resource(common, ".trackspacespline"))
    zones = extract_zones(parse_bxml(read_erp_resource(common, ".trackmarkup")), knot_mapper(knots, length))
    game = game_corners(parse_bxml(read_erp_resource(common, ".taprogram")), length)
    merged, notes = merge_track_data(data, zones, game, layout_boards(wep_dir, folder, knots, length))
    notes = corner_report(data["segments"], game) + notes
    try:
        TrackSegmentsClassifier.model_validate({**merged, "use_cache": False})
    except ValueError as err:
        return notes + [f"NOT WRITTEN, fails validation: {str(err).splitlines()[0]}"]
    text = json.dumps(merged, indent=2, ensure_ascii=False)
    newline = "\r\n" if "\r\n" in raw else "\n"
    path.write_bytes((text.replace("\n", newline) + (newline if raw.endswith("\n") else "")).encode("utf-8"))
    return notes


def circuit_for_folder(folder: str) -> Optional[int]:
    """Circuit number for a game track folder, or None if it is not a known TrackID."""
    return TrackID.lowercase_names().get(FOLDER_ALIASES.get(folder, folder))


def game_layouts(game_dir: Path) -> List[str]:
    """FOLDER=CIRCUIT for every track folder in the install that maps to a TrackID."""
    specs = []
    for path in sorted((game_dir / TRACKS_SUBDIR).iterdir()):
        circuit = circuit_for_folder(path.name)
        if path.is_dir() and circuit is not None:
            specs.append(f"{path.name}={circuit}")
    return specs


def segment_files() -> Dict[int, Path]:
    """circuit_number -> segment file path."""
    return {int(json.loads(path.read_text(encoding="utf-8"))["circuit_number"]): path
            for path in SEGMENTS_DIR.glob("*.json")}


def json_lengths() -> Dict[int, float]:
    """circuit_number -> track_length from the segment files."""
    return {c: float(json.loads(p.read_text(encoding="utf-8"))["track_length"]) for c, p in segment_files().items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game-dir", required=True, type=Path)
    ap.add_argument("--layout", nargs="+", metavar="FOLDER=CIRCUIT")
    ap.add_argument("--update", action="store_true",
                    help="rewrite zones, corners and brake boards in assets/track-segments instead of the geometry")
    args = ap.parse_args()

    specs = args.layout or game_layouts(args.game_dir)
    if args.update:
        files = segment_files()
        for spec in specs:
            folder, _, number = spec.partition("=")
            path = files.get(int(number)) if number.isdigit() else None
            if path is None:
                ap.error(f"--layout {spec!r} must be FOLDER=CIRCUIT with an existing segment file")
            notes = update_segment_file(path, args.game_dir / TRACKS_SUBDIR / folder / "wep", folder)
            print(f"{folder}: {path.name}" + "".join(f"\n    {n}" for n in notes))
        return
    real = json_lengths()
    if not args.layout:
        for stale in OUT_DIR.glob("c*.npz"):
            stale.unlink()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    flagged: List[str] = []
    for spec in specs:
        folder, _, number = spec.partition("=")
        if not number.isdigit():
            ap.error(f"--layout {spec!r} must be FOLDER=CIRCUIT, the id is never guessed")
        circuit = int(number)
        erp = args.game_dir / TRACKS_SUBDIR / folder / "wep" / f"{folder}_common.erp"
        gates = parse_gates(read_aispline(erp))
        edges, frac = build_geometry(gates)
        np.savez_compressed(OUT_DIR / f"c{circuit}.npz", edges=edges, frac=frac,
                            version=np.int32(FORMAT_VERSION), source_year=np.int32(SOURCE_YEAR))
        length = midpoint_length(edges)
        expected = real.get(circuit)
        note = "no segment file"
        if expected:
            gap = length / expected - 1
            note = f"{length:.0f} m vs {expected:.0f} m ({gap:+.2%})"
            if abs(gap) > LENGTH_TOLERANCE:
                flagged.append(f"{folder} {note}")
                note += "  <-- FLAG"
        print(f"{folder}: circuit {circuit}, {len(gates)} gates, {len(edges)} track gates, {note}")

    print(f"wrote {len(specs)} file(s) to {OUT_DIR}")
    if flagged:
        print(f"length gap over {LENGTH_TOLERANCE:.0%}: " + "; ".join(flagged))


if __name__ == "__main__":
    main()
