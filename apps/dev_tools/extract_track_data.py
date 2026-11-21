"""Extract track geometry (white-line edges) from an F1 25 install into assets/track-data/c<circuit>.npz.

usage: poetry run python -m apps.dev_tools.extract_track_data --game-dir "E:\\...\\F1 25" [--layout monza=11 ...]

With no --layout, every folder under <game>/2025_asset_groups/environment_package/tracks that maps to a
TrackID is extracted. Each --layout is "<game track folder>=<circuit number>" and replaces that default.

One compressed file per layout, so a single layout can be re-extracted alone. A run over the default full
table clears the folder first, so dropped layouts leave no stale file. A length report compares each
layout's midpoint lap length with track_length in assets/track-segments/*.json.
"""
import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import zstandard

from lib.f1_types import TrackID

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


def read_erp_resource(erp_path: Path, suffix: str) -> bytes:
    """Return the decompressed first resource whose name ends with `suffix` from an ERP v3 archive."""
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
                off, size, packed = frags[0]
                f.seek(data_off + off)
                raw = f.read(packed)
                if raw[:4] == _ZSTD_MAGIC:
                    raw = zstandard.ZstdDecompressor().decompress(raw, max_output_size=size)
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
    out: Dict[str, Any] = {
        "drs_zones": [{"id": i, "detection_m": z["detection_m"],
                       "activation": sorted(z["activation"], key=lambda a: a["start_m"])}
                      for i, z in sorted(drs.items()) if "detection_m" in z and z["activation"]],
        "overtake_zones": [{"id": i, **z} for i, z in sorted(overtake.items())
                           if "detection_m" in z and "activation_m" in z],
        "active_aero_zones": sorted(aero, key=lambda a: (a["mode"], a["start_m"])),
    }
    if trap is not None:
        out["speed_trap_m"] = trap
    return out


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


def json_lengths() -> Dict[int, float]:
    """circuit_number -> track_length from the segment files."""
    out: Dict[int, float] = {}
    for path in SEGMENTS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        out[int(data["circuit_number"])] = float(data["track_length"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game-dir", required=True, type=Path)
    ap.add_argument("--layout", nargs="+", metavar="FOLDER=CIRCUIT")
    args = ap.parse_args()

    specs = args.layout or game_layouts(args.game_dir)
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
