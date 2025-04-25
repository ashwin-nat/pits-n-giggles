import requests

def test_endpoints_with_session(hostname, port, endpoints):
    base_url = f'http://{hostname}:{port}'
    session = requests.Session()
    passed = 0
    failed = 0

# sourcery skip: no-loop-in-tests
    for endpoint in endpoints:
        url = f'{base_url}/{endpoint}'
        response = session.get(url)
        # sourcery skip: no-conditionals-in-tests
        if response.status_code in {200, 400}:
            print(f"Success: {url} returned {response.status_code}")
            passed += 1
        else:
            print(f"Failed: {url} returned {response.status_code}")
            failed += 1

    print(f"Tested {len(endpoints)} endpoints. {passed} passed, {failed} failed.")

endpoints = [
    "/favicon.ico",
    "/tyre-icons/soft.svg",
    "/tyre-icons/super-soft.svg",
    "/tyre-icons/medium.svg",
    "/tyre-icons/hard.svg",
    "/tyre-icons/intermediate.svg",
    "/tyre-icons/wet.svg",
    "/",
    "/eng-view",
    "/player-stream-overlay",
    "/telemetry-info",
    "/race-info",
    "/driver-info?index=0",
    "/stream-overlay-info",
    "/static/css/style.css",
    "/static/css/modals.css",
    "/static/css/weather.css",
    "/static/css/conditions.css",
    "/static/css/speedLimit.css",
    "/static/css/tyreStintHistoryModal.css",
    "/static/js/preferences.js",
    "/static/js/utils.js",
    "/static/js/iconCache.js",
    "/static/js/weatherUI.js",
    "/static/js/graph.js",
    "/static/js/driverDataModalPopulator.js",
    "/static/js/raceStatsModalPopulator.js",
    "/static/js/tyreStintHistoryModal.js",
    "/static/js/modals.js",
    "/static/js/raceTableRowPopulator.js",
    "/static/js/timeTrialDataPopulator.js",
    "/static/js/telemetryRenderer.js",
    "/static/js/frontendUpdate.js",
    "/static/js/app.js",
    "/static/js/updater.js",
]

# Example hostname and port
hostname = "localhost"
port = 62943

test_endpoints_with_session(hostname, port, endpoints)
