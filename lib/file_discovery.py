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

"""Generic "scan a directory of recording files, cache their parsed metadata by
mtime" engine, extracted from session_discovery.py's shape when pngt_discovery.py
needed the identical skeleton for a second file format.

A single call to `discover_all()` walks the session directory once and fans each file
out to whichever registered `DiscoveryConfig` handler's glob matches it. Adding a third
file type later means writing one more handler and registering it -- the walk, the
per-type mtime cache, the concurrent parsing, and the progressive yields are all
already generic.

session_discovery.py (the existing JSON save-viewer discovery) is NOT migrated onto
this engine yet -- it's shipped, tested, and entangled with F1-specific race-analytics
recomputation (tyre wear backfill, overtake enrichment, etc.) that's orthogonal to the
generic scan/cache shape. Migrating it to be a handler here is a deliberate, isolated
follow-up, not bundled into the change that introduced this engine.

One deliberate scope limit versus session_discovery.py's current behaviour: a file that
fails to parse is skipped entirely here (logged, excluded from the result), not given a
filename-derived placeholder entry. session_discovery.py's placeholder-on-failure
behaviour is JSON-specific (it can derive a usable-enough summary from the filename
alone); nothing here rules that out for a future consumer, it's just not needed by
pngt_discovery.py, whose only usable data lives inside the archive itself.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import fnmatch
import gzip
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (Any, AsyncIterator, Callable, Dict, Generic, List,
                    Optional, Tuple, Type, TypeVar)

import orjson

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Cache entries are tagged with the app version that produced them. Any version
# mismatch (upgrade or downgrade) invalidates the whole cache - mtime alone can't
# detect that the *parsing logic*, not the file, changed, and a manually-maintained
# schema counter is too easy to forget bumping. Same reasoning as session_discovery.py.
_APP_VERSION_KEY = '__app_version__'

T = TypeVar('T')

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class DiscoveryConfig(Generic[T]):
    """One registered file type's handler. The engine owns the directory walk,
    per-type mtime cache, concurrency, and pruning; a handler supplies what a `T`
    (the "entry" a consumer gets back for this type) actually is and how to get one.
    """
    glob: str  # e.g. '*.pngt' -- matched against each file's name, not used to walk
    cache_filename: str  # e.g. '.png_pngt_cache.json.gz'
    parse: Callable[[Path], Any]
    """Reads and returns the raw parsed content of one file. Runs inside
    asyncio.to_thread -- must not touch any shared mutable state (see `make_entry`
    for why slug-like derived state is handled separately, not here)."""
    make_entry: Callable[[str, Any, Optional[T]], T]
    """(rel_path, parsed, previous_entry) -> entry. `previous_entry` is this same
    file's entry from the *previous* run, reconstructed from the on-disk cache before
    it gets overwritten -- None if the file is new. Runs back on the event loop
    (single-threaded), so it's the only safe place to carry forward any derived state
    that must survive a reparse (e.g. pngt's slug, which must not change on a rename
    even though a rename changes both session_name and the file's mtime)."""
    to_cache_dict: Callable[[T], Dict[str, Any]]
    from_cache_dict: Callable[[str, Dict[str, Any]], T]
    sort_key: Callable[[T], Any]
    """Descending sort key applied to this handler's entry list on every yield."""
    concurrency: int = 16
    catch: Tuple[Type[BaseException], ...] = (Exception,)
    """Exception types that cause a single file to be skipped (logged) rather than
    aborting the whole scan."""
    on_cache_loaded: Optional[Callable[[Dict[str, T]], None]] = None
    """Called once, synchronously, right after this handler's on-disk cache is loaded
    and before any concurrent parsing starts -- with every previously-known entry,
    keyed by rel_path. Lets a handler see the *complete* prior state up front rather
    than piecemeal as cache hits resolve in arbitrary completion order, which matters
    for any cross-file invariant a single file's own `make_entry` can't enforce alone
    (pngt_discovery.py uses this to pre-reserve every already-assigned slug before a
    newly-discovered file's collision check runs)."""

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def find_files(session_dir: Path, glob: str) -> List[Path]:
    """Recursively find all files matching `glob` under session_dir; paths relative
    to session_dir. Hidden files (cache files included) are always excluded.

    Standalone utility, independent of discover_all()'s own single-pass walk below --
    still useful for a handler (or a test) that wants "just the file list" for one
    type without registering it and running a full scan.
    """
    return [
        p.relative_to(session_dir)
        for p in session_dir.rglob(glob)
        if not p.name.startswith('.')
    ]


def _load_cache(cache_path: Path, app_version: str) -> Dict[str, Any]:
    try:
        with open(cache_path, 'rb') as f:
            cache: dict = orjson.loads(gzip.decompress(f.read()))
    except (FileNotFoundError, orjson.JSONDecodeError, gzip.BadGzipFile):
        return {}
    if cache.get(_APP_VERSION_KEY) != app_version:
        return {}
    return cache


def _save_cache(cache_path: Path, cache: Dict[str, Any], app_version: str) -> None:
    with open(cache_path, 'wb') as f:
        f.write(gzip.compress(orjson.dumps({**cache, _APP_VERSION_KEY: app_version})))


async def _parse_one(
    file_idx: int,
    total: int,
    rel_path: Path,
    full_path: Path,
    logger: logging.Logger,
    cache: Dict[str, Any],
    sem: asyncio.Semaphore,
    config: DiscoveryConfig[T],
) -> Tuple[Path, Optional[T]]:
    """Return (rel_path, entry), using the mtime cache to skip unchanged files.
    `entry` is None if the file could not be parsed -- logged and skipped rather than
    aborting the whole scan (see module docstring for how this differs from
    session_discovery.py's placeholder-on-failure behaviour).
    """
    async with sem:
        cache_key = str(rel_path)
        try:
            mtime = full_path.stat().st_mtime
        except OSError:
            mtime = 0.0

        cached = cache.get(cache_key)
        if cached and cached.get('mtime') == mtime and 'data' in cached:
            return rel_path, config.from_cache_dict(cache_key, cached['data'])

        previous_entry: Optional[T] = None
        if cached and 'data' in cached:
            try:
                previous_entry = config.from_cache_dict(cache_key, cached['data'])
            except config.catch:
                previous_entry = None

        try:
            start = time.perf_counter()
            parsed = await asyncio.to_thread(config.parse, full_path)
            logger.debug("[%d/%d] done in %.2fs - %s", file_idx, total, time.perf_counter() - start, rel_path)
            entry = config.make_entry(cache_key, parsed, previous_entry)
            cache[cache_key] = {'mtime': mtime, 'data': config.to_cache_dict(entry)}
            return rel_path, entry
        except config.catch as exc:
            logger.exception("[%d/%d] failed - %s: %s", file_idx, total, rel_path, exc)
            return rel_path, None


@dataclass
class _HandlerState(Generic[T]):
    """Mutable per-handler bookkeeping for one discover_all() run."""
    config: DiscoveryConfig[T]
    files: List[Path]
    cache: Dict[str, Any]
    cache_path: Path
    all_entries: List[T]
    sem: asyncio.Semaphore


def _match_handler(name: str, handlers: List[DiscoveryConfig], logger: logging.Logger, rel_path: Path) -> Optional[DiscoveryConfig]:
    matches = [h for h in handlers if fnmatch.fnmatch(name, h.glob)]
    if not matches:
        return None
    if len(matches) > 1:
        logger.warning(
            "discover_all: %s matches multiple registered globs (%s) -- using the first",
            rel_path, [h.glob for h in matches])
    return matches[0]


async def _load_handler_state(
    session_dir: Path,
    logger: logging.Logger,
    app_version: str,
    config: DiscoveryConfig[T],
    files: List[Path],
) -> _HandlerState[T]:
    total = len(files)
    cache_path = session_dir / config.cache_filename
    cache_file_existed = cache_path.exists()
    cache: Dict[str, Any] = await asyncio.to_thread(_load_cache, cache_path, app_version)
    cache_hits = sum(1 for r in files if str(r) in cache)

    if not cache_file_existed:
        logger.info("Discovery cache (%s): no cache file found, parsing all %d files from scratch",
                    config.cache_filename, total)
    elif not cache:
        logger.warning("Discovery cache (%s): cache file invalid or empty, parsing all %d files from scratch",
                       config.cache_filename, total)
    elif cache_hits < total:
        logger.info("Discovery cache (%s): %d new/modified files to parse (%d/%d already cached)",
                    config.cache_filename, total - cache_hits, cache_hits, total)
    else:
        logger.debug("Discovery cache (%s): all %d files already cached", config.cache_filename, total)

    if config.on_cache_loaded is not None:
        known: Dict[str, T] = {}
        for rel_path_str, blob in cache.items():
            if rel_path_str == _APP_VERSION_KEY or 'data' not in blob:
                continue
            try:
                known[rel_path_str] = config.from_cache_dict(rel_path_str, blob['data'])
            except config.catch:
                continue  # stale/incompatible entry -- it'll simply be reparsed below
        config.on_cache_loaded(known)

    return _HandlerState(
        config=config, files=files, cache=cache, cache_path=cache_path,
        all_entries=[], sem=asyncio.Semaphore(config.concurrency),
    )


def _scan_and_group_files(
    session_dir: Path,
    logger: logging.Logger,
    handlers: List[DiscoveryConfig],
) -> Dict[int, List[Path]]:
    """The walk (`rglob`) plus every file's `stat()` for mtime-sorting -- run inside
    `asyncio.to_thread` by `discover_all()` below, same reasoning as that function's
    own cache load/save: a session directory with thousands of files would otherwise
    stall the event loop on every startup scan and every watchfiles-triggered
    rebuild, for the walk and every stat() call, not just the cache I/O.
    """
    all_files = [
        p.relative_to(session_dir) for p in session_dir.rglob('*')
        if p.is_file() and not p.name.startswith('.')
    ]
    logger.debug("discover_all: found %d files in %s across %d handler(s)",
                len(all_files), session_dir, len(handlers))

    files_by_handler: Dict[int, List[Path]] = {id(h): [] for h in handlers}
    for rel_path in all_files:
        handler = _match_handler(rel_path.name, handlers, logger, rel_path)
        if handler is not None:
            files_by_handler[id(handler)].append(rel_path)

    for handler_id, files in files_by_handler.items():
        files.sort(key=lambda p: (session_dir / p).stat().st_mtime, reverse=True)
        files_by_handler[handler_id] = files
    return files_by_handler


async def discover_all(
    session_dir: Path,
    logger: logging.Logger,
    app_version: str,
    handlers: List[DiscoveryConfig],
) -> AsyncIterator[Tuple[DiscoveryConfig, List[Any]]]:
    """Async generator: walks `session_dir` once, dispatches each file to whichever
    registered handler's glob matches it, and yields (handler, entries) every time
    any handler's entry list changes -- entries sorted by that handler's own
    `sort_key` (descending). Compare by identity (`is`) against your own handler
    instance to tell which stream a yield belongs to.

    Each handler keeps its own on-disk cache file (their cached data shapes are
    unrelated) and is invalidated independently on an app-version mismatch. A file
    matching no registered glob is ignored; a file matching more than one is a
    misconfiguration, logged and resolved to the first match.
    """
    if not session_dir.exists():
        return

    files_by_handler = await asyncio.to_thread(_scan_and_group_files, session_dir, logger, handlers)

    states: Dict[int, _HandlerState] = {}
    for config in handlers:
        states[id(config)] = await _load_handler_state(
            session_dir, logger, app_version, config, files_by_handler[id(config)])

    async def _tagged(config: DiscoveryConfig, file_idx: int, total: int, rel: Path, state: _HandlerState):
        rel_path, entry = await _parse_one(
            file_idx, total, rel, session_dir / rel, logger, state.cache, state.sem, config)
        return config, rel_path, entry

    tasks = []
    for config in handlers:
        state = states[id(config)]
        total = len(state.files)
        for i, rel in enumerate(state.files):
            tasks.append(asyncio.create_task(_tagged(config, i + 1, total, rel, state)))

    completed_by_handler: Dict[int, int] = {id(h): 0 for h in handlers}
    for coro in asyncio.as_completed(tasks):
        config, _rel_path, entry = await coro
        state = states[id(config)]
        completed_by_handler[id(config)] += 1
        if entry is None:
            continue
        state.all_entries.append(entry)

        entries = sorted(state.all_entries, key=config.sort_key, reverse=True)
        yield config, entries

    for config in handlers:
        state = states[id(config)]
        live_keys = {str(r) for r in state.files}
        pruned_cache = {k: v for k, v in state.cache.items() if k in live_keys}
        await asyncio.to_thread(_save_cache, state.cache_path, pruned_cache, app_version)
