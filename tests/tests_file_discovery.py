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
# pylint: skip-file

"""lib.file_discovery: the generic multi-handler registry engine itself, independent
of any real file format. Two synthetic handler types (not pngt/JSON) stand in for
"two registered file types sharing one directory walk" -- the scenario
apps/web/pngt_discovery.py's own tests don't exercise, since they only ever register
one handler via the build_pngt_session_list() convenience wrapper.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from lib.file_discovery import DiscoveryConfig, discover_all
from lib.logger import PngLogger

logging.setLoggerClass(PngLogger)


def _logger() -> PngLogger:
    return logging.getLogger("test_file_discovery")


@dataclass(frozen=True)
class _Entry:
    rel_path: str
    content: str


def _make_handler(glob: str, cache_filename: str) -> DiscoveryConfig:
    def _parse(path: Path) -> str:
        return path.read_text(encoding='utf-8')

    def _make_entry(rel_path: str, parsed: str, _previous: Optional[_Entry]) -> _Entry:
        return _Entry(rel_path=rel_path, content=parsed)

    def _to_cache_dict(entry: _Entry) -> Dict[str, Any]:
        return {'content': entry.content}

    def _from_cache_dict(rel_path: str, raw: Dict[str, Any]) -> _Entry:
        return _Entry(rel_path=rel_path, content=raw['content'])

    return DiscoveryConfig[_Entry](
        glob=glob,
        cache_filename=cache_filename,
        parse=_parse,
        make_entry=_make_entry,
        to_cache_dict=_to_cache_dict,
        from_cache_dict=_from_cache_dict,
        sort_key=lambda e: e.rel_path,
    )


async def _run_all(session_dir: Path, handlers):
    """Drain discover_all(); return {handler_index: final_entries_list}."""
    by_index = {id(h): i for i, h in enumerate(handlers)}
    results = {i: [] for i in range(len(handlers))}
    async for handler, entries in discover_all(session_dir, _logger(), "0.0.1-test", handlers):
        results[by_index[id(handler)]] = entries
    return results


async def test_two_handlers_dispatch_independently(tmp_path):
    (tmp_path / "a.alpha").write_text("alpha-content", encoding='utf-8')
    (tmp_path / "b.beta").write_text("beta-content", encoding='utf-8')

    alpha = _make_handler("*.alpha", ".cache_alpha.json.gz")
    beta = _make_handler("*.beta", ".cache_beta.json.gz")

    results = await _run_all(tmp_path, [alpha, beta])

    assert [e.rel_path for e in results[0]] == ["a.alpha"]
    assert [e.rel_path for e in results[1]] == ["b.beta"]
    assert results[0][0].content == "alpha-content"
    assert results[1][0].content == "beta-content"


async def test_unmatched_file_is_ignored(tmp_path):
    (tmp_path / "a.alpha").write_text("alpha-content", encoding='utf-8')
    (tmp_path / "c.gamma").write_text("unmatched", encoding='utf-8')

    alpha = _make_handler("*.alpha", ".cache_alpha.json.gz")
    results = await _run_all(tmp_path, [alpha])

    assert [e.rel_path for e in results[0]] == ["a.alpha"]


async def test_each_handler_gets_its_own_cache_file(tmp_path):
    (tmp_path / "a.alpha").write_text("alpha-content", encoding='utf-8')
    (tmp_path / "b.beta").write_text("beta-content", encoding='utf-8')

    alpha = _make_handler("*.alpha", ".cache_alpha.json.gz")
    beta = _make_handler("*.beta", ".cache_beta.json.gz")
    await _run_all(tmp_path, [alpha, beta])

    assert (tmp_path / ".cache_alpha.json.gz").exists()
    assert (tmp_path / ".cache_beta.json.gz").exists()


async def test_overlapping_glob_resolves_to_first_registered(tmp_path, caplog):
    (tmp_path / "a.alpha").write_text("alpha-content", encoding='utf-8')

    first = _make_handler("*.alpha", ".cache_first.json.gz")
    second = _make_handler("a.*", ".cache_second.json.gz")  # also matches a.alpha

    with caplog.at_level("WARNING"):
        results = await _run_all(tmp_path, [first, second])

    assert [e.rel_path for e in results[0]] == ["a.alpha"]
    assert results[1] == []
    assert any("multiple registered globs" in r.message for r in caplog.records)


async def test_missing_session_dir_yields_nothing(tmp_path):
    alpha = _make_handler("*.alpha", ".cache_alpha.json.gz")
    results = await _run_all(tmp_path / "does-not-exist", [alpha])
    assert results[0] == []
