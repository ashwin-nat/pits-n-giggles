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
from typing import Any, Dict, List, Optional, Tuple

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


def read_aispline(erp_path: Path) -> bytes:
    """Return the decompressed .aispline blob from an ERP v3 archive."""
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
            if name.endswith(".aispline"):
                off, size, packed = frags[0]
                f.seek(data_off + off)
                raw = f.read(packed)
                if raw[:4] == _ZSTD_MAGIC:
                    raw = zstandard.ZstdDecompressor().decompress(raw, max_output_size=size)
                return raw
    raise ValueError(f"no .aispline in {erp_path}")


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
