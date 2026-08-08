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
# SOFTWARE.

"""Helpers for the integration runner's --base A/B differential mode.

Kept separate from runner.py so the git-worktree plumbing and diff normalization can be
reasoned about (and unit tested) without pulling in the whole app-lifecycle harness.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from deepdiff import DeepDiff

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

# Fields that legitimately differ between two otherwise-identical replays: wall-clock
# timestamps on race-control messages (SessionState stamps them with time.time(), not the
# packet's session time) and the running app's version string.
_VOLATILE_KEYS = {"timestamp", "version"}

# ------------------------- FUNCTIONS -----------------------------------------------------------------------------------

def normalize_for_diff(obj: Any) -> Any:
    """Recursively strip volatile keys so two runs of the same replay diff as identical.

    Args:
        obj (Any): A JSON-decoded response body (or any nested dict/list structure).

    Returns:
        Any: The same structure with volatile keys removed.
    """
    if isinstance(obj, dict):
        return {k: normalize_for_diff(v) for k, v in obj.items() if k not in _VOLATILE_KEYS}
    if isinstance(obj, list):
        return [normalize_for_diff(v) for v in obj]
    return obj


def resolve_commit(base_ref: str, repo_root: Path) -> str:
    """Resolve a ref/branch/short-sha to a full commit sha, failing fast if it doesn't exist.

    Args:
        base_ref (str): Anything git accepts as a commit-ish.
        repo_root (Path): Repository root to run git in.

    Returns:
        str: The full commit sha.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
        cwd=repo_root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError(f"--base {base_ref!r} does not resolve to a commit: {result.stderr.strip()}")
    return result.stdout.strip()


def create_worktree(base_sha: str, repo_root: Path) -> Path:
    """Check out base_sha into a throwaway git worktree.

    Detached, so this works even if base_sha is a branch tip already checked out elsewhere.

    Args:
        base_sha (str): Full commit sha to check out.
        repo_root (Path): Repository root to run git in.

    Returns:
        Path: The worktree's directory.
    """
    worktree_dir = Path(tempfile.mkdtemp(prefix="png_diff_base_"))
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), base_sha],
        cwd=repo_root, check=True)
    return worktree_dir


def remove_worktree(worktree_dir: Path, repo_root: Path) -> None:
    """Tear down a worktree created by create_worktree.

    Args:
        worktree_dir (Path): The worktree to remove.
        repo_root (Path): Repository root to run git in.
    """
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_dir)],
        cwd=repo_root, check=False)
    shutil.rmtree(worktree_dir, ignore_errors=True)


def diff_captures(base_capture: dict, current_capture: dict,
                   progress_cb: Optional[Callable[[int, int, str], None]] = None) -> Tuple[int, List[str]]:
    """Deep-diff two {file_stem: {url: normalized_body}} captures.

    Args:
        base_capture (dict): Captured endpoint bodies from the base commit.
        current_capture (dict): Captured endpoint bodies from the working tree.
        progress_cb (Optional[Callable[[int, int, str], None]]): Called as
            (file_index, total_files, file_stem) before each file's urls are diffed. A DeepDiff
            call on a genuinely differing large body (a full tyre-wear-history) can still take
            tens of seconds even after the cheap-equality short-circuit below, so this is what
            keeps a long run from looking silently stuck.

    Returns:
        Tuple[int, List[str]]: (number of files/urls that differ, human-readable diff lines)
    """
    violations = 0
    report: List[str] = []

    file_stems = sorted(set(base_capture) | set(current_capture))
    for file_index, file_stem in enumerate(file_stems, start=1):
        if progress_cb:
            progress_cb(file_index, len(file_stems), file_stem)
        base_bodies = base_capture.get(file_stem)
        current_bodies = current_capture.get(file_stem)
        if base_bodies is None or current_bodies is None:
            missing_side = "base" if base_bodies is None else "current"
            violations += 1
            report.append(f"[FAIL] {file_stem}: missing from {missing_side} capture")
            continue

        for url in sorted(set(base_bodies) | set(current_bodies)):
            base_body = base_bodies.get(url)
            current_body = current_bodies.get(url)
            # Plain equality first: for a body this size (driver-info/race-info can carry a
            # full 1500-sample tyre-wear history per stint, across 24 drivers), DeepDiff costs
            # single-digit-to-tens of seconds even when the two sides are identical - the
            # common case for a correctness-preserving change. Only pay that cost to explain
            # an actual difference. Ordered comparison (no ignore_order): these lists (lap
            # history, tyre-stint history, race-control messages) are meaningfully ordered, so
            # a reorder is itself a real difference worth surfacing.
            if base_body == current_body:
                continue
            delta = DeepDiff(base_body, current_body)
            if delta:
                violations += 1
                report.append(f"[DIFF] {file_stem} {url}")
                report.extend(f"         {line}" for line in str(delta).splitlines())

    return violations, report
