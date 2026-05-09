"""Manual smoke-test script for the save-viewer API endpoints.

Usage:
    poetry run python apps/save_viewer/test_viewer_api.py --base-url http://localhost:<port>

Requires the save-viewer server to be running. Exits 0 on all-pass, non-zero otherwise.
"""

import argparse
import sys

import requests


REQUIRED_SESSION_KEYS = {"slug", "sessionType", "track", "date", "validLapCount"}
TIMEOUT = 10  # seconds per request

_passed = 0
_failed = 0


def _check(name: str, ok: bool, reason: str = "") -> None:
    global _passed, _failed
    if ok:
        print(f"PASS: {name}")
        _passed += 1
    else:
        msg = f"FAIL: {name}"
        if reason:
            msg += f" — {reason}"
        print(msg)
        _failed += 1


def _get(session: requests.Session, url: str) -> requests.Response:
    print(f"  --> GET {url}", flush=True)
    r = session.get(url, timeout=TIMEOUT)
    print(f"  <-- {r.status_code}", flush=True)
    return r


def run(base_url: str) -> None:
    base_url = base_url.rstrip("/")
    session = requests.Session()

    # 1. GET /api/sessions → 200 with non-empty array
    print("\n[1] GET /api/sessions — expect 200 + non-empty array")
    try:
        r = _get(session, f"{base_url}/api/sessions")
        if r.status_code != 200:
            _check("GET /api/sessions returns 200", False, f"got {r.status_code}")
            sessions = []
        else:
            sessions = r.json()
            is_non_empty = isinstance(sessions, list) and len(sessions) > 0
            if not is_non_empty:
                print(f"  raw response: {r.text[:500]!r}", flush=True)
            _check(
                "GET /api/sessions returns 200 with non-empty array",
                is_non_empty,
                "expected non-empty array" if not is_non_empty else "",
            )
    except Exception as exc: # pylint: disable=broad-exception-caught
        _check("GET /api/sessions returns 200 with non-empty array", False, str(exc))
        sessions = []

    # 2. Every session object has required keys
    print("\n[2] Check required keys on every session object")
    if sessions:
        missing = [
            s.get("slug", "<no-slug>")
            for s in sessions
            if not REQUIRED_SESSION_KEYS.issubset(s.keys())
        ]
        _check(
            f"All session objects have required keys {sorted(REQUIRED_SESSION_KEYS)}",
            len(missing) == 0,
            f"missing keys in slugs: {missing}" if missing else "",
        )
    else:
        _check(
            f"All session objects have required keys {sorted(REQUIRED_SESSION_KEYS)}",
            False,
            "no sessions returned — cannot verify keys",
        )

    # 3. GET /api/sessions/<first_slug> → 200 with valid JSON
    first_slug = sessions[0].get("slug") if sessions else None
    print(f"\n[3] GET /api/sessions/<first_slug> — expect 200 + valid JSON (slug={first_slug!r})")
    if first_slug:
        try:
            r = _get(session, f"{base_url}/api/sessions/{first_slug}")
            ok = r.status_code == 200
            if ok:
                try:
                    r.json()
                except ValueError:
                    ok = False
            _check(
                f"GET /api/sessions/{first_slug} returns 200 with valid JSON",
                ok,
                f"got {r.status_code}" if r.status_code != 200 else "response is not valid JSON",
            )
        except Exception as exc: # pylint: disable=broad-exception-caught
            _check(f"GET /api/sessions/{first_slug} returns 200 with valid JSON", False, str(exc))
    else:
        _check("GET /api/sessions/<first_slug> returns 200 with valid JSON", False, "no slug available")

    # 4. GET /api/sessions/does-not-exist → 404
    print("\n[4] GET /api/sessions/does-not-exist — expect 404")
    try:
        r = _get(session, f"{base_url}/api/sessions/does-not-exist")
        _check(
            "GET /api/sessions/does-not-exist returns 404",
            r.status_code == 404,
            f"got {r.status_code}",
        )
    except Exception as exc: # pylint: disable=broad-exception-caught
        _check("GET /api/sessions/does-not-exist returns 404", False, str(exc))

    # 5. Path traversal → 403 or 404; body must not contain filesystem content
    TRAVERSAL_PATH = "/%2F..%2F..%2Fetc%2Fpasswd"
    print(f"\n[5] GET /api/sessions{TRAVERSAL_PATH} — expect 403/404 + safe body")
    try:
        r = _get(session, f"{base_url}/api/sessions{TRAVERSAL_PATH}")
        status_ok = r.status_code in {403, 404}
        body_safe = "root:" not in r.text and "/bin/" not in r.text
        _check(
            "Path traversal returns 403/404 and body contains no filesystem content",
            status_ok and body_safe,
            (
                f"got {r.status_code}"
                if not status_ok
                else "response body contains filesystem content"
            ),
        )
    except Exception as exc: # pylint: disable=broad-exception-caught
        _check(
            "Path traversal returns 403/404 and body contains no filesystem content",
            False,
            str(exc),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the save-viewer API endpoints.")
    parser.add_argument("--base-url", required=True, help="Base URL of the running server, e.g. http://localhost:4768")
    args = parser.parse_args()

    run(args.base_url)

    print(f"\nResults: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()
