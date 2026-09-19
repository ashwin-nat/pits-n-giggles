"""Manual smoke-test script for the save-viewer and lap-analyzer API endpoints.

Usage:
    poetry run python apps/web/test_viewer_api.py --base-url http://localhost:<port>

Requires the web server to be running, with at least one .pngt recording in its
session directory for the lap-analyzer checks to find anything. Exits 0 on
all-pass, non-zero otherwise.
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
    base_url = base_url.rstrip("/") + "/save-viewer"
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

    # 5. Path traversal must never leak filesystem content. A %2F-encoded ".." segment
    #    routes past the /api/sessions/<slug> handler entirely (ASGI decodes %2F before
    #    matching, so it lands on the SPA catch-all instead) — that's expected and safe as
    #    long as the response is the app shell, not real file content. Any status code is
    #    fine here; only the body content matters.
    TRAVERSAL_PATH = "/%2F..%2F..%2Fetc%2Fpasswd"
    print(f"\n[5] GET /api/sessions{TRAVERSAL_PATH} — expect no filesystem content in the body")
    try:
        r = _get(session, f"{base_url}/api/sessions{TRAVERSAL_PATH}")
        body_safe = "root:" not in r.text and "/bin/" not in r.text
        _check(
            "Path traversal response body contains no filesystem content",
            body_safe,
            "response body contains filesystem content" if not body_safe else "",
        )
    except Exception as exc: # pylint: disable=broad-exception-caught
        _check(
            "Path traversal returns 403/404 and body contains no filesystem content",
            False,
            str(exc),
        )


_REQUIRED_SESSION_KEYS = {
    "id", "name", "trackId", "trackName", "date", "type",
    "appVersion", "gameYear", "formula", "gameVersion", "sessionBest", "sensorManifest",
}
_REQUIRED_DRIVER_KEYS = {"index", "name", "team", "carNumber", "nationality", "platform", "telemetrySettings"}
_REQUIRED_LAP_KEYS = {
    "lapNumber", "lapTime", "valid", "tyreCompound", "tyreLaps", "pitInLap", "pitOutLap", "isGood",
}


def run_lap_analyzer(base_url: str) -> None:
    base_url = base_url.rstrip("/") + "/lap-analyzer/api/v1"
    session = requests.Session()

    print("\n[LA-1] GET /sessions — expect 200 + non-empty array with required keys")
    try:
        r = _get(session, f"{base_url}/sessions")
        if r.status_code != 200:
            _check("GET /sessions returns 200", False, f"got {r.status_code}")
            sessions = []
        else:
            sessions = r.json()
            is_non_empty = isinstance(sessions, list) and len(sessions) > 0
            _check("GET /sessions returns 200 with non-empty array", is_non_empty,
                  "expected at least one .pngt recording in the session directory" if not is_non_empty else "")
            if sessions:
                missing = [s.get("id", "<no-id>") for s in sessions if not _REQUIRED_SESSION_KEYS.issubset(s.keys())]
                _check(f"All session objects have required keys {sorted(_REQUIRED_SESSION_KEYS)}",
                      len(missing) == 0, f"missing keys in ids: {missing}" if missing else "")
                # isAi is a deliberate omission (see lap_analyzer_api.py) -- assert it's
                # gone from *drivers*, not sessions; nothing to check here directly.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _check("GET /sessions returns 200 with non-empty array", False, str(exc))
        sessions = []

    first_id = sessions[0].get("id") if sessions else None
    print(f"\n[LA-2] GET /sessions/<id>/drivers — expect 200 + non-empty array (id={first_id!r})")
    drivers = []
    if first_id:
        try:
            r = _get(session, f"{base_url}/sessions/{first_id}/drivers")
            ok = r.status_code == 200
            drivers = r.json() if ok else []
            _check("GET /sessions/<id>/drivers returns 200 with non-empty array",
                  ok and isinstance(drivers, list) and len(drivers) > 0,
                  f"got {r.status_code}" if not ok else "expected non-empty array")
            if drivers:
                missing = [d.get("index") for d in drivers if not _REQUIRED_DRIVER_KEYS.issubset(d.keys())]
                _check(f"All driver objects have required keys {sorted(_REQUIRED_DRIVER_KEYS)}",
                      len(missing) == 0, f"missing keys for indices: {missing}" if missing else "")
                has_is_ai = any("isAi" in d for d in drivers)
                _check("Driver objects do not include isAi (deliberately dropped, see spec deviation)",
                      not has_is_ai, "found isAi on a driver object" if has_is_ai else "")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _check("GET /sessions/<id>/drivers returns 200 with non-empty array", False, str(exc))
    else:
        _check("GET /sessions/<id>/drivers returns 200 with non-empty array", False, "no session id available")

    print("\n[LA-3] GET /sessions/does-not-exist/drivers — expect 404")
    try:
        r = _get(session, f"{base_url}/sessions/does-not-exist/drivers")
        _check("GET /sessions/does-not-exist/drivers returns 404", r.status_code == 404, f"got {r.status_code}")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _check("GET /sessions/does-not-exist/drivers returns 404", False, str(exc))

    first_driver_index = drivers[0].get("index") if drivers else None
    print(f"\n[LA-4] GET /sessions/<id>/drivers/<index>/laps — expect 200 + array (index={first_driver_index!r})")
    if first_id and first_driver_index is not None:
        try:
            r = _get(session, f"{base_url}/sessions/{first_id}/drivers/{first_driver_index}/laps")
            ok = r.status_code == 200
            laps = r.json() if ok else []
            _check("GET /sessions/<id>/drivers/<index>/laps returns 200 with an array",
                  ok and isinstance(laps, list), f"got {r.status_code}" if not ok else "")
            if laps:
                missing = [l.get("lapNumber") for l in laps if not _REQUIRED_LAP_KEYS.issubset(l.keys())]
                _check(f"All lap objects have required keys {sorted(_REQUIRED_LAP_KEYS)}",
                      len(missing) == 0, f"missing keys for lap numbers: {missing}" if missing else "")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _check("GET /sessions/<id>/drivers/<index>/laps returns 200 with an array", False, str(exc))
    else:
        _check("GET /sessions/<id>/drivers/<index>/laps returns 200 with an array",
              False, "no session id / driver index available")

    print(f"\n[LA-5] GET /sessions/{first_id}/drivers/999999/laps — expect 404 DRIVER_NOT_FOUND")
    if first_id:
        try:
            r = _get(session, f"{base_url}/sessions/{first_id}/drivers/999999/laps")
            ok = r.status_code == 404
            code = r.json().get("error", {}).get("code") if ok else None
            _check("Unknown driver index returns 404 with DRIVER_NOT_FOUND",
                  ok and code == "DRIVER_NOT_FOUND", f"got {r.status_code}, code={code!r}")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _check("Unknown driver index returns 404 with DRIVER_NOT_FOUND", False, str(exc))
    else:
        _check("Unknown driver index returns 404 with DRIVER_NOT_FOUND", False, "no session id available")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the save-viewer and lap-analyzer API endpoints.")
    parser.add_argument("--base-url", required=True, help="Base URL of the running server, e.g. http://localhost:4768")
    args = parser.parse_args()

    run(args.base_url)
    run_lap_analyzer(args.base_url)

    print(f"\nResults: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()
